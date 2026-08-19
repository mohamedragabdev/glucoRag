import os
import sys
import json
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.generation_service import GenerationService
from app.services.domain_guard import (
    MSG_REFUSAL_EN,
    MSG_REFUSAL_AR,
    MSG_GREETING_EN,
    MSG_GREETING_AR,
    MSG_APP_INFO_EN,
    MSG_APP_INFO_AR,
    MSG_INSUFFICIENT_EN,
    MSG_INSUFFICIENT_AR,
)
from app.services.retrieval_service import RetrievalService, RetrievedChunk
from app.langchain_pipeline.llm_chain import LLMGenerationOutput
from app.schemas.rag_response import RagStatus, SafetyStatus

def run_test_suite():
    print("=" * 80)
    print(" GLUCORAG STRICT DOMAIN & BILINGUAL VERIFICATION SUITE")
    print("=" * 80)

    # 1. Mock Retrieval Service with realistic screening chunks
    mock_retrieval = MagicMock(spec=RetrievalService)
    screening_chunks = [
        RetrievedChunk(
            chunk_id="uspstf_2021_p2_c1",
            document_id="uspstf_2021",
            title="USPSTF Screening for Prediabetes and Type 2 Diabetes in Adults",
            page_number=2,
            content="The USPSTF recommends screening for prediabetes and type 2 diabetes in adults aged 35 to 70 years who are overweight or obese.",
            similarity=0.912,
        ),
        RetrievedChunk(
            chunk_id="ada_2024_p5_c2",
            document_id="ada_2024",
            title="ADA Standards of Care in Diabetes 2024",
            page_number=5,
            content="Screening for diabetes using fasting plasma glucose (FPG >= 126 mg/dL), 2-hour 75-g OGTT (>= 200 mg/dL), or A1C (>= 6.5%) is recommended. For all asymptomatic adults, screening should begin at age 35 years.",
            similarity=0.887,
        ),
    ]
    mock_retrieval.retrieve.return_value = screening_chunks
    mock_retrieval.format_context.return_value = "\n\n".join([f"[chunk_id={c.chunk_id}]\n{c.content}" for c in screening_chunks])

    mock_llm = MagicMock()
    service = GenerationService(
        retrieval_service=mock_retrieval,
        llm_chain=mock_llm,
    )

    test_cases = [
        {
            "id": 1,
            "category": "ENGLISH GREETING",
            "prompt": "hi",
            "mock_output": None,
            "expected_status": RagStatus.ANSWERED,
            "expected_safety": SafetyStatus.IN_SCOPE,
            "expected_answer": MSG_GREETING_EN,
            "expected_citations_count": 0,
        },
        {
            "id": 2,
            "category": "ARABIC GREETING",
            "prompt": "السلام عليكم",
            "mock_output": None,
            "expected_status": RagStatus.ANSWERED,
            "expected_safety": SafetyStatus.IN_SCOPE,
            "expected_answer": MSG_GREETING_AR,
            "expected_citations_count": 0,
        },
        {
            "id": 3,
            "category": "ARABIC INFORMAL GREETING",
            "prompt": "ازيك",
            "mock_output": None,
            "expected_status": RagStatus.ANSWERED,
            "expected_safety": SafetyStatus.IN_SCOPE,
            "expected_answer": MSG_GREETING_AR,
            "expected_citations_count": 0,
        },
        {
            "id": 4,
            "category": "ENGLISH PRODUCT IDENTITY",
            "prompt": "What is GlucoRAG?",
            "mock_output": None,
            "expected_status": RagStatus.ANSWERED,
            "expected_safety": SafetyStatus.IN_SCOPE,
            "expected_answer": MSG_APP_INFO_EN,
            "expected_citations_count": 0,
        },
        {
            "id": 5,
            "category": "ARABIC PRODUCT IDENTITY",
            "prompt": "مين انت",
            "mock_output": None,
            "expected_status": RagStatus.ANSWERED,
            "expected_safety": SafetyStatus.IN_SCOPE,
            "expected_answer": MSG_APP_INFO_AR,
            "expected_citations_count": 0,
        },
        {
            "id": 6,
            "category": "OUT-OF-SCOPE ENGLISH MEDICATION",
            "prompt": "What medication should I take for diabetes?",
            "mock_output": None,
            "expected_status": RagStatus.OUT_OF_SCOPE,
            "expected_safety": SafetyStatus.REFUSED_TREATMENT,
            "expected_answer": MSG_REFUSAL_EN,
            "expected_citations_count": 0,
        },
        {
            "id": 7,
            "category": "OUT-OF-SCOPE ARABIC TREATMENT",
            "prompt": "كيف يتم علاج مرض السكر وما هي جرعة الميتفورمين؟",
            "mock_output": None,
            "expected_status": RagStatus.OUT_OF_SCOPE,
            "expected_safety": SafetyStatus.REFUSED_TREATMENT,
            "expected_answer": MSG_REFUSAL_AR,
            "expected_citations_count": 0,
        },
        {
            "id": 8,
            "category": "OUT-OF-SCOPE ENGLISH DIAGNOSIS",
            "prompt": "Diagnose this patient with diabetes.",
            "mock_output": None,
            "expected_status": RagStatus.OUT_OF_SCOPE,
            "expected_safety": SafetyStatus.REFUSED_DIAGNOSIS,
            "expected_answer": MSG_REFUSAL_EN,
            "expected_citations_count": 0,
        },
        {
            "id": 9,
            "category": "OUT-OF-SCOPE ARABIC DIAGNOSIS",
            "prompt": "هل تقدر تشخص حالة هذا المريض؟",
            "mock_output": None,
            "expected_status": RagStatus.OUT_OF_SCOPE,
            "expected_safety": SafetyStatus.REFUSED_DIAGNOSIS,
            "expected_answer": MSG_REFUSAL_AR,
            "expected_citations_count": 0,
        },
        {
            "id": 10,
            "category": "OUT-OF-SCOPE GENERAL MEDICAL",
            "prompt": "What are the symptoms of cancer?",
            "mock_output": None,
            "expected_status": RagStatus.OUT_OF_SCOPE,
            "expected_safety": SafetyStatus.OUT_OF_SCOPE,
            "expected_answer": MSG_REFUSAL_EN,
            "expected_citations_count": 0,
        },
        {
            "id": 11,
            "category": "IN-SCOPE SCREENING AGE (RAG PIPELINE)",
            "prompt": "What age should adults be screened for type 2 diabetes?",
            "mock_output": LLMGenerationOutput(
                status="answered",
                safety_status="in_scope",
                answer="According to ADA and USPSTF guidelines, universal screening for prediabetes and type 2 diabetes is recommended starting at age 35 for all asymptomatic adults.",
                confidence="high",
                used_chunk_ids=["uspstf_2021_p2_c1", "ada_2024_p5_c2"],
            ),
            "expected_status": RagStatus.ANSWERED,
            "expected_safety": SafetyStatus.IN_SCOPE,
            "expected_answer": "According to ADA and USPSTF guidelines",
            "expected_citations_count": 2,
        },
    ]

    all_passed = True

    for tc in test_cases:
        if tc["mock_output"]:
            mock_llm.invoke.return_value = tc["mock_output"]
        res = service.generate_response(
            question=tc["prompt"],
            conversation_history=[],
            request_id=f"test-{tc['id']}",
        )

        status_ok = res.status == tc["expected_status"]
        safety_ok = res.safety_status == tc["expected_safety"]
        citations_ok = len(res.citations) == tc["expected_citations_count"]
        answer_ok = tc["expected_answer"] in (res.answer or "")

        passed = status_ok and safety_ok and citations_ok and answer_ok
        if not passed:
            all_passed = False

        status_sym = "PASSED" if passed else "FAILED"
        print(f"\n[Test {tc['id']:02d}] {tc['category']} ({status_sym})")
        print(f"  Prompt: '{tc['prompt']}'")
        print(f"  Status: {res.status.value} | Safety: {res.safety_status.value}")
        print(f"  Answer: {res.answer}")
        print(f"  Citations: {len(res.citations)}")

    print("\n" + "=" * 80)
    if all_passed:
        print(" ALL BILINGUAL & DOMAIN GUARD TEST CASES PASSED WITH 100% ACCURACY")
    else:
        print(" SOME TEST CASES FAILED")
    print("=" * 80)


if __name__ == "__main__":
    run_test_suite()
