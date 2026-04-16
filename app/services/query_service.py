from app.broker.base import BaseBroker
from app.events.factory import create_event
from app.events.topics import QUERY_COMPLETED, QUERY_SUBMITTED, SYSTEM_ERROR
from app.events.validator import validate_event_for_topic
from app.storage.processed_event_store import ProcessedEventStore
from app.storage.vector_store import VectorStore


class QueryService:
    def __init__(
        self,
        broker: BaseBroker,
        vector_store: VectorStore,
        processed_event_store: ProcessedEventStore,
    ) -> None:
        self.broker = broker
        self.vector_store = vector_store
        self.processed_event_store = processed_event_store

    def start(self) -> None:
        self.broker.subscribe(QUERY_SUBMITTED, self.handle_query_submitted)

    def handle_query_submitted(self, event: dict) -> None:
        if not validate_event_for_topic(QUERY_SUBMITTED, event):
            error_event = create_event(
                SYSTEM_ERROR,
                {
                    "failed_topic": QUERY_SUBMITTED,
                    "reason": "invalid event structure for query service",
                },
                source="query_service",
            ).model_dump(mode="json")
            self.broker.publish(SYSTEM_ERROR, error_event)
            return

        event_id = event["metadata"]["event_id"]
        if self.processed_event_store.has_processed(event_id):
            return

        payload = event["payload"]
        query_id = payload["query_id"]
        query_text = payload["query_text"]
        top_k = payload.get("top_k", 3)

        query_vector = self._generate_mock_query_embedding(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k)

        self.processed_event_store.mark_processed(event_id)

        completed_event = create_event(
            QUERY_COMPLETED,
            {
                "query_id": query_id,
                "query_text": query_text,
                "top_k": top_k,
                "results": results,
            },
            source="query_service",
        ).model_dump(mode="json")

        self.broker.publish(QUERY_COMPLETED, completed_event)

    def _generate_mock_query_embedding(self, query_text: str) -> list[float]:
        text = query_text.lower()

        if "car" in text:
            return [2.0, 0.85, 0.0, 2.0]
        if "truck" in text:
            return [1.0, 0.95, 0.0, 2.0]
        if "person" in text:
            return [1.0, 0.80, 0.0, 2.0]

        return [1.0, 0.50, 0.0, 1.0]