from unittest.mock import MagicMock
from app.services.generation_service import GenerationService
from app.services.domain_guard import (
    MSG_REFUSAL_EN,
    MSG_REFUSAL_AR,
    MSG_INSUFFICIENT_EN,
    MSG_INSUFFICIENT_AR,
    MSG_GREETING_EN,
    MSG_GREETING_AR,
    MSG_APP_INFO_AR,
)
from app.services.retrieval_service import RetrievalService, RetrievedChunk
from app.langchain_pipeline.llm_chain import LLMGenerationOutput
from app.schemas.rag_response import RagStatus, SafetyStatus


def test_generation_in_scope_answered():
    mock_retrieval = MagicMock(spec=RetrievalService)
    mock_retrieval.retrieve.return_value = [
        RetrievedChunk(
            chunk_id="ada_2024_p1_c1",
            document_id="ada_2024",
            title="ADA Standards of Care 2024",
            page_number=1,
            content="Screening for diabetes should begin at age 35 for all people.",
            similarity=0.925,
        )
    ]
    mock_retrieval.format_context.return_value = "[chunk_id=ada_2024_p1_c1]\nScreening for diabetes should begin at age 35 for all people."

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = LLMGenerationOutput(
        status="answered",
        safety_status="in_scope",
        answer="According to ADA guidelines, universal screening for diabetes begins at age 35.",
        confidence="high",
        used_chunk_ids=["ada_2024_p1_c1"],
    )

    service = GenerationService(
        retrieval_service=mock_retrieval,
        llm_chain=mock_llm,
    )

    response = service.generate_response(
        question="What age should diabetes screening start for asymptomatic adults?",
        conversation_history=[],
        request_id="req-test-1",
    )

    assert response.status == RagStatus.ANSWERED
    assert response.safety_status == SafetyStatus.IN_SCOPE
    assert response.answer is not None
    assert response.confidence == "high"
    assert len(response.citations) == 1
    assert response.citations[0].chunk_id == "ada_2024_p1_c1"


def test_generation_conversational_greeting_en():
    service = GenerationService()

    response = service.generate_response(
        question="Hi",
        conversation_history=[],
        request_id="req-greet-en",
    )

    assert response.status == RagStatus.ANSWERED
    assert response.safety_status == SafetyStatus.IN_SCOPE
    assert response.answer == MSG_GREETING_EN
    assert len(response.citations) == 0


def test_generation_conversational_greeting_ar():
    service = GenerationService()

    response = service.generate_response(
        question="السلام عليكم",
        conversation_history=[],
        request_id="req-greet-ar",
    )

    assert response.status == RagStatus.ANSWERED
    assert response.safety_status == SafetyStatus.IN_SCOPE
    assert response.answer == MSG_GREETING_AR
    assert len(response.citations) == 0


def test_generation_identity_question_ar():
    service = GenerationService()

    response = service.generate_response(
        question="مين انت؟",
        conversation_history=[],
        request_id="req-identity-ar",
    )

    assert response.status == RagStatus.ANSWERED
    assert response.safety_status == SafetyStatus.IN_SCOPE
    assert response.answer == MSG_APP_INFO_AR
    assert len(response.citations) == 0


def test_generation_out_of_scope_treatment_en():
    service = GenerationService()

    response = service.generate_response(
        question="What dose of metformin should I prescribe?",
        conversation_history=[],
        request_id="req-oos-treat-en",
    )

    assert response.status == RagStatus.OUT_OF_SCOPE
    assert response.safety_status == SafetyStatus.REFUSED_TREATMENT
    assert response.answer == MSG_REFUSAL_EN
    assert len(response.citations) == 0


def test_generation_out_of_scope_treatment_ar():
    service = GenerationService()

    response = service.generate_response(
        question="ما هي جرعة الميتفورمين المناسبة للمريض؟",
        conversation_history=[],
        request_id="req-oos-treat-ar",
    )

    assert response.status == RagStatus.OUT_OF_SCOPE
    assert response.safety_status == SafetyStatus.REFUSED_TREATMENT
    assert response.answer == MSG_REFUSAL_AR
    assert len(response.citations) == 0


def test_generation_diagnosis_refusal():
    service = GenerationService()

    response = service.generate_response(
        question="Diagnose this patient with diabetes.",
        conversation_history=[],
        request_id="req-diag",
    )

    assert response.status == RagStatus.OUT_OF_SCOPE
    assert response.safety_status == SafetyStatus.REFUSED_DIAGNOSIS
    assert response.answer == MSG_REFUSAL_EN
    assert len(response.citations) == 0


def test_generation_emergency_refusal():
    service = GenerationService()

    response = service.generate_response(
        question="Patient is unresponsive in emergency, what should I do?",
        conversation_history=[],
        request_id="req-emerg",
    )

    assert response.status == RagStatus.OUT_OF_SCOPE
    assert response.safety_status == SafetyStatus.REFUSED_EMERGENCY
    assert response.answer == MSG_REFUSAL_EN


def test_generation_insufficient_evidence():
    mock_retrieval = MagicMock(spec=RetrievalService)
    mock_retrieval.retrieve.return_value = []

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = LLMGenerationOutput(
        status="insufficient_evidence",
        safety_status="in_scope",
        answer=MSG_INSUFFICIENT_EN,
        confidence=None,
        used_chunk_ids=[],
    )

    service = GenerationService(retrieval_service=mock_retrieval, llm_chain=mock_llm)

    response = service.generate_response(
        question="How does cosmic radiation impact prediabetes screening intervals?",
        conversation_history=[],
        request_id="req-insufficient",
    )

    assert response.status == RagStatus.INSUFFICIENT_EVIDENCE
    assert response.answer == MSG_INSUFFICIENT_EN
    assert len(response.citations) == 0
