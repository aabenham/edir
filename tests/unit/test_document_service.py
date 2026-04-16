from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import ANNOTATION_STORED, INFERENCE_COMPLETED, SYSTEM_ERROR
from app.services.document_service import DocumentService
from app.storage.document_store import DocumentStore
from app.storage.processed_event_store import ProcessedEventStore


def test_document_service_stores_document_and_publishes_annotation_stored():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    processed_store = ProcessedEventStore()
    service = DocumentService(broker, document_store, processed_store)

    published_annotations = []

    def annotation_handler(event: dict) -> None:
        published_annotations.append(event)

    broker.subscribe(ANNOTATION_STORED, annotation_handler)
    service.start()

    inference_event = create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_5001",
            "objects": [
                {"label": "car", "confidence": 0.93},
                {"label": "person", "confidence": 0.88},
            ],
            "model_version": "v1",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(INFERENCE_COMPLETED, inference_event)

    stored_doc = document_store.get("img_5001")

    assert stored_doc is not None
    assert stored_doc["image_id"] == "img_5001"
    assert len(stored_doc["objects"]) == 2
    assert stored_doc["status"] == "stored"

    assert len(published_annotations) == 1
    assert published_annotations[0]["payload"]["image_id"] == "img_5001"
    assert published_annotations[0]["metadata"]["event_type"] == ANNOTATION_STORED


def test_document_service_ignores_duplicate_events():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    processed_store = ProcessedEventStore()
    service = DocumentService(broker, document_store, processed_store)

    published_annotations = []

    def annotation_handler(event: dict) -> None:
        published_annotations.append(event)

    broker.subscribe(ANNOTATION_STORED, annotation_handler)
    service.start()

    inference_event = create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_5002",
            "objects": [{"label": "truck", "confidence": 0.95}],
            "model_version": "v1",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(INFERENCE_COMPLETED, inference_event)
    broker.publish(INFERENCE_COMPLETED, inference_event)

    assert document_store.count() == 1
    assert processed_store.count() == 1
    assert len(published_annotations) == 1


def test_document_service_publishes_system_error_for_invalid_event():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    processed_store = ProcessedEventStore()
    service = DocumentService(broker, document_store, processed_store)

    system_errors = []

    def error_handler(event: dict) -> None:
        system_errors.append(event)

    broker.subscribe(SYSTEM_ERROR, error_handler)
    service.start()

    invalid_event = {
        "payload": {
            "image_id": "img_bad",
            "objects": [],
        }
    }

    broker.publish(INFERENCE_COMPLETED, invalid_event)

    assert document_store.count() == 0
    assert processed_store.count() == 0
    assert len(system_errors) == 1
    assert system_errors[0]["metadata"]["event_type"] == SYSTEM_ERROR