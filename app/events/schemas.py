from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"


class BaseEvent(BaseModel):
    metadata: EventMetadata
    payload: Dict[str, Any]


class ImageSubmittedPayload(BaseModel):
    image_id: str
    image_path: str
    submitted_by: Optional[str] = None


class InferenceCompletedPayload(BaseModel):
    image_id: str
    labels: List[str]
    confidence_scores: List[float]


class AnnotationStoredPayload(BaseModel):
    image_id: str
    annotations: Dict[str, Any]


class EmbeddingCreatedPayload(BaseModel):
    image_id: str
    vector: List[float]
    model_name: str


class QuerySubmittedPayload(BaseModel):
    query_id: str
    query_text: str
    top_k: int = 5


class QueryCompletedPayload(BaseModel):
    query_id: str
    results: List[Dict[str, Any]]


class AnnotationCorrectedPayload(BaseModel):
    image_id: str
    corrected_annotations: Dict[str, Any]
    corrected_by: Optional[str] = None


class SystemErrorPayload(BaseModel):
    failed_event_id: Optional[str] = None
    error_message: str
    topic: Optional[str] = None