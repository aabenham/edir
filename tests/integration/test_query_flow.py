from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import (
    EMBEDDING_CREATED,
    IMAGE_QUERY_COMPLETED,
    IMAGE_QUERY_SUBMITTED,
    INFERENCE_COMPLETED,
    QUERY_COMPLETED,
    QUERY_SUBMITTED,
)
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.query_service import QueryService
from app.storage.document_store import DocumentStore
from app.storage.processed_event_store import ProcessedEventStore
from app.storage.vector_store import VectorStore


def test_end_to_end_annotation_embedding_and_query_flow():
    broker = InMemoryBroker()

    document_store = DocumentStore()
    vector_store = VectorStore()

    document_processed_store = ProcessedEventStore()
    embedding_processed_store = ProcessedEventStore()
    query_processed_store = ProcessedEventStore()

    document_service = DocumentService(
        broker,
        document_store,
        document_processed_store,
    )
    embedding_service = EmbeddingService(
        broker,
        document_store,
        vector_store,
        embedding_processed_store,
    )
    query_service = QueryService(
        broker,
        vector_store,
        query_processed_store,
    )

    document_service.start()
    embedding_service.start()
    query_service.start()

    embedding_events = []
    query_completed_events = []

    def embedding_handler(event: dict) -> None:
        embedding_events.append(event)

    def query_completed_handler(event: dict) -> None:
        query_completed_events.append(event)

    broker.subscribe(EMBEDDING_CREATED, embedding_handler)
    broker.subscribe(QUERY_COMPLETED, query_completed_handler)

    inference_event = create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_pipeline_1",
            "objects": [
                {"label": "car", "confidence": 0.92},
                {"label": "person", "confidence": 0.84},
            ],
            "model_version": "v1",
        },
        source="integration-test",
    ).model_dump(mode="json")

    broker.publish(INFERENCE_COMPLETED, inference_event)

    stored_doc = document_store.get("img_pipeline_1")
    assert stored_doc is not None
    assert stored_doc["image_id"] == "img_pipeline_1"
    assert len(stored_doc["objects"]) == 2

    stored_vector = vector_store.get("img_pipeline_1")
    assert stored_vector is not None
    assert len(stored_vector) == 4

    assert len(embedding_events) == 1
    assert embedding_events[0]["payload"]["image_id"] == "img_pipeline_1"

    query_event = create_event(
        QUERY_SUBMITTED,
        {
            "query_id": "q_pipeline_1",
            "query_text": "car",
            "top_k": 1,
        },
        source="integration-test",
    ).model_dump(mode="json")

    broker.publish(QUERY_SUBMITTED, query_event)

    assert len(query_completed_events) == 1
    completed = query_completed_events[0]

    assert completed["payload"]["query_id"] == "q_pipeline_1"
    assert len(completed["payload"]["results"]) == 1
    assert completed["payload"]["results"][0]["image_id"] == "img_pipeline_1"


def test_end_to_end_image_to_image_query_flow():
    broker = InMemoryBroker()

    document_store = DocumentStore()
    vector_store = VectorStore()

    document_processed_store = ProcessedEventStore()
    embedding_processed_store = ProcessedEventStore()
    query_processed_store = ProcessedEventStore()

    document_service = DocumentService(
        broker,
        document_store,
        document_processed_store,
    )
    embedding_service = EmbeddingService(
        broker,
        document_store,
        vector_store,
        embedding_processed_store,
    )
    query_service = QueryService(
        broker,
        vector_store,
        query_processed_store,
    )

    document_service.start()
    embedding_service.start()
    query_service.start()

    image_query_completed_events = []

    def image_query_completed_handler(event: dict) -> None:
        image_query_completed_events.append(event)

    broker.subscribe(IMAGE_QUERY_COMPLETED, image_query_completed_handler)

    inference_event = create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_pipeline_2",
            "objects": [
                {"label": "car", "confidence": 0.92},
                {"label": "person", "confidence": 0.84},
            ],
            "model_version": "v1",
        },
        source="integration-test",
    ).model_dump(mode="json")

    broker.publish(INFERENCE_COMPLETED, inference_event)

    image_query_event = create_event(
        IMAGE_QUERY_SUBMITTED,
        {
            "query_id": "iq_pipeline_1",
            "image_id": "img_pipeline_2",
            "top_k": 1,
        },
        source="integration-test",
    ).model_dump(mode="json")

    broker.publish(IMAGE_QUERY_SUBMITTED, image_query_event)

    assert len(image_query_completed_events) == 1
    completed = image_query_completed_events[0]

    assert completed["payload"]["query_id"] == "iq_pipeline_1"
    assert len(completed["payload"]["results"]) == 1
    assert completed["payload"]["results"][0]["image_id"] == "img_pipeline_2"
