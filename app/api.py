import asyncio
import logging
from contextlib import asynccontextmanager
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from .queue_store import get_queue, QueueBackend

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


# --------------------------------------------------------------------------- #
# Task schema
# --------------------------------------------------------------------------- #
class TaskIn(BaseModel):
    task_id: uuid.UUID = Field()
    job: Literal["classify"]
    job_level: int = 0
    content: str


# --------------------------------------------------------------------------- #
# FastAPI
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Started lifespan context.")

    global task_queue
    task_queue = get_queue()
    
    asyncio.create_task(task_queue.worker(process_task))
    logger.info("Started queue worker.")
    try:
        yield
    finally:
        await task_queue.close()
        logger.info("Stopped queue worker.")


app = FastAPI(title=conf.APP_NAME, lifespan=lifespan)


@app.post("/queue/", dependencies=[Depends(validate_api_key)], status_code=202)
async def enqueue_task(task: TaskIn) -> dict[str, str]:
    """Accept a task JSON and push to the internal queue."""
    await task_queue.enqueue(task)
    return {"status": "queued", "task_id": str(task.task_id)}


# --------------------------------------------------------------------------- #
# Layer logic
# --------------------------------------------------------------------------- #
async def process_task(task: TaskIn) -> None:
    logger.info("Processing task %s | level=%s | content=%r",
                task.task_id, task.job_level, task.content)

    await asyncio.sleep(0.25)
    logger.info("Finished task %s", task.task_id)
