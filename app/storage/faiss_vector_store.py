import math

import faiss
import numpy as np


class FaissVectorStore:
    def __init__(self) -> None:
        self._index: faiss.IndexFlatL2 | None = None
        self._dimension: int | None = None
        self._image_ids: list[str] = []
        self._vectors_by_id: dict[str, list[float]] = {}

    def add(self, image_id: str, vector: list[float]) -> None:
        if self._dimension is None:
            self._dimension = len(vector)
            self._index = faiss.IndexFlatL2(self._dimension)
        elif len(vector) != self._dimension:
            raise ValueError("Vectors must have the same length")

        if image_id in self._vectors_by_id:
            self._vectors_by_id[image_id] = vector
            self._rebuild_index()
            return

        self._vectors_by_id[image_id] = vector
        self._image_ids.append(image_id)
        assert self._index is not None
        self._index.add(np.array([vector], dtype="float32"))

    def get(self, image_id: str) -> list[float] | None:
        return self._vectors_by_id.get(image_id)

    def count(self) -> int:
        return len(self._image_ids)

    def clear(self) -> None:
        self._index = None
        self._dimension = None
        self._image_ids.clear()
        self._vectors_by_id.clear()

    def search(self, query_vector: list[float], top_k: int = 3) -> list[dict]:
        if self._index is None or self._dimension is None or not self._image_ids:
            return []

        if len(query_vector) != self._dimension:
            raise ValueError("Vectors must have the same length")

        distances, indices = self._index.search(
            np.array([query_vector], dtype="float32"),
            min(top_k, len(self._image_ids)),
        )

        results: list[dict] = []
        for distance, index in zip(distances[0], indices[0]):
            if index < 0:
                continue
            results.append(
                {
                    "image_id": self._image_ids[index],
                    "score": self._distance_to_similarity(float(distance)),
                }
            )

        return results

    def close(self) -> None:
        self.clear()

    def _rebuild_index(self) -> None:
        if self._dimension is None:
            return

        self._index = faiss.IndexFlatL2(self._dimension)
        vectors = [self._vectors_by_id[image_id] for image_id in self._image_ids]
        if vectors:
            self._index.add(np.array(vectors, dtype="float32"))

    def _distance_to_similarity(self, distance: float) -> float:
        return 1.0 / (1.0 + math.sqrt(max(distance, 0.0)))
