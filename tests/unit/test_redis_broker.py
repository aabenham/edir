import json

import fakeredis

from app.broker.redis_broker import RedisBroker


def test_redis_broker_publish_sends_message():
    fake_client = fakeredis.FakeRedis(decode_responses=True)

    broker = RedisBroker()
    broker._client = fake_client

    pubsub = fake_client.pubsub()
    pubsub.subscribe("image.submitted")

    event = {
        "metadata": {
            "event_id": "evt-1",
            "event_type": "image.submitted",
            "timestamp": "2026-04-14T12:00:00Z",
            "source": "test",
        },
        "payload": {
            "image_id": "img-1",
            "image_path": "images/test.jpg",
        },
    }

    broker.publish("image.submitted", event)

    message = pubsub.get_message(timeout=1)

    while message and message["type"] != "message":
        message = pubsub.get_message(timeout=1)

    assert message is not None
    data = json.loads(message["data"])

    assert data["metadata"]["event_type"] == "image.submitted"
    assert data["payload"]["image_id"] == "img-1"


def test_redis_broker_serializes_event_correctly():
    fake_client = fakeredis.FakeRedis(decode_responses=True)

    broker = RedisBroker()
    broker._client = fake_client

    pubsub = fake_client.pubsub()
    pubsub.subscribe("query.submitted")

    event = {
        "metadata": {
            "event_id": "evt-2",
            "event_type": "query.submitted",
            "timestamp": "2026-04-14T12:01:00Z",
            "source": "test",
        },
        "payload": {
            "query_id": "q-1",
            "query_text": "car",
            "top_k": 3,
        },
    }

    broker.publish("query.submitted", event)

    message = pubsub.get_message(timeout=1)

    while message and message["type"] != "message":
        message = pubsub.get_message(timeout=1)

    assert message is not None
    decoded = json.loads(message["data"])

    assert decoded["metadata"]["event_type"] == "query.submitted"
    assert decoded["payload"]["query_text"] == "car"
    assert decoded["payload"]["top_k"] == 3