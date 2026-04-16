from app.storage.vector_store import VectorStore


def test_vector_store_add_and_get():
    store = VectorStore()
    vector = [0.1, 0.2, 0.3]

    store.add("img_1", vector)

    assert store.get("img_1") == vector
    assert store.count() == 1


def test_vector_store_search_returns_top_matches():
    store = VectorStore()

    store.add("img_1", [1.0, 0.0, 0.0])
    store.add("img_2", [0.9, 0.1, 0.0])
    store.add("img_3", [0.0, 1.0, 0.0])

    results = store.search([1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2
    assert results[0]["image_id"] == "img_1"
    assert results[1]["image_id"] == "img_2"