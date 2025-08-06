import asyncio
from typing import Any

from .base import QueueBackend

class MemoryQueue(QueueBackend):
    def __init__(self) -> None:
        self._q: asyncio.Queue[Any] = asyncio.Queue()

    async def enqueue(self, item): await self._q.put(item)
    async def dequeue(self): return await self._q.get()
    def task_done(self): self._q.task_done()