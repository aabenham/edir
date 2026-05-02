import pytest

faiss = pytest.importorskip("faiss")

from app.storage.faiss_vector_store import FaissVectorStore  # noqa: E402


def test_faiss_vector_store_add_and_get():
    _ = faiss
    store = FaissVectorStore()
    vector = [42.3601, -71.0589]

    store.add("img_1", vector)

    assert store.get("img_1") == vector
    assert store.count() == 1


def test_faiss_vector_store_search_returns_top_matches():
    _ = faiss
    store = FaissVectorStore()

    store.add("img_cat", [42.3601, -71.0589])
    store.add("img_dog", [40.7128, -74.0060])
    store.add("img_car", [34.0522, -118.2437])

    results = store.search([42.3601, -71.0589], top_k=2)

    assert len(results) == 2
    assert results[0]["image_id"] == "img_cat"
    assert results[1]["image_id"] == "img_dog"
