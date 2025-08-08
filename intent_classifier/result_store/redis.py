import json
import uuid
from typing import Any, Optional

from redis.asyncio import Redis
from .base import ResultBackend

class RedisResultStore(ResultBackend):
    def __init__(self, url: str | None = None, default_ttl: int = 3600) -> None:
        """
        Initialize Redis result store.
        
        Args:
            url: Redis connection URL
            default_ttl: Default time-to-live in seconds (1 hour by default)
        """
        self._r = Redis.from_url(url or "redis://localhost:6379/0")
        self._default_ttl = default_ttl
        self._key_prefix = "intent-result:"
    
    def _get_key(self, task_id: uuid.UUID) -> str:
        """Generate Redis key for a task ID."""
        return f"{self._key_prefix}{task_id}"
    
    async def store_result(self, task_id: uuid.UUID, result: Any, ttl: Optional[int] = None) -> None:
        """Store a result with optional TTL. Redis handles expiration automatically."""
        key = self._get_key(task_id)
        ttl = ttl or self._default_ttl
        
        # Serialize the result to JSON
        serialized_result = json.dumps(result, default=str)
        
        # Store with TTL (Redis handles expiration)
        await self._r.setex(key, ttl, serialized_result)
    
    async def get_result(self, task_id: uuid.UUID) -> Any:
        """Get a result by task ID, returns None if not found or expired."""
        key = self._get_key(task_id)
        data = await self._r.get(key)
        
        if data is None:
            return None
        
        # Deserialize the result from JSON
        return json.loads(data)
    
    async def delete_result(self, task_id: uuid.UUID) -> bool:
        """Delete a result by task ID. Returns True if deleted, False if not found."""
        key = self._get_key(task_id)
        deleted_count = await self._r.delete(key)
        return deleted_count > 0
    
    async def result_exists(self, task_id: uuid.UUID) -> bool:
        """Check if a result exists and is not expired."""
        key = self._get_key(task_id)
        exists = await self._r.exists(key)
        return exists > 0
