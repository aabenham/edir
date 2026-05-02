from pymongo import MongoClient


class MongoDocumentStore:
    def __init__(
        self,
        mongo_uri: str,
        database_name: str,
        collection_name: str,
        client: MongoClient | None = None,
    ) -> None:
        self._client = client or MongoClient(mongo_uri)
        self._collection = self._client[database_name][collection_name]
        self._collection.create_index("image_id", unique=True)

    def save(self, image_id: str, document: dict) -> None:
        payload = dict(document)
        payload["image_id"] = image_id
        self._collection.replace_one({"image_id": image_id}, payload, upsert=True)

    def get(self, image_id: str) -> dict | None:
        document = self._collection.find_one({"image_id": image_id}, {"_id": 0})
        return dict(document) if document is not None else None

    def all(self) -> dict[str, dict]:
        return {
            document["image_id"]: document
            for document in self._collection.find({}, {"_id": 0})
        }

    def count(self) -> int:
        return self._collection.count_documents({})

    def clear(self) -> None:
        self._collection.delete_many({})

    def close(self) -> None:
        self._client.close()
