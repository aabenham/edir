from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import ANNOTATION_STORED, EMBEDDING_CREATED, SYSTEM_ERROR
from app.services.embedding_service import EmbeddingService
from app.storage.document_store import DocumentStore
from app.storage.processed_event_store import ProcessedEventStore
from app.storage.vector_store import VectorStore


def test_embedding_service_creates_vector_and_publishes_embedding_created():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    document_store.save(
        "img_6001",
        {
            "image_id": "img_6001",
            "objects": [
                {"label": "car", "confidence": 0.9},
                {"label": "person", "confidence": 0.8},
            ],
            "status": "stored",
            "history": ["inference.completed", "annotation.stored"],
        },
    )

    service = EmbeddingService(
        broker,
        document_store,
        vector_store,
        processed_store,
    )

    published_embeddings = []

    def embedding_handler(event: dict) -> None:
        published_embeddings.append(event)

    broker.subscribe(EMBEDDING_CREATED, embedding_handler)
    service.start()

    annotation_event = create_event(
        ANNOTATION_STORED,
        {
            "image_id": "img_6001",
            "document_id": "img_6001",
            "status": "stored",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(ANNOTATION_STORED, annotation_event)

    stored_vector = vector_store.get("img_6001")

    assert stored_vector is not None
    assert len(stored_vector) == 4
    assert stored_vector[0] == 2.0

    assert len(published_embeddings) == 1
    assert published_embeddings[0]["metadata"]["event_type"] == EMBEDDING_CREATED
    assert published_embeddings[0]["payload"]["image_id"] == "img_6001"


def test_embedding_service_ignores_duplicate_events():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    document_store.save(
        "img_6002",
        {
            "image_id": "img_6002",
            "objects": [{"label": "truck", "confidence": 0.95}],
            "status": "stored",
            "history": ["inference.completed", "annotation.stored"],
        },
    )

    service = EmbeddingService(
        broker,
        document_store,
        vector_store,
        processed_store,
    )

    published_embeddings = []

    def embedding_handler(event: dict) -> None:
        published_embeddings.append(event)

    broker.subscribe(EMBEDDING_CREATED, embedding_handler)
    service.start()

    annotation_event = create_event(
        ANNOTATION_STORED,
        {
            "image_id": "img_6002",
            "document_id": "img_6002",
            "status": "stored",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(ANNOTATION_STORED, annotation_event)
    broker.publish(ANNOTATION_STORED, annotation_event)

    assert vector_store.count() == 1
    assert processed_store.count() == 1
    assert len(published_embeddings) == 1


def test_embedding_service_publishes_error_when_document_missing():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    service = EmbeddingService(
        broker,
        document_store,
        vector_store,
        processed_store,
    )

    system_errors = []

    def error_handler(event: dict) -> None:
        system_errors.append(event)

    broker.subscribe(SYSTEM_ERROR, error_handler)
    service.start()

    annotation_event = create_event(
        ANNOTATION_STORED,
        {
            "image_id": "img_missing",
            "document_id": "img_missing",
            "status": "stored",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(ANNOTATION_STORED, annotation_event)

    assert vector_store.count() == 0
    assert processed_store.count() == 0
    assert len(system_errors) == 1
    assert system_errors[0]["metadata"]["event_type"] == SYSTEM_ERROR


def test_embedding_service_publishes_system_error_for_invalid_event():
    broker = InMemoryBroker()
    document_store = DocumentStore()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    service = EmbeddingService(
        broker,
        document_store,
        vector_store,
        processed_store,
    )

    system_errors = []

    def error_handler(event: dict) -> None:
        system_errors.append(event)

    broker.subscribe(SYSTEM_ERROR, error_handler)
    service.start()

    invalid_event = {
        "payload": {
            "image_id": "img_bad",
        }
    }

    broker.publish(ANNOTATION_STORED, invalid_event)

    assert vector_store.count() == 0
    assert processed_store.count() == 0
    assert len(system_errors) == 1