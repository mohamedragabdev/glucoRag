from typing import List, Literal
from pydantic import BaseModel, Field


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Clinician question")
    conversation_history: List[Turn] = Field(default_factory=list, description="Prior conversation turns")
    request_id: str = Field(..., description="Unique request ID for correlation")
