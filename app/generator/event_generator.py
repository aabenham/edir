import random
from datetime import datetime, timezone
from typing import Any

from app.broker.base import BaseBroker
from app.events.factory import create_event
from app.events.topics import (
    ANNOTATION_CORRECTED,
    ANNOTATION_STORED,
    EMBEDDING_CREATED,
    IMAGE_SUBMITTED,
    INFERENCE_COMPLETED,
    QUERY_COMPLETED,
    QUERY_SUBMITTED,
    SYSTEM_ERROR,
)


class EventGenerator:
    def __init__(self, broker: BaseBroker, seed: int | None = None) -> None:
        self.broker = broker
        self.random = random.Random(seed)

    def _random_id(self, prefix: str) -> str:
        return f"{prefix}_{self.random.randint(1000, 9999)}"

    def generate_payload(self, topic: str) -> dict[str, Any]:
        if topic == IMAGE_SUBMITTED:
            image_id = self._random_id("img")
            return {
                "image_id": image_id,
                "image_path": f"images/{image_id}.jpg",
                "source": "camera_A",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        if topic == INFERENCE_COMPLETED:
            return {
                "image_id": self._random_id("img"),
                "objects": [
                    {"label": "car", "confidence": 0.91},
                    {"label": "person", "confidence": 0.87},
                ],
                "model_version": "v1",
            }

        if topic == ANNOTATION_STORED:
            return {
                "image_id": self._random_id("img"),
                "document_id": self._random_id("doc"),
                "status": "stored",
            }

        if topic == EMBEDDING_CREATED:
            return {
                "image_id": self._random_id("img"),
                "embedding": [0.11, 0.22, 0.33, 0.44],
                "model_name": "mock-embedding-model",
            }

        if topic == QUERY_SUBMITTED:
            return {
                "query_id": self._random_id("qry"),
                "query_text": "red car",
                "top_k": 3,
            }

        if topic == QUERY_COMPLETED:
            return {
                "query_id": self._random_id("qry"),
                "results": [
                    {"image_id": "img_1001", "score": 0.95},
                    {"image_id": "img_1002", "score": 0.89},
                ],
            }

        if topic == ANNOTATION_CORRECTED:
            return {
                "image_id": self._random_id("img"),
                "corrections": [{"from": "car", "to": "truck"}],
                "reviewer": "human_reviewer",
            }

        if topic == SYSTEM_ERROR:
            return {
                "failed_topic": IMAGE_SUBMITTED,
                "reason": "malformed payload",
            }

        raise ValueError(f"Unsupported topic: {topic}")

    def publish_event(self, topic: str, source: str = "event_generator") -> dict[str, Any]:
        payload = self.generate_payload(topic)
        event = create_event(topic, payload, source=source)
        event_dict = event.model_dump(mode="json")
        self.broker.publish(topic, event_dict)
        return event_dict

    def publish_duplicate_event(self, topic: str, source: str = "event_generator") -> tuple[dict[str, Any], dict[str, Any]]:
        payload = self.generate_payload(topic)
        event = create_event(topic, payload, source=source)
        event_dict = event.model_dump(mode="json")

        self.broker.publish(topic, event_dict)
        self.broker.publish(topic, event_dict)

        return event_dict, event_dict

    def publish_malformed_event(self, topic: str) -> dict[str, Any]:
        bad_event = {
            "bad_field": "bad_value",
            "payload": {
                "unexpected": True,
            },
        }
        self.broker.publish(topic, bad_event)
        return bad_event