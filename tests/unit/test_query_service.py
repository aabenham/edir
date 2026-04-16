from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import QUERY_COMPLETED, QUERY_SUBMITTED, SYSTEM_ERROR
from app.services.query_service import QueryService
from app.storage.processed_event_store import ProcessedEventStore
from app.storage.vector_store import VectorStore


def test_query_service_searches_vectors_and_publishes_query_completed():
    broker = InMemoryBroker()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    vector_store.add("img_car_1", [2.0, 0.90, 0.0, 2.0])
    vector_store.add("img_truck_1", [1.0, 0.95, 0.0, 2.0])
    vector_store.add("img_random_1", [0.0, 0.10, 0.0, 1.0])

    service = QueryService(
        broker,
        vector_store,
        processed_store,
    )

    completed_queries = []

    def completed_handler(event: dict) -> None:
        completed_queries.append(event)

    broker.subscribe(QUERY_COMPLETED, completed_handler)
    service.start()

    query_event = create_event(
        QUERY_SUBMITTED,
        {
            "query_id": "q_7001",
            "query_text": "car",
            "top_k": 2,
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(QUERY_SUBMITTED, query_event)

    assert len(completed_queries) == 1
    completed_event = completed_queries[0]

    assert completed_event["metadata"]["event_type"] == QUERY_COMPLETED
    assert completed_event["payload"]["query_id"] == "q_7001"
    assert len(completed_event["payload"]["results"]) == 2
    assert completed_event["payload"]["results"][0]["image_id"] == "img_car_1"


def test_query_service_ignores_duplicate_events():
    broker = InMemoryBroker()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    vector_store.add("img_car_2", [2.0, 0.88, 0.0, 2.0])

    service = QueryService(
        broker,
        vector_store,
        processed_store,
    )

    completed_queries = []

    def completed_handler(event: dict) -> None:
        completed_queries.append(event)

    broker.subscribe(QUERY_COMPLETED, completed_handler)
    service.start()

    query_event = create_event(
        QUERY_SUBMITTED,
        {
            "query_id": "q_7002",
            "query_text": "car",
            "top_k": 1,
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(QUERY_SUBMITTED, query_event)
    broker.publish(QUERY_SUBMITTED, query_event)

    assert processed_store.count() == 1
    assert len(completed_queries) == 1


def test_query_service_publishes_system_error_for_invalid_event():
    broker = InMemoryBroker()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    service = QueryService(
        broker,
        vector_store,
        processed_store,
    )

    system_errors = []

    def error_handler(event: dict) -> None:
        system_errors.append(event)

    broker.subscribe(SYSTEM_ERROR, error_handler)
    service.start()

    invalid_event = {
        "payload": {
            "query_id": "q_bad",
            "query_text": "car",
        }
    }

    broker.publish(QUERY_SUBMITTED, invalid_event)

    assert processed_store.count() == 0
    assert len(system_errors) == 1
    assert system_errors[0]["metadata"]["event_type"] == SYSTEM_ERROR


def test_query_service_returns_empty_results_when_store_is_empty():
    broker = InMemoryBroker()
    vector_store = VectorStore()
    processed_store = ProcessedEventStore()

    service = QueryService(
        broker,
        vector_store,
        processed_store,
    )

    completed_queries = []

    def completed_handler(event: dict) -> None:
        completed_queries.append(event)

    broker.subscribe(QUERY_COMPLETED, completed_handler)
    service.start()

    query_event = create_event(
        QUERY_SUBMITTED,
        {
            "query_id": "q_7003",
            "query_text": "car",
            "top_k": 3,
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(QUERY_SUBMITTED, query_event)

    assert len(completed_queries) == 1
    assert completed_queries[0]["payload"]["results"] == []