from app.broker.in_memory_broker import InMemoryBroker
from app.events.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED
from app.events.validator import validate_event_structure
from app.generator.event_generator import EventGenerator


def test_event_generator_publishes_valid_event():
    broker = InMemoryBroker()
    received = []

    def handler(event: dict) -> None:
        received.append(event)

    broker.subscribe(IMAGE_SUBMITTED, handler)

    generator = EventGenerator(broker, seed=42)
    event = generator.publish_event(IMAGE_SUBMITTED)

    assert len(received) == 1
    assert received[0]["metadata"]["event_type"] == IMAGE_SUBMITTED
    assert validate_event_structure(event) is True


def test_event_generator_is_deterministic_for_seeded_ids():
    broker = InMemoryBroker()
    generator_one = EventGenerator(broker, seed=123)
    generator_two = EventGenerator(broker, seed=123)

    payload_one = generator_one.generate_payload(QUERY_SUBMITTED)
    payload_two = generator_two.generate_payload(QUERY_SUBMITTED)

    assert payload_one["query_id"] == payload_two["query_id"]


def test_event_generator_can_publish_duplicate_events():
    broker = InMemoryBroker()
    received = []

    def handler(event: dict) -> None:
        received.append(event)

    broker.subscribe(IMAGE_SUBMITTED, handler)

    generator = EventGenerator(broker, seed=99)
    first, second = generator.publish_duplicate_event(IMAGE_SUBMITTED)

    assert len(received) == 2
    assert first["metadata"]["event_id"] == second["metadata"]["event_id"]


def test_event_generator_can_publish_malformed_event():
    broker = InMemoryBroker()
    received = []

    def handler(event: dict) -> None:
        received.append(event)

    broker.subscribe(IMAGE_SUBMITTED, handler)

    generator = EventGenerator(broker)
    bad_event = generator.publish_malformed_event(IMAGE_SUBMITTED)

    assert len(received) == 1
    assert validate_event_structure(bad_event) is False