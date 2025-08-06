from .memory import MemoryQueue
from .redis import RedisQueue
from .base import QueueBackend

QUEUE_MAPPING = {
    "memory": MemoryQueue,
    "redis": RedisQueue,
}

def get_queue(queue_type: str) -> QueueBackend:
    queue_class = QUEUE_MAPPING.get(queue_type)
    if not queue_class:
        raise ValueError(f"Unknown queue type: {queue_type}")
    return queue_class()
