from collections import defaultdict
from typing import Callable

from app.broker.base import BaseBroker


class InMemoryBroker(BaseBroker):
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[dict], None]]] = defaultdict(list)

    def publish(self, topic: str, event: dict) -> None:
        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            handler(event)

    def subscribe(self, topic: str, handler: Callable[[dict], None]) -> None:
        self._subscribers[topic].append(handler)

    def close(self) -> None:
        self._subscribers.clear()