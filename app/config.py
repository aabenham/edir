import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    broker_backend: str
    redis_host: str
    redis_port: int
    redis_db: int
    data_dir: Path
    images_dir: Path
    annotations_path: Path
    coco_cache_dir: Path
    max_dataset_images: int

    @classmethod
    def from_env(cls, root_dir: str | Path | None = None) -> "AppConfig":
        resolved_root = Path(root_dir or Path(__file__).resolve().parents[1]).resolve()
        data_dir = resolved_root / os.getenv("APP_DATA_DIR", "data")
        images_dir = data_dir / os.getenv("APP_IMAGES_SUBDIR", "images")
        annotations_path = data_dir / os.getenv(
            "APP_ANNOTATIONS_FILE",
            "annotations/simulated_annotations.json",
        )
        coco_cache_dir = data_dir / os.getenv("APP_COCO_CACHE_SUBDIR", "raw/coco")

        return cls(
            root_dir=resolved_root,
            broker_backend=os.getenv("APP_BROKER", "inmemory").lower(),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            data_dir=data_dir,
            images_dir=images_dir,
            annotations_path=annotations_path,
            coco_cache_dir=coco_cache_dir,
            max_dataset_images=int(os.getenv("APP_MAX_DATASET_IMAGES", "30")),
        )

    def ensure_data_dirs(self) -> None:
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_path.parent.mkdir(parents=True, exist_ok=True)
        self.coco_cache_dir.mkdir(parents=True, exist_ok=True)
