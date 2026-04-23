import argparse
import json
from uuid import uuid4

from app.config import AppConfig
from app.events.factory import create_event
from app.events.topics import QUERY_COMPLETED, QUERY_SUBMITTED
from app.main import build_application
from app.services.image_service import ImageService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Event-driven image annotation and retrieval demo CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload", help="Submit one image into the pipeline")
    upload_parser.add_argument("image_path")
    upload_parser.add_argument("--source", default="cli")

    query_parser = subparsers.add_parser("query", help="Run a natural-language image query")
    query_parser.add_argument("query_text")
    query_parser.add_argument("--top-k", type=int, default=3)
    query_parser.add_argument("--source", default="cli")
    query_parser.add_argument("--timeout", type=float, default=5.0)

    paths_parser = subparsers.add_parser("paths", help="Show configured data paths")
    paths_parser.add_argument("--json", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = AppConfig.from_env()

    if args.command == "paths":
        payload = {
            "root_dir": str(config.root_dir),
            "data_dir": str(config.data_dir),
            "images_dir": str(config.images_dir),
            "annotations_path": str(config.annotations_path),
            "coco_cache_dir": str(config.coco_cache_dir),
            "broker_backend": config.broker_backend,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for key, value in payload.items():
                print(f"{key}: {value}")
        return 0

    if config.broker_backend == "redis":
        from app.broker.redis_broker import RedisBroker
        import redis

        broker = RedisBroker(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
        )
        try:
            if args.command == "upload":
                event = ImageService(broker).submit_image(args.image_path, source=args.source)
                print(json.dumps(event, indent=2))
                return 0

            if args.command == "query":
                query_id = f"qry_{uuid4().hex[:8]}"
                client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    decode_responses=True,
                )
                pubsub = client.pubsub()
                pubsub.subscribe(QUERY_COMPLETED)

                event = create_event(
                    QUERY_SUBMITTED,
                    {
                        "query_id": query_id,
                        "query_text": args.query_text,
                        "top_k": args.top_k,
                    },
                    source=args.source,
                ).model_dump(mode="json")
                broker.publish(QUERY_SUBMITTED, event)

                try:
                    response = pubsub.get_message(timeout=args.timeout)
                    while response:
                        if response["type"] == "message":
                            payload = json.loads(response["data"])
                            if payload["payload"].get("query_id") == query_id:
                                print(json.dumps(payload, indent=2))
                                return 0
                        response = pubsub.get_message(timeout=args.timeout)
                finally:
                    pubsub.close()
                    client.close()

                raise TimeoutError(
                    f"Timed out waiting {args.timeout} seconds for query.completed"
                )
        finally:
            broker.close()

    app = build_application(config).start()

    try:
        if args.command == "upload":
            event = app.submit_image(args.image_path, source=args.source)
            print(json.dumps(event, indent=2))
            return 0

        if args.command == "query":
            result = app.submit_query(
                args.query_text,
                top_k=args.top_k,
                source=args.source,
            )
            print(json.dumps(result, indent=2))
            return 0
    finally:
        app.close()

    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

