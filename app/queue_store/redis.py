import os
import json

from redis.asyncio import Redis
from .base import QueueBackend

REDIS_LIST_NAME = "intent-tasks"

class RedisQueue(QueueBackend):
    def __init__(self, url: str | None = None) -> None:
        self._r = Redis.from_url(url or os.getenv("REDIS_URL"))

    async def enqueue(self, item):
        await self._r.lpush(REDIS_LIST_NAME, json.dumps(item, default=str))

    async def dequeue(self):
        _, data = await self._r.brpop(REDIS_LIST_NAME)
        return json.loads(data)

    def task_done(self):
        # Redis doesn't need a task_done since it doesn't track in-flight tasks
        pass