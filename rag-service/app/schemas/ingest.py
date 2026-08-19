from pydantic import BaseModel, Field
from typing import Optional


class IngestRequest(BaseModel):
    document_path: str = Field(..., description="Path to the PDF document to ingest")
    document_id: str = Field(..., description="Unique deterministic identifier for the document")
    title: str = Field(..., description="Human-readable title of the document")


class IngestResponse(BaseModel):
    document_id: str
    title: str
    chunks_ingested: int
    status: str = "success"
    message: Optional[str] = None
