from app.events.schemas import (
    BaseEvent,
    EventMetadata,
)
from datetime import datetime, timezone
from uuid import uuid4


def create_event(event_type: str, payload: dict, source: str = "app") -> BaseEvent:
    metadata = EventMetadata(
        event_id=str(uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        source=source,
    )
    return BaseEvent(metadata=metadata, payload=payload)