from app.storage.processed_event_store import ProcessedEventStore


def test_processed_event_store_tracks_processed_ids():
    store = ProcessedEventStore()

    assert store.has_processed("evt_1") is False

    store.mark_processed("evt_1")

    assert store.has_processed("evt_1") is True
    assert store.count() == 1


def test_processed_event_store_clear_removes_all_ids():
    store = ProcessedEventStore()

    store.mark_processed("evt_1")
    store.mark_processed("evt_2")
    assert store.count() == 2

    store.clear()
    assert store.count() == 0