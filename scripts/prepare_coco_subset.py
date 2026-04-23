import argparse
import json
import shutil
import sys
import urllib.request
from urllib.error import HTTPError, URLError
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import AppConfig


ANNOTATIONS_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
IMAGES_URL_TEMPLATE = "http://images.cocodataset.org/zips/{split}2017.zip"


def download_file(url: str, destination: Path) -> None:
    if destination.exists():
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except HTTPError as exc:
        raise RuntimeError(f"Download failed for {url}: HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Download failed for {url}: {exc.reason}") from exc


def ensure_zip_extracted(zip_path: Path, target_dir: Path) -> None:
    marker = target_dir / ".extract_complete"
    if marker.exists():
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target_dir)
    marker.write_text(zip_path.name, encoding="utf-8")


def build_subset_annotations(
    annotations_path: Path,
    split: str,
    category_names: set[str],
    max_images: int,
) -> tuple[list[dict], dict[str, dict]]:
    payload = json.loads(annotations_path.read_text(encoding="utf-8"))
    categories = {item["id"]: item["name"] for item in payload["categories"]}
    allowed_category_ids = {
        category_id
        for category_id, name in categories.items()
        if name in category_names
    }

    images_by_id = {item["id"]: item for item in payload["images"]}
    grouped_annotations: dict[int, list[dict]] = {}
    for annotation in payload["annotations"]:
        if annotation["category_id"] not in allowed_category_ids:
            continue
        grouped_annotations.setdefault(annotation["image_id"], []).append(annotation)

    subset_images: list[dict] = []
    simulated_annotations: dict[str, dict] = {}

    for image_id, annotations in grouped_annotations.items():
        if len(subset_images) >= max_images:
            break

        image = images_by_id[image_id]
        filename = image["file_name"]
        objects = []
        for annotation in annotations:
            x, y, width, height = annotation["bbox"]
            objects.append(
                {
                    "label": categories[annotation["category_id"]],
                    "bbox": [
                        round(x, 2),
                        round(y, 2),
                        round(x + width, 2),
                        round(y + height, 2),
                    ],
                    "confidence": 1.0,
                    "area": annotation.get("area"),
                }
            )

        subset_images.append(image)
        simulated_annotations[filename] = {
            "objects": objects,
            "model_version": f"coco-{split}2017-groundtruth",
        }

    return subset_images, simulated_annotations


def copy_subset_images(
    source_dir: Path,
    destination_dir: Path,
    images: list[dict],
) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    for image in images:
        source = source_dir / image["file_name"]
        destination = destination_dir / image["file_name"]
        if destination.exists():
            continue
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and prepare a small COCO subset for the demo pipeline",
    )
    parser.add_argument(
        "--split",
        default="val",
        choices=["train", "val"],
        help="COCO 2017 split to download",
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        default=["cat", "dog", "person"],
        help="Object classes to include in the subset",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to keep",
    )
    args = parser.parse_args()

    config = AppConfig.from_env()
    config.ensure_data_dirs()
    limit = min(args.limit or config.max_dataset_images, config.max_dataset_images)

    annotations_zip = config.coco_cache_dir / "annotations_trainval2017.zip"
    images_zip = config.coco_cache_dir / f"{args.split}2017.zip"
    extracted_root = config.coco_cache_dir / "extracted"
    annotations_extract_dir = extracted_root / "annotations_bundle"
    images_extract_dir = extracted_root / f"{args.split}_images_bundle"

    print("Downloading COCO archives if needed...")
    download_file(ANNOTATIONS_URL, annotations_zip)
    download_file(IMAGES_URL_TEMPLATE.format(split=args.split), images_zip)

    print("Extracting COCO archives if needed...")
    ensure_zip_extracted(annotations_zip, annotations_extract_dir)
    ensure_zip_extracted(images_zip, images_extract_dir)

    annotations_path = (
        annotations_extract_dir / "annotations" / f"instances_{args.split}2017.json"
    )
    image_root = images_extract_dir / f"{args.split}2017"

    print("Selecting subset and converting annotations...")
    subset_images, simulated_annotations = build_subset_annotations(
        annotations_path=annotations_path,
        split=args.split,
        category_names=set(args.classes),
        max_images=limit,
    )

    copy_subset_images(image_root, config.images_dir, subset_images)
    config.annotations_path.write_text(
        json.dumps(simulated_annotations, indent=2),
        encoding="utf-8",
    )

    manifest_path = config.data_dir / "annotations" / "subset_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "split": args.split,
                "classes": args.classes,
                "limit": limit,
                "selected_images": [image["file_name"] for image in subset_images],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Prepared {len(subset_images)} images in {config.images_dir}")
    print(f"Wrote annotations to {config.annotations_path}")
    print(f"Wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

