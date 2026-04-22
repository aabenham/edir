from pathlib import Path

from app.broker.base import BaseBroker
from app.events.factory import create_event
from app.events.topics import IMAGE_SUBMITTED, SYSTEM_ERROR


class ImageService:
    def __init__(self, broker: BaseBroker) -> None:
        self.broker = broker

    def submit_image(self, image_path: str, source: str = "cli") -> dict:
        path = Path(image_path)

        if not path.exists() or not path.is_file():
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": IMAGE_SUBMITTED,
                    "reason": f"image file not found: {image_path}",
                },
                source="image_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            raise FileNotFoundError(f"Image file not found: {image_path}")

        event = create_event(
            IMAGE_SUBMITTED,
            {
                "image_id": path.stem,
                "image_path": str(path),
                "filename": path.name,
                "source": source,
            },
            source="image_service",
        ).model_dump(mode="json")

        self.broker.publish(IMAGE_SUBMITTED, event)
        return event