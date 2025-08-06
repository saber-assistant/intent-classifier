import asyncio
import logging
from contextlib import asynccontextmanager
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from .queue_store import get_queue, QueueBackend
from .result_store import get_result_store, ResultBackend

from .settings import conf


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
    job_budget: int = 10
    content: str
    callback_url: str | None = None


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
async def process_task(task: TaskIn) -> None:
    logger.info("Processing task %s | level=%s | content=%r",
                task.task_id, task.job_budget, task.content)

    try:
        # Simulate processing
        await asyncio.sleep(0.25)
        

        result = {
            "task_id": str(task.task_id),
            "job": task.job,
            "job_budget": task.job_budget,
            "status": "completed",
            "result": f"Classification result for task {task.task_id}",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store the result in the result store
        await result_store.store_result(task.task_id, result)
        
        logger.info("Finished task %s and stored result", task.task_id)
        
    except Exception as e:
        # Store error result
        error_result = {
            "task_id": str(task.task_id),
            "job": task.job,
            "job_budget": task.job_budget,
            "status": "failed",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await result_store.store_result(task.task_id, error_result)
        logger.error("Task %s failed: %s", task.task_id, str(e))
