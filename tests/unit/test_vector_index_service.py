from app.services.vector_index_service import VectorIndexService
from app.storage.vector_store import VectorStore


def test_vector_index_service_upserts_and_searches_vectors():
    vector_store = VectorStore()
    service = VectorIndexService(vector_store)

    service.upsert("img_1", [1.0, 0.9, 0.0, 2.0])
    service.upsert("img_2", [0.2, 0.1, 0.0, 1.0])

    results = service.search([1.0, 0.95, 0.0, 2.0], top_k=1)

    assert len(results) == 1
    assert results[0]["image_id"] == "img_1"

