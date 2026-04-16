from app.broker.base import BaseBroker
from app.events.factory import create_event
from app.events.topics import ANNOTATION_STORED, EMBEDDING_CREATED, SYSTEM_ERROR
from app.events.validator import validate_event_for_topic
from app.storage.document_store import DocumentStore
from app.storage.processed_event_store import ProcessedEventStore
from app.storage.vector_store import VectorStore


class EmbeddingService:
    def __init__(
        self,
        broker: BaseBroker,
        document_store: DocumentStore,
        vector_store: VectorStore,
        processed_event_store: ProcessedEventStore,
    ) -> None:
        self.broker = broker
        self.document_store = document_store
        self.vector_store = vector_store
        self.processed_event_store = processed_event_store

    def start(self) -> None:
        self.broker.subscribe(ANNOTATION_STORED, self.handle_annotation_stored)

    def handle_annotation_stored(self, event: dict) -> None:
        if not validate_event_for_topic(ANNOTATION_STORED, event):
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": ANNOTATION_STORED,
                    "reason": "invalid event structure for embedding service",
                },
                source="embedding_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            return

        event_id = event["metadata"]["event_id"]
        if self.processed_event_store.has_processed(event_id):
            return

        image_id = event["payload"]["image_id"]
        document = self.document_store.get(image_id)

        if document is None:
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": ANNOTATION_STORED,
                    "reason": f"document not found for image_id={image_id}",
                },
                source="embedding_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            return

        embedding = self._generate_mock_embedding(document)

        self.vector_store.add(image_id, embedding)
        self.processed_event_store.mark_processed(event_id)

        embedding_event = create_event(
            EMBEDDING_CREATED,
            {
                "image_id": image_id,
                "embedding": embedding,
                "model_name": "mock-embedding-model",
            },
            source="embedding_service",
        ).model_dump(mode="json")

        self.broker.publish(EMBEDDING_CREATED, embedding_event)

    def _generate_mock_embedding(self, document: dict) -> list[float]:
        objects = document.get("objects", [])
        object_count = len(objects)
        avg_confidence = (
            sum(obj.get("confidence", 0.0) for obj in objects) / object_count
            if object_count > 0
            else 0.0
        )
        has_review = 1.0 if "review" in document else 0.0
        history_length = float(len(document.get("history", [])))

        return [
            float(object_count),
            round(avg_confidence, 4),
            has_review,
            history_length,
        ]