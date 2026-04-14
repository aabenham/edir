from app.events.topics import ALL_TOPICS


def validate_topic(topic: str) -> bool:
    return topic in ALL_TOPICS


def validate_event_structure(event: dict) -> bool:
    if not isinstance(event, dict):
        return False

    if "metadata" not in event or "payload" not in event:
        return False

    metadata = event["metadata"]
    if not isinstance(metadata, dict):
        return False

    required_metadata_fields = {"event_id", "event_type", "timestamp", "source"}
    if not required_metadata_fields.issubset(metadata.keys()):
        return False

    return True


def validate_event_for_topic(topic: str, event: dict) -> bool:
    if not validate_topic(topic):
        return False

    if not validate_event_structure(event):
        return False

    return event["metadata"]["event_type"] == topic