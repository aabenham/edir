from typing import Protocol


class DocumentStoreProtocol(Protocol):
    def save(self, image_id: str, document: dict) -> None:
        ...

    def get(self, image_id: str) -> dict | None:
        ...

    def all(self) -> dict[str, dict]:
        ...

    def count(self) -> int:
        ...

    def clear(self) -> None:
        ...

    def close(self) -> None:
        ...


class DocumentStore:
    def __init__(self) -> None:
        self._documents: dict[str, dict] = {}

    def save(self, image_id: str, document: dict) -> None:
        self._documents[image_id] = document

    def get(self, image_id: str) -> dict | None:
        return self._documents.get(image_id)

    def all(self) -> dict[str, dict]:
        return dict(self._documents)

    def count(self) -> int:
        return len(self._documents)

    def clear(self) -> None:
        self._documents.clear()

    def close(self) -> None:
        return None
