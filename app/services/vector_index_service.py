from app.storage.vector_store import VectorStore


class VectorIndexService:
    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def upsert(self, image_id: str, embedding: list[float]) -> None:
        self.vector_store.add(image_id, embedding)

    def search(self, query_vector: list[float], top_k: int = 3) -> list[dict]:
        return self.vector_store.search(query_vector, top_k=top_k)

