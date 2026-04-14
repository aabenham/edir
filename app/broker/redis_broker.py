import json
from typing import Callable

import redis

from app.broker.base import BaseBroker


class RedisBroker(BaseBroker):
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self._pubsub = self._client.pubsub()

    def publish(self, topic: str, event: dict) -> None:
        message = json.dumps(event)
        self._client.publish(topic, message)

    def subscribe(self, topic: str, handler: Callable[[dict], None]) -> None:
        self._pubsub.subscribe(topic)

        for message in self._pubsub.listen():
            if message["type"] != "message":
                continue

            if message["channel"] != topic:
                continue

            payload = json.loads(message["data"])
            handler(payload)

    def close(self) -> None:
        self._pubsub.close()
        self._client.close()