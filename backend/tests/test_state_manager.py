from datetime import datetime

import pytest

from app.models.message import NormalizedMessage
from app.services.state_manager import RedisStateManager


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.lists = {}

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def lpush(self, key, value):
        self.lists.setdefault(key, [])
        self.lists[key].insert(0, value)

    async def get(self, key):
        return self.values.get(key)

    async def lrange(self, key, start, end):
        data = self.lists.get(key, [])
        if end == -1:
            return data[start:]
        return data[start:end + 1]

    async def scan_iter(self, match=None):
        for key in self.values.keys():
            if not match:
                yield key
                continue
            if match.endswith("*"):
                prefix = match[:-1]
                if key.startswith(prefix):
                    yield key
            elif key == match:
                yield key


@pytest.mark.asyncio
async def test_save_message_is_idempotent():
    manager = RedisStateManager()
    manager.redis = FakeRedis()

    message = NormalizedMessage(
        channel="mock",
        user_id="u1",
        user_name="User 1",
        message_id="m1",
        text="hello",
        timestamp=datetime.utcnow()
    )

    first = await manager.save_message("mock", "u1", message)
    second = await manager.save_message("mock", "u1", message)

    assert first is True
    assert second is True
    assert manager.redis.lists["messages:mock:u1"] == ["m1"]
