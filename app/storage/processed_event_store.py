class ProcessedEventStore:
    def __init__(self) -> None:
        self._processed_event_ids: set[str] = set()

    def has_processed(self, event_id: str) -> bool:
        return event_id in self._processed_event_ids

    def mark_processed(self, event_id: str) -> None:
        self._processed_event_ids.add(event_id)

    def count(self) -> int:
        return len(self._processed_event_ids)

    def clear(self) -> None:
        self._processed_event_ids.clear()