from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RagStatus(str, Enum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    OUT_OF_SCOPE = "out_of_scope"
    ERROR = "error"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SafetyStatus(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    REFUSED_DIAGNOSIS = "refused_diagnosis"
    REFUSED_TREATMENT = "refused_treatment"
    REFUSED_EMERGENCY = "refused_emergency"


class Citation(BaseModel):
    chunk_id: str = Field(..., description="Unique source chunk identifier")
    document_id: str = Field(..., description="Source document identifier")
    title: str = Field(..., description="Human-readable title of the source document")
    page_number: Optional[int] = Field(None, description="Page number in the reference document")
    similarity_score: Optional[float] = Field(None, description="Retrieval cosine similarity score")


class RagResponse(BaseModel):
    request_id: str = Field(..., description="Correlation request ID")
    status: RagStatus = Field(..., description="Overall response status")
    answer: Optional[str] = Field(None, description="Grounded answer text, or null if refused/insufficient")
    confidence: Optional[ConfidenceLevel] = Field(None, description="Categorical confidence level")
    safety_status: SafetyStatus = Field(..., description="Medical safety categorization")
    model: str = Field(..., description="The LLM model slug used for generation")
    citations: List[Citation] = Field(default_factory=list, description="Verified citations from retrieved metadata")
