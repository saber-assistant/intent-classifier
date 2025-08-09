import asyncio
import logging
from contextlib import asynccontextmanager
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import httpx


from .queue_store import get_queue, QueueBackend
from .result_store import get_result_store, ResultBackend
from .utils import send_post_request
from .conf import conf, processors
from .logic import classify_segment, segment_text


# --------------------------------------------------------------------------- #
logger = logging.getLogger(conf.APP_NAME)
logging.basicConfig(level=conf.LOG_LEVEL, format=conf.LOG_FORMAT)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def validate_api_key(key: str | None = Depends(api_key_header)) -> None:
    """FastAPI dependency that aborts if the key is bad/missing."""
    if key is None or key != conf.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


task_queue: QueueBackend
result_store: ResultBackend


# --------------------------------------------------------------------------- #
# Task schema
# --------------------------------------------------------------------------- #
class TaskIn(BaseModel):
    task_id: uuid.UUID = Field()
    job: Literal["classify"]
    content: str
    is_partial: bool = False
    job_budget: int = 10
    callback_url: str | None = None
    priority_order: Literal["ascending", "descending"] = "ascending"


# --------------------------------------------------------------------------- #
# FastAPI
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Started lifespan context.")

    global task_queue, result_store
    
    # Initialize queue based on settings
    queue_settings = conf.QUEUE_SETTINGS.get(conf.QUEUE_TYPE, {})
    task_queue = get_queue(conf.QUEUE_TYPE, **queue_settings)

    # Initialize result store based on settings
    result_store_settings = conf.RESULT_STORE_SETTINGS.get(conf.RESULT_STORE_TYPE, {})
    result_store = get_result_store(conf.RESULT_STORE_TYPE, **result_store_settings)

    asyncio.create_task(task_queue.worker(process_task))

    logger.info("Started queue worker and result store.")

    for separator in processors.INTENT_SEPARATORS:
        await separator["instance"].on_startup()
        logger.info("Initialized intent separator: %s", separator["alias"])


    for layer in processors.CLASSIFICATION_LAYERS:
        await layer["instance"].on_startup()
        logger.info("Initialized classification layer: %s", layer["alias"])


    try:
        yield
    finally:
        await task_queue.close()
        logger.info("Stopped queue worker.")


app = FastAPI(title=conf.APP_NAME, lifespan=lifespan)


@app.post("/queue/", dependencies=[Depends(validate_api_key)], status_code=202)
async def enqueue_task(task: TaskIn) -> dict[str, str]:
    await task_queue.enqueue(task)
    return {"status": "queued", "task_id": str(task.task_id)}


@app.get("/result/{task_id}", dependencies=[Depends(validate_api_key)])
async def get_task_result(task_id: uuid.UUID) -> dict:
    """Get the result of a completed task."""
    result = await result_store.get_result(task_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result for task {task_id} not found or expired",
        )

    return result


async def process_task(task: TaskIn) -> None:
    task_result = {
        "task_id": str(task.task_id),
        "status": "processing",
        "timestamp": asyncio.get_event_loop().time(),
        "is_partial": task.is_partial,
    }
    
    logger.info(
        "Processing task %r",
        task
    )

    try:
        # Find out how many intents to classify and their borders
        segments = await segment_text(processors.INTENT_SEPARATORS, task.content)

        # Run segments through classification layers
        layers = (
            processors.CLASSIFICATION_LAYERS
            if task.priority_order == "ascending"
            else reversed(processors.CLASSIFICATION_LAYERS)
        )
        running_cost = 0
        classification_results = []

        for i in range(len(segments)):
            segment = segments[i]
            logger.info("Processing segment %d/%d: %r", i + 1, len(segments), segment)
            logger.debug("Current running cost: %d", running_cost)

            running_cost, result = await classify_segment(
                task,
                segments[:i],
                segment,
                layers,
                running_cost=running_cost,
                is_partial=task.is_partial,
            )
            logger.debug("Segment %d result: %r, updated running cost: %d", i + 1, result, running_cost)
            if result is None:
                logger.info("No classification result for segment %d", i + 1)
                continue

            classification_results.append(
                {
                    "segment": segment,
                    "eval": result,
                }
            )

        task_result["status"] = "completed"
        task_result["results"] = classification_results
        logger.debug("Task completed with results: %r", classification_results)

    # Incase of any error, store the error result
    except Exception as e:
        logger.exception("Error processing task %s", task.task_id)
        task_result["status"] = "failed"
        task_result["error"] = str(e)
        logger.debug("Task failed with error: %s", str(e))

    finally:
        # Store the result in the result store
        logger.debug("Storing result for task %s: %r", task.task_id, task_result)
        await result_store.store_result(task.task_id, task_result)
        logger.info("Finished task %s and stored result", task.task_id)

        # Let callback url know that its done if provided (failed or succeeded both)
        if task.callback_url:
            logger.info("Sending result to callback URL: %s", task.callback_url)
            try:
                await send_post_request(task.callback_url, task_result)
                logger.debug("Callback POST succeeded for URL: %s", task.callback_url)
            except httpx.RequestError as e:
                logger.exception("An error occurred while requesting: %s", e)
            except httpx.HTTPStatusError as e:
                logger.exception(
                    "Callback URL returned status %s", e.response.status_code
                )
            except Exception as e:
                logger.exception("Callback POST failed: %s", e)
