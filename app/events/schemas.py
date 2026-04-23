from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"


class BaseEvent(BaseModel):
    metadata: EventMetadata
    payload: dict[str, Any]


class ImageSubmittedPayload(BaseModel):
    image_id: str
    image_path: str
    filename: str
    source: str | None = None


class InferenceCompletedPayload(BaseModel):
    image_id: str
    objects: list[dict[str, Any]]
    model_version: str


class AnnotationStoredPayload(BaseModel):
    image_id: str
    document_id: str
    status: str


class EmbeddingCreatedPayload(BaseModel):
    image_id: str
    embedding: list[float]
    model_name: str


class QuerySubmittedPayload(BaseModel):
    query_id: str
    query_text: str
    top_k: int = 5


class QueryCompletedPayload(BaseModel):
    query_id: str
    query_text: str | None = None
    top_k: int | None = None
    results: list[dict[str, Any]]


class AnnotationCorrectedPayload(BaseModel):
    image_id: str
    corrections: list[dict[str, Any]]
    reviewer: str | None = None


class SystemErrorPayload(BaseModel):
    failed_topic: str | None = None
    reason: str

