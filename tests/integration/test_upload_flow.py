import json
from pathlib import Path

from app.main import build_application
from app.config import AppConfig


def test_upload_flow_runs_end_to_end_from_image_submission(tmp_path: Path):
    data_dir = tmp_path / "data"
    images_dir = data_dir / "images"
    annotations_dir = data_dir / "annotations"
    images_dir.mkdir(parents=True)
    annotations_dir.mkdir(parents=True)

    image_path = images_dir / "cat_101.jpg"
    image_path.write_text("fake image content", encoding="utf-8")

    annotations_path = annotations_dir / "simulated_annotations.json"
    annotations_path.write_text(
        json.dumps(
            {
                "cat_101.jpg": {
                    "objects": [
                        {
                            "label": "cat",
                            "bbox": [12, 18, 150, 190],
                            "confidence": 0.99,
                        }
                    ],
                    "model_version": "test-v1",
                }
            }
        ),
        encoding="utf-8",
    )

    config = AppConfig(
        root_dir=tmp_path,
        broker_backend="inmemory",
        redis_host="localhost",
        redis_port=6379,
        redis_db=0,
        data_dir=data_dir,
        images_dir=images_dir,
        annotations_path=annotations_path,
        coco_cache_dir=data_dir / "raw" / "coco",
        max_dataset_images=30,
    )

    app = build_application(config).start()
    try:
        submitted = app.submit_image(str(image_path), source="integration-test")
    finally:
        app.close()

    assert submitted["metadata"]["event_type"] == "image.submitted"

    document = app.document_store.get("cat_101")
    assert document is not None
    assert document["objects"][0]["label"] == "cat"

    vector = app.vector_store.get("cat_101")
    assert vector is not None
    assert len(vector) == 4

