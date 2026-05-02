import mongomock

from app.storage.mongo_document_store import MongoDocumentStore


def test_mongo_document_store_save_and_get():
    client = mongomock.MongoClient()
    store = MongoDocumentStore(
        mongo_uri="mongodb://unused",
        database_name="test_db",
        collection_name="documents",
        client=client,
    )

    document = {
        "image_id": "img_1",
        "objects": [{"label": "car", "confidence": 0.9}],
        "status": "stored",
    }

    store.save("img_1", document)

    assert store.get("img_1") == document
    assert store.count() == 1


def test_mongo_document_store_all_and_clear():
    client = mongomock.MongoClient()
    store = MongoDocumentStore(
        mongo_uri="mongodb://unused",
        database_name="test_db",
        collection_name="documents",
        client=client,
    )

    store.save("img_1", {"image_id": "img_1"})
    store.save("img_2", {"image_id": "img_2"})

    documents = store.all()

    assert len(documents) == 2
    assert "img_1" in documents
    assert "img_2" in documents

    store.clear()
    assert store.count() == 0
