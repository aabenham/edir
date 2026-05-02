# Event-Driven Image Annotation and Retrieval System

This project is a Python-based event-driven image annotation and retrieval system built for a software engineering assignment focused on modular design, pub-sub messaging, document-style storage, vector search, and testability.

The system simulates an image-processing pipeline:

1. an image is submitted
2. simulated inference produces object annotations
3. annotations are stored as a document
4. an embedding is generated and indexed
5. a natural-language or image-based query retrieves matching images

The project uses a small filtered COCO subset for realistic image and annotation data, while keeping inference deterministic by converting the dataset into a local JSON format.

## Architecture

Main event flow:

1. `image.submitted`
2. `inference.completed`
3. `annotation.stored`
4. `embedding.created`
5. `query.submitted`
6. `query.completed`

Core services:

- `app/services/image_service.py`
  Publishes image submission events after validating the file exists.
- `app/services/inference_service.py`
  Simulates inference by loading precomputed annotations from local JSON.
- `app/services/document_service.py`
  Stores annotation documents for each image.
- `app/services/embedding_service.py`
  Generates mock embeddings from stored documents and writes them to the vector store.
- `app/services/query_service.py`
  Converts natural-language queries into mock query vectors and returns top-k matches.

Infrastructure:

- `app/broker/in_memory_broker.py`
  Fast, synchronous broker used in tests and simple local runs.
- `app/broker/redis_broker.py`
  Redis-backed broker for local or hosted Redis deployments.
- `app/storage/document_store.py`
  In-memory document store.
- `app/storage/mongo_document_store.py`
  MongoDB-backed document store for local or hosted MongoDB deployments.
- `app/storage/vector_store.py`
  In-memory vector store with cosine similarity search.
- `app/storage/faiss_vector_store.py`
  FAISS-backed vector store for nearest-neighbor search over synthetic embeddings.
- `app/storage/processed_event_store.py`
  Tracks processed event IDs for idempotency.

## Project Goals

This project is designed to demonstrate:

- event-driven service boundaries
- pub-sub messaging
- idempotent event handling
- fault-oriented testing
- document-style annotation storage
- vector-based image retrieval
- cloud-configurable service integrations

The project intentionally does not train models or implement advanced ANN search. The focus is on architecture and system integration.

## Repository Layout

Key paths:

- `app/`
  Application services, broker implementations, storage, events, and CLI logic
- `scripts/`
  Utility scripts for dataset preparation, demo seeding, and running services
- `tests/`
  Unit and integration tests
- `data/images/`
  Local image subset used for uploads
- `data/annotations/simulated_annotations.json`
  Converted annotation data consumed by `InferenceService`
- `data/annotations/subset_manifest.json`
  Metadata describing the selected COCO subset

## Setup

Create and activate a virtual environment:

```bash
cd edir
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The project supports both local and cloud-style backends through environment variables.

### Broker configuration

- `APP_BROKER=inmemory`
  Use the in-memory broker for tests and quick local runs.
- `APP_BROKER=redis`
  Use Redis pub-sub.

Redis connection options:

- `REDIS_URL`
  Full hosted Redis connection string. If set, it takes precedence over host/port/db.
- `REDIS_HOST`
  Redis host for local or self-managed Redis.
- `REDIS_PORT`
  Redis port.
- `REDIS_DB`
  Redis database number.

### Document store configuration

- `APP_DOCUMENT_STORE=inmemory`
  Use the in-memory document store.
- `APP_DOCUMENT_STORE=mongodb`
  Use MongoDB as the document store.

MongoDB connection options:

- `MONGO_URI`
  MongoDB connection string.
- `MONGO_DATABASE`
  Database name.
- `MONGO_COLLECTION`
  Collection name for annotation documents.

### Vector store configuration

- `APP_VECTOR_STORE=inmemory`
  Use the in-memory vector store.
- `APP_VECTOR_STORE=faiss`
  Use a FAISS-backed vector store.

## Running Tests and Lint

Run the full test suite:

```bash
pytest -q
```

Run lint:

```bash
ruff check .
```

At the time of final verification:

- `48` tests pass
- `ruff check .` passes

## Dataset Preparation

The project uses a constrained COCO-based workflow:

- download COCO 2017 annotations and one image split
- filter to selected classes
- limit to about 30 images
- convert annotations into a local deterministic JSON format

Prepare the dataset:

```bash
python3 scripts/prepare_coco_subset.py --split val --classes cat dog person --limit 30
```

Verify generated files:

```bash
ls data/images | head
ls data/annotations
```

Expected outputs include:

- `data/images/...`
- `data/annotations/simulated_annotations.json`
- `data/annotations/subset_manifest.json`

If you want a tiny placeholder dataset first, you can run:

```bash
python3 scripts/seed_demo.py
```

## CLI Usage

Show configured paths:

```bash
python3 -m app.cli.commands paths
```

Upload an image:

```bash
python3 -m app.cli.commands upload data/images/000000023272.jpg
```

Run a query:

```bash
python3 -m app.cli.commands query "cat" --top-k 3
```

Run an image-to-image query:

```bash
python3 -m app.cli.commands query-image data/images/000000023272.jpg --top-k 3
```

## Embedding Simulation

The project uses synthetic coordinate embeddings to simulate semantic similarity.

Example label centers:

- `cat` -> Boston
- `dog` -> New York
- `person` -> Chicago
- `car` -> Los Angeles
- `truck` -> Houston

Each image embedding is a 2D coordinate generated from its detected object labels. This matches the project’s goal of simulating embeddings without training a model.

## In-Memory Demo

The in-memory broker is useful for quick local verification and tests.

One-process end-to-end verification:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from app.main import build_application

app = build_application().start()
image_name = sorted(Path("data/images").iterdir())[0]

submitted = app.submit_image(str(image_name))
result = app.submit_query("cat", top_k=3)

print(json.dumps({
    "uploaded": image_name.name,
    "submitted_type": submitted["metadata"]["event_type"],
    "document_exists": app.document_store.get(image_name.stem) is not None,
    "vector_exists": app.vector_store.get(image_name.stem) is not None,
    "query_type": result["metadata"]["event_type"],
    "results": result["payload"]["results"],
}, indent=2))

app.close()
PY
```

Expected behavior:

- image submission succeeds
- annotation document is stored
- embedding is created
- query returns a `query.completed` payload with results

## Redis Demo

This project supports a Redis-backed local demo and can also be configured for hosted Redis by setting `REDIS_URL`.

Start Redis:

```bash
brew services start redis
redis-cli ping
```

Expected response:

```bash
PONG
```

### Terminal 1: start the workers

```bash
cd edir
source .venv/bin/activate
APP_BROKER=redis python3 scripts/run_services.py --broker redis
```

Expected output:

```text
Broker: redis
Annotations: <project-root>/data/annotations/simulated_annotations.json
Redis-backed service listeners are running.
```

### Terminal 2: upload and query

```bash
cd edir
source .venv/bin/activate
APP_BROKER=redis python3 -m app.cli.commands upload data/images/000000023272.jpg
APP_BROKER=redis python3 -m app.cli.commands query "cat" --top-k 3
APP_BROKER=redis python3 -m app.cli.commands query-image data/images/000000023272.jpg --top-k 3
```

Expected behavior:

- `upload` prints an `image.submitted` event
- `query` prints a `query.completed` event
- `query-image` prints an `image.query_completed` event
- the returned results include the uploaded image with a similarity score

Example result:

```json
{
  "metadata": {
    "event_type": "query.completed",
    "source": "query_service"
  },
  "payload": {
    "query_text": "cat",
    "top_k": 3,
    "results": [
      {
        "image_id": "000000023272",
        "score": 0.9525793444156805
      }
    ]
  }
}
```

## Testing Guarantees

The tests cover several system guarantees:

- duplicate events do not create duplicate state
- malformed events do not crash the system
- delayed delivery can still be processed later
- subscriber downtime can be handled with replay
- end-to-end query flow works

## Notes

- The project supports both `inmemory` and `redis` broker modes.
- The document store supports both `inmemory` and `mongodb` backends.
- The vector store supports both `inmemory` and `faiss` backends.
- The Redis path can be used locally or pointed at a hosted Redis deployment.
- The MongoDB document store can be pointed at a local instance or a hosted MongoDB deployment.
- The COCO subset is intentionally capped to keep the project small and deterministic.
- Generated local data is not required to be committed if the scripts can reproduce it.
