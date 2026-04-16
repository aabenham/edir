from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import ANNOTATION_STORED


def test_subscriber_downtime_allows_recovery_after_replay():
    broker = InMemoryBroker()
    stored_documents = {}

    event = create_event(
        ANNOTATION_STORED,
        {
            "image_id": "img_3001",
            "document_id": "doc_3001",
            "status": "stored",
        },
        source="integration-test",
    ).model_dump(mode="json")

    # subscriber is "down" here, so event is published before subscription
    broker.publish(ANNOTATION_STORED, event)

    assert stored_documents == {}

    def document_consumer(event: dict) -> None:
        image_id = event["payload"]["image_id"]
        stored_documents[image_id] = {
            "document_id": event["payload"]["document_id"],
            "status": event["payload"]["status"],
        }

    # subscriber comes back online
    broker.subscribe(ANNOTATION_STORED, document_consumer)

    # replay the event after recovery
    broker.publish(ANNOTATION_STORED, event)

    assert "img_3001" in stored_documents
    assert stored_documents["img_3001"]["document_id"] == "doc_3001"
    assert stored_documents["img_3001"]["status"] == "stored"