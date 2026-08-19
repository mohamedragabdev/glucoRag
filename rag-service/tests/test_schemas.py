import pytest
from pydantic import ValidationError
from app.schemas.query import QueryRequest, Turn
from app.schemas.ingest import IngestRequest, IngestResponse
from app.schemas.rag_response import RagResponse, RagStatus, ConfidenceLevel, SafetyStatus, Citation


def test_query_request_valid():
    req = QueryRequest(
        question="What is the recommended age for diabetes screening in asymptomatic adults?",
        conversation_history=[
            Turn(role="user", content="Hi"),
            Turn(role="assistant", content="Hello"),
        ],
        request_id="req-123",
    )
    assert req.question.startswith("What is the")
    assert len(req.conversation_history) == 2


def test_query_request_rejects_empty_question():
    with pytest.raises(ValidationError):
        QueryRequest(
            question="",
            conversation_history=[],
            request_id="req-123",
        )


def test_rag_response_valid():
    res = RagResponse(
        request_id="req-123",
        status=RagStatus.ANSWERED,
        answer="ADA recommends screening at age 35.",
        confidence=ConfidenceLevel.HIGH,
        safety_status=SafetyStatus.IN_SCOPE,
        model="openai/gpt-4o-mini",
        citations=[
            Citation(
                chunk_id="doc1_p1_c1",
                document_id="doc1",
                title="ADA Guidelines",
                page_number=1,
                similarity_score=0.92,
            )
        ],
    )
    assert res.status == "answered"
    assert res.confidence == "high"
    assert len(res.citations) == 1
