from app.events.factory import create_event


def test_create_event():
    event = create_event(
        "image.submitted",
        {"image_id": "img-1", "image_path": "sample.jpg"},
        source="unit-test",
    )

    assert event.metadata.event_type == "image.submitted"
    assert event.metadata.source == "unit-test"
    assert event.payload["image_id"] == "img-1"