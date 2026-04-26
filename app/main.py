from dataclasses import dataclass
from uuid import uuid4

from app.broker.base import BaseBroker
from app.broker.in_memory_broker import InMemoryBroker
from app.config import AppConfig
from app.events.factory import create_event
from app.events.topics import (
    IMAGE_QUERY_COMPLETED,
    IMAGE_QUERY_SUBMITTED,
    QUERY_COMPLETED,
    QUERY_SUBMITTED,
)
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.image_service import ImageService
from app.services.inference_service import InferenceService
from app.services.query_service import QueryService
from app.storage.document_store import DocumentStore
from app.storage.processed_event_store import ProcessedEventStore
from app.storage.vector_store import VectorStore


@dataclass
class Application:
    config: AppConfig
    broker: BaseBroker
    image_service: ImageService
    inference_service: InferenceService
    document_service: DocumentService
    embedding_service: EmbeddingService
    query_service: QueryService
    document_store: DocumentStore
    vector_store: VectorStore

    def start(self) -> "Application":
        self.inference_service.start()
        self.document_service.start()
        self.embedding_service.start()
        self.query_service.start()
        return self

    def submit_image(self, image_path: str, source: str = "cli") -> dict:
        return self.image_service.submit_image(image_path, source=source)

    def submit_query(self, query_text: str, top_k: int = 3, source: str = "cli") -> dict:
        responses: list[dict] = []

        def capture_response(event: dict) -> None:
            responses.append(event)

        self.broker.subscribe(QUERY_COMPLETED, capture_response)

        query_event = create_event(
            QUERY_SUBMITTED,
            {
                "query_id": f"qry_{uuid4().hex[:8]}",
                "query_text": query_text,
                "top_k": top_k,
            },
            source=source,
        ).model_dump(mode="json")

        self.broker.publish(QUERY_SUBMITTED, query_event)
        return responses[-1] if responses else {}

    def submit_image_query(self, image_id: str, top_k: int = 3, source: str = "cli") -> dict:
        responses: list[dict] = []

        def capture_response(event: dict) -> None:
            responses.append(event)

        self.broker.subscribe(IMAGE_QUERY_COMPLETED, capture_response)

        query_event = create_event(
            IMAGE_QUERY_SUBMITTED,
            {
                "query_id": f"imgqry_{uuid4().hex[:8]}",
                "image_id": image_id,
                "top_k": top_k,
            },
            source=source,
        ).model_dump(mode="json")

        self.broker.publish(IMAGE_QUERY_SUBMITTED, query_event)
        return responses[-1] if responses else {}

    def close(self) -> None:
        self.broker.close()


def build_broker(config: AppConfig) -> BaseBroker:
    if config.broker_backend == "redis":
        from app.broker.redis_broker import RedisBroker

        return RedisBroker(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
        )

    return InMemoryBroker()


def build_application(config: AppConfig | None = None) -> Application:
    resolved_config = config or AppConfig.from_env()
    resolved_config.ensure_data_dirs()

    broker = build_broker(resolved_config)
    document_store = DocumentStore()
    vector_store = VectorStore()

    return Application(
        config=resolved_config,
        broker=broker,
        image_service=ImageService(broker),
        inference_service=InferenceService(
            broker,
            ProcessedEventStore(),
            str(resolved_config.annotations_path),
        ),
        document_service=DocumentService(
            broker,
            document_store,
            ProcessedEventStore(),
        ),
        embedding_service=EmbeddingService(
            broker,
            document_store,
            vector_store,
            ProcessedEventStore(),
        ),
        query_service=QueryService(
            broker,
            vector_store,
            ProcessedEventStore(),
        ),
        document_store=document_store,
        vector_store=vector_store,
    )
