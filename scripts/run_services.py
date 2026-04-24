import argparse
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import AppConfig  # noqa: E402
from app.main import build_application  # noqa: E402
from app.services.document_service import DocumentService  # noqa: E402
from app.services.embedding_service import EmbeddingService  # noqa: E402
from app.services.inference_service import InferenceService  # noqa: E402
from app.services.query_service import QueryService  # noqa: E402
from app.storage.document_store import DocumentStore  # noqa: E402
from app.storage.processed_event_store import ProcessedEventStore  # noqa: E402
from app.storage.vector_store import VectorStore  # noqa: E402


def run_redis_services(config: AppConfig) -> None:
    from app.broker.redis_broker import RedisBroker

    document_store = DocumentStore()
    vector_store = VectorStore()

    services = [
        InferenceService(
            RedisBroker(config.redis_host, config.redis_port, config.redis_db),
            ProcessedEventStore(),
            str(config.annotations_path),
        ),
        DocumentService(
            RedisBroker(config.redis_host, config.redis_port, config.redis_db),
            document_store,
            ProcessedEventStore(),
        ),
        EmbeddingService(
            RedisBroker(config.redis_host, config.redis_port, config.redis_db),
            document_store,
            vector_store,
            ProcessedEventStore(),
        ),
        QueryService(
            RedisBroker(config.redis_host, config.redis_port, config.redis_db),
            vector_store,
            ProcessedEventStore(),
        ),
    ]

    threads = [
        threading.Thread(target=service.start, daemon=True)
        for service in services
    ]

    for thread in threads:
        thread.start()

    print(f"Broker: {config.broker_backend}")
    print(f"Annotations: {config.annotations_path}")
    print("Redis-backed service listeners are running.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services.")
    finally:
        for service in services:
            service.broker.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the event-driven demo services")
    parser.add_argument(
        "--broker",
        choices=["inmemory", "redis"],
        default=None,
        help="Override the configured broker backend",
    )
    args = parser.parse_args()

    config = AppConfig.from_env()
    if args.broker:
        config = AppConfig(
            root_dir=config.root_dir,
            broker_backend=args.broker,
            redis_host=config.redis_host,
            redis_port=config.redis_port,
            redis_db=config.redis_db,
            data_dir=config.data_dir,
            images_dir=config.images_dir,
            annotations_path=config.annotations_path,
            coco_cache_dir=config.coco_cache_dir,
            max_dataset_images=config.max_dataset_images,
        )

    if config.broker_backend == "redis":
        run_redis_services(config)
        return 0

    app = build_application(config).start()
    try:
        print(f"Broker: {config.broker_backend}")
        print(f"Annotations: {config.annotations_path}")
        print("Services are ready. Use the CLI to submit uploads and queries.")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services.")
    finally:
        app.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
