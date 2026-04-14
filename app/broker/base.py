from abc import ABC, abstractmethod
from typing import Callable, Protocol


class EventHandler(Protocol):
    def __call__(self, event: dict) -> None:
        ...


class BaseBroker(ABC):
    @abstractmethod
    def publish(self, topic: str, event: dict) -> None:
        """Publish an event to a topic."""
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[dict], None]) -> None:
        """Subscribe a handler to a topic."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Clean up broker resources."""
        raise NotImplementedError