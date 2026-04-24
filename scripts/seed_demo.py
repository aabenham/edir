import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import AppConfig  # noqa: E402


def main() -> int:
    config = AppConfig.from_env()
    config.ensure_data_dirs()

    sample_annotations = {
        "cat_001.jpg": {
            "objects": [
                {
                    "label": "cat",
                    "bbox": [18, 24, 180, 210],
                    "confidence": 0.98,
                }
            ],
            "model_version": "simulated-coco-v1",
        },
        "dog_001.jpg": {
            "objects": [
                {
                    "label": "dog",
                    "bbox": [12, 40, 210, 230],
                    "confidence": 0.97,
                }
            ],
            "model_version": "simulated-coco-v1",
        },
    }

    config.annotations_path.write_text(
        json.dumps(sample_annotations, indent=2),
        encoding="utf-8",
    )

    readme_path = config.data_dir / "README.txt"
    readme_path.write_text(
        "Place your downloaded subset images under data/images/ and keep\n"
        "their filenames aligned with data/annotations/simulated_annotations.json.\n",
        encoding="utf-8",
    )

    print(f"Seeded annotations at {config.annotations_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
