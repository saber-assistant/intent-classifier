import asyncio
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from .base import ResultBackend

class MemoryResultStore(ResultBackend):
    def __init__(self, default_ttl: int = 3600) -> None:
        """
        Initialize memory result store with manual expiration handling.
        
        Args:
            default_ttl: Default time-to-live in seconds (1 hour by default)
        """
        self._results: Dict[uuid.UUID, Tuple[Any, float]] = {}  # task_id -> (result, expiry_time)
        self._default_ttl = default_ttl
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def _cleanup_expired(self) -> None:
        """Background task to clean up expired results."""
        while True:
            try:
                current_time = time.time()
                expired_keys = [
                    task_id for task_id, (_, expiry_time) in self._results.items()
                    if current_time > expiry_time
                ]
                
                for task_id in expired_keys:
                    del self._results[task_id]
                
                # Run cleanup every 60 seconds
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue cleanup even if there's an error
                await asyncio.sleep(60)
    
    async def store_result(self, task_id: uuid.UUID, result: Any, ttl: Optional[int] = None) -> None:
        """Store a result with optional TTL."""
        ttl = ttl or self._default_ttl
        expiry_time = time.time() + ttl
        self._results[task_id] = (result, expiry_time)
    
    async def get_result(self, task_id: uuid.UUID) -> Any:
        """Get a result by task ID, returns None if not found or expired."""
        if task_id not in self._results:
            return None
        
        result, expiry_time = self._results[task_id]
        if time.time() > expiry_time:
            # Result has expired, remove it
            del self._results[task_id]
            return None
        
        return result
    
    async def delete_result(self, task_id: uuid.UUID) -> bool:
        """Delete a result by task ID. Returns True if deleted, False if not found."""
        if task_id in self._results:
            del self._results[task_id]
            return True
        return False
    
    async def result_exists(self, task_id: uuid.UUID) -> bool:
        """Check if a result exists and is not expired."""
        if task_id not in self._results:
            return False
        
        _, expiry_time = self._results[task_id]
        if time.time() > expiry_time:
            # Result has expired, remove it
            del self._results[task_id]
            return False
        
        return True
    
    def __del__(self):
        """Clean up the background task when the instance is destroyed."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
