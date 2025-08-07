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

from .conf import conf, processors


# --------------------------------------------------------------------------- #
logger = logging.getLogger(conf.APP_NAME)
logging.basicConfig(level=conf.LOG_LEVEL,
                    format=conf.LOG_FORMAT)

api_key_header = APIKeyHeader(name=conf.API_KEY, auto_error=False)


def validate_api_key(key: str | None = Depends(api_key_header)) -> None:
    """FastAPI dependency that aborts if the key is bad/missing."""
    if key is None or key != conf.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or missing API key")
        
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
    task_queue = get_queue()
    
    # Initialize result store based on settings
    if conf.RESULT_STORE_TYPE == "redis":
        result_store = get_result_store(
            conf.RESULT_STORE_TYPE,
            url=conf.RESULT_STORE_REDIS_URL,
            default_ttl=conf.RESULT_STORE_TTL
        )
    else:
        result_store = get_result_store(
            conf.RESULT_STORE_TYPE,
            default_ttl=conf.RESULT_STORE_TTL
        )
    
    asyncio.create_task(task_queue.worker(process_task))
    
    logger.info("Started queue worker and result store.")
    
    
    for layer in conf.CLASSIFICATION_LAYERS:
        await layer["instance"].setup()
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
            detail=f"Result for task {task_id} not found or expired"
        )
    
    return result


# --------------------------------------------------------------------------- #
# Layer logic
# --------------------------------------------------------------------------- #
async def classify_segment(
    task: TaskIn, last_segment: str, segment: str, layers: list[dict],
    running_cost: int = 0, is_partial: bool = False
) -> tuple[int, dict] | None:
    
    for layer in layers:
        if layer["cost"] + running_cost > task.job_budget:
            continue
        if not await layer["instance"].matches_content(last_segment, segment):
            continue

        result = await layer["instance"].classify(last_segment, segment, is_partial=is_partial)
        running_cost += layer["cost"]
        await layer.on_complete(result)

        threshold = float(layer.get("confidence_threshold", conf.DEFAULT_INTENT_CONFIDENCE_THRESHOLD))
        if result > threshold:
            await layer.on_success(result)
            return running_cost, result
        else:
            await layer.on_failure(result, "Result below confidence threshold")
    return running_cost, None


async def _post_callback(url: str, payload: dict) -> None:
    """Send a POST request to the caller's callback URL."""
    headers = {
        "Content-Type": "application/json",
        
    }
    if conf.CALLBACK_API_KEY:
        headers["X-Api-Key"] = conf.CALLBACK_API_KEY

    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        
        

async def process_task(task: TaskIn) -> None:
    logger.info("Processing task %s | budget=%s | content=%r",
                task.task_id, task.job_budget, task.content)
    
    task_result = {
        "task_id": str(task.task_id),
        "status": "processing",
        "timestamp": asyncio.get_event_loop().time(),
        "is_partial": task.is_partial,
    }

    try:    
        # Find out how many intents to classify and their borders
        intent_separators = processors.INTENT_SEPARATORS

        # Assume with full confidence that each segment is independent from each other
        # This is a simplification, but it makes handling large texts much easier.
        logger.info("Segmenting content for classification.")
        
        segments = [task.content]  # Default to single segment if no separators work
        
        for intent_separator in intent_separators:
            if await intent_separator.check_condition(task.content):
                new_segments = await intent_separator.get_segments(task.content)

                if new_segments is not None and new_segments:
                    segments = new_segments
                    break


        # Run segments through classification layers
        layers = processors.CLASSIFICATION_LAYERS if task.priority_order == "ascending" else reversed(processors.CLASSIFICATION_LAYERS)
        running_cost = 0
        classification_results = []
        
        for i in range(len(segments)):
            last_segment = segments[i - 1] if i > 0 else None
            segment = segments[i]
            logger.info("Processing segment %d/%d: %r", i + 1, len(segments), segment)
            
            running_cost, result = await classify_segment(task, last_segment, segment, layers, running_cost=running_cost, is_partial=task.is_partial)

            if result is None:
                logger.info("No classification result for segment %d", i + 1)
                continue
            
            classification_results.append({
                "segment": segment,
                "eval": result,
            })
        
        task_result["status"] = "completed"
        task_result["results"] = classification_results
        
    # Incase of any error, store the error result
    except Exception as e:
        logger.exception("Error processing task %s", task.task_id)
        task_result["status"] = "failed"
        task_result["error"] = str(e)
        
    finally:
        # Store the result in the result store
        await result_store.store_result(task.task_id, task_result)
        logger.info("Finished task %s and stored result", task.task_id)
            
        # Let callback url know that its done if provided (failed or succeeded both)
        if task.callback_url:
            logger.info("Sending result to callback URL: %s", task.callback_url)
            try:
                await _post_callback(task.callback_url, task_result)
            except httpx.RequestError as e:
                logger.exception("An error occurred while requesting: %s", e)
            except httpx.HTTPStatusError as e:
                logger.exception("Callback URL returned status %s", e.response.status_code)
            except Exception as e:
                logger.exception("Callback POST failed: %s", e)
