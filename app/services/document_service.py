from app.broker.base import BaseBroker
from app.events.factory import create_event
from app.events.topics import ANNOTATION_STORED, INFERENCE_COMPLETED, SYSTEM_ERROR
from app.events.validator import validate_event_for_topic
from app.storage.document_store import DocumentStore
from app.storage.processed_event_store import ProcessedEventStore


class DocumentService:
    def __init__(
        self,
        broker: BaseBroker,
        document_store: DocumentStore,
        processed_event_store: ProcessedEventStore,
    ) -> None:
        self.broker = broker
        self.document_store = document_store
        self.processed_event_store = processed_event_store

    def start(self) -> None:
        self.broker.subscribe(INFERENCE_COMPLETED, self.handle_inference_completed)

    def handle_inference_completed(self, event: dict) -> None:
        if not validate_event_for_topic(INFERENCE_COMPLETED, event):
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": INFERENCE_COMPLETED,
                    "reason": "invalid event structure for document service",
                },
                source="document_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            return

        event_id = event["metadata"]["event_id"]
        if self.processed_event_store.has_processed(event_id):
            return

        payload = event["payload"]
        image_id = payload["image_id"]

        document = {
            "image_id": image_id,
            "objects": payload.get("objects", []),
            "model_version": payload.get("model_version"),
            "status": "stored",
            "history": ["inference.completed", "annotation.stored"],
        }

        self.document_store.save(image_id, document)
        self.processed_event_store.mark_processed(event_id)

        stored_event = create_event(
            ANNOTATION_STORED,
            {
                "image_id": image_id,
                "document_id": image_id,
                "status": "stored",
            },
            source="document_service",
        ).model_dump(mode="json")

        self.broker.publish(ANNOTATION_STORED, stored_event)