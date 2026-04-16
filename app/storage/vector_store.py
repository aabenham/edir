import math


class VectorStore:
    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}

    def add(self, image_id: str, vector: list[float]) -> None:
        self._vectors[image_id] = vector

    def get(self, image_id: str) -> list[float] | None:
        return self._vectors.get(image_id)

    def count(self) -> int:
        return len(self._vectors)

    def clear(self) -> None:
        self._vectors.clear()

    def search(self, query_vector: list[float], top_k: int = 3) -> list[dict]:
        scored = []

        for image_id, vector in self._vectors.items():
            score = self._cosine_similarity(query_vector, vector)
            scored.append({"image_id": image_id, "score": score})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            raise ValueError("Vectors must have the same length")

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)