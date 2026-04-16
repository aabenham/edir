from app.storage.document_store import DocumentStore


def test_document_store_save_and_get():
    store = DocumentStore()

    doc = {
        "image_id": "img_1",
        "objects": [{"label": "car", "confidence": 0.9}],
        "status": "stored",
    }

    store.save("img_1", doc)

    assert store.get("img_1") == doc
    assert store.count() == 1


def test_document_store_all_returns_saved_documents():
    store = DocumentStore()

    store.save("img_1", {"image_id": "img_1"})
    store.save("img_2", {"image_id": "img_2"})

    documents = store.all()

    assert len(documents) == 2
    assert "img_1" in documents
    assert "img_2" in documents