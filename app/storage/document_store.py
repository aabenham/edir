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