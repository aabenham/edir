import json
from pathlib import Path

from app.broker.base import BaseBroker
from app.events.factory import create_event
from app.events.topics import IMAGE_SUBMITTED, INFERENCE_COMPLETED, SYSTEM_ERROR
from app.events.validator import validate_event_for_topic
from app.storage.processed_event_store import ProcessedEventStore


class InferenceService:
    def __init__(
        self,
        broker: BaseBroker,
        processed_event_store: ProcessedEventStore,
        annotations_path: str,
    ) -> None:
        self.broker = broker
        self.processed_event_store = processed_event_store
        self.annotations_path = Path(annotations_path)
        self.annotations = self._load_annotations()

    def _load_annotations(self) -> dict:
        if not self.annotations_path.exists():
            return {}

        with self.annotations_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def start(self) -> None:
        self.broker.subscribe(IMAGE_SUBMITTED, self.handle_image_submitted)

    def handle_image_submitted(self, event: dict) -> None:
        if not validate_event_for_topic(IMAGE_SUBMITTED, event):
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": IMAGE_SUBMITTED,
                    "reason": "invalid event structure for inference service",
                },
                source="inference_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            return

        event_id = event["metadata"]["event_id"]
        if self.processed_event_store.has_processed(event_id):
            return

        payload = event["payload"]
        image_id = payload["image_id"]
        filename = payload["filename"]

        annotation = self.annotations.get(filename)
        if annotation is None:
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": IMAGE_SUBMITTED,
                    "reason": f"no simulated annotation found for filename={filename}",
                },
                source="inference_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            return

        inference_event = create_event(
            INFERENCE_COMPLETED,
            {
                "image_id": image_id,
                "objects": annotation.get("objects", []),
                "model_version": annotation.get("model_version", "coco-sim-v1"),
            },
            source="inference_service",
        ).model_dump(mode="json")

        self.processed_event_store.mark_processed(event_id)
        self.broker.publish(INFERENCE_COMPLETED, inference_event)