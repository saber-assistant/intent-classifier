from .memory import MemoryResultStore
from .redis import RedisResultStore
from .base import ResultBackend

RESULT_STORE_MAPPING = {
    "memory": MemoryResultStore,
    "redis": RedisResultStore,
}

def get_result_store(store_type: str, **kwargs) -> ResultBackend:
    store_class = RESULT_STORE_MAPPING.get(store_type)
    if not store_class:
        raise ValueError(f"Unknown result store type: {store_type}")
    
    return store_class(**kwargs)

__all__ = ["ResultBackend", "MemoryResultStore", "RedisResultStore", "get_result_store"]
