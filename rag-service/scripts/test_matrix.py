import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.generation_service import GenerationService
from app.services.domain_guard import (
    DomainGuard,
    IntentType,
    MSG_REFUSAL_EN,
    MSG_REFUSAL_AR,
    MSG_GREETING_EN,
    MSG_GREETING_AR,
    MSG_APP_INFO_EN,
    MSG_APP_INFO_AR,
)
from app.schemas.query import Turn
from app.schemas.rag_response import RagStatus, SafetyStatus
from app.services.retrieval_service import RetrievalService, RetrievedChunk
from app.langchain_pipeline.llm_chain import LLMGenerationOutput

def run_matrix():
    print("=" * 80)
    print(" GLUCORAG DOMAIN GUARD FULL TEST MATRIX VERIFICATION")
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
    mock_llm.invoke.return_value = LLMGenerationOutput(
        status="answered",
        safety_status="in_scope",
        answer="According to clinical guidelines, universal screening for prediabetes and type 2 diabetes begins at age 35.",
        confidence="high",
        used_chunk_ids=["uspstf_2021_p2_c1", "ada_2024_p5_c2"],
    )

    service = GenerationService(
        retrieval_service=mock_retrieval,
        llm_chain=mock_llm,
    )

    test_matrix = [
        # --- VALID / MUST GO THROUGH ---
        {"id": 1, "group": "VALID", "q": "Hi", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 0, "ans_contains": "Hello! I'm GlucoRAG"},
        {"id": 2, "group": "VALID", "q": "السلام عليكم", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 0, "ans_contains": "أهلاً! أنا GlucoRAG"},
        {"id": 3, "group": "VALID", "q": "What is GlucoRAG?", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 0, "ans_contains": "GlucoRAG is an evidence-grounded"},
        {"id": 4, "group": "VALID", "q": "What is the recommended screening age for type 2 diabetes?", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 2, "ans_contains": "clinical guidelines"},
        {"id": 5, "group": "VALID", "q": "What is the recommended screening age according to the USPSTF?", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 2, "ans_contains": "clinical guidelines"},
        {"id": 6, "group": "VALID", "q": "What tests are used to screen for type 2 diabetes?", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 2, "ans_contains": "clinical guidelines"},
        {"id": 7, "group": "VALID", "q": "How often should adults be screened?", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 2, "ans_contains": "clinical guidelines"},
        {"id": 8, "group": "VALID", "q": "ما هي توصيات USPSTF لفحص السكري من النوع الثاني؟", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 2, "ans_contains": "clinical guidelines"},
        {"id": 9, "group": "VALID", "q": "ما هي الفحوصات المستخدمة للكشف عن السكري من النوع الثاني؟", "history": [], "expect_status": RagStatus.ANSWERED, "expect_safety": SafetyStatus.IN_SCOPE, "expect_citations": 2, "ans_contains": "clinical guidelines"},

        # --- MUST BE REJECTED ---
        {"id": 10, "group": "REJECT", "q": "How do I treat diabetes?", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.REFUSED_TREATMENT, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},
        {"id": 11, "group": "REJECT", "q": "What medication should I take?", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.REFUSED_TREATMENT, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},
        {"id": 12, "group": "REJECT", "q": "What dose of metformin should I use?", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.REFUSED_TREATMENT, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},
        {"id": 13, "group": "REJECT", "q": "How do I treat hypertension?", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.REFUSED_TREATMENT, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},
        {"id": 14, "group": "REJECT", "q": "What is cancer?", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.REFUSED_TREATMENT, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},
        {"id": 15, "group": "REJECT", "q": "Write Python code.", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.OUT_OF_SCOPE, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},
        {"id": 16, "group": "REJECT", "q": "What's the weather?", "history": [], "expect_status": RagStatus.OUT_OF_SCOPE, "expect_safety": SafetyStatus.OUT_OF_SCOPE, "expect_citations": 0, "ans_contains": MSG_REFUSAL_EN},

        # --- IMPORTANT CONTEXT TEST ---
        {
            "id": 17,
            "group": "CONTEXT_TEST",
            "q": "What about people with hypertension?",
            "history": [
                Turn(role="user", content="What is the recommended screening age for T2D?"),
                Turn(role="assistant", content="Screening begins at age 35 for asymptomatic adults according to ADA.")
            ],
            "expect_status": RagStatus.ANSWERED,
            "expect_safety": SafetyStatus.IN_SCOPE,
            "expect_citations": 2,
            "ans_contains": "clinical guidelines"
        },
    ]

    all_passed = True
    for tc in test_matrix:
        res = service.generate_response(
            question=tc["q"],
            conversation_history=tc["history"],
            request_id=f"matrix-{tc['id']}",
        )

        status_ok = res.status == tc["expect_status"]
        safety_ok = res.safety_status == tc["expect_safety"]
        citations_ok = len(res.citations) == tc["expect_citations"]
        answer_ok = tc["ans_contains"] in (res.answer or "")

        passed = status_ok and safety_ok and citations_ok and answer_ok
        if not passed:
            all_passed = False

        status_sym = "PASSED" if passed else "FAILED"
        print(f"[{tc['id']:02d}] {tc['group']} | '{tc['q'][:45]}' -> {status_sym} (status={res.status.value}, safety={res.safety_status.value}, citations={len(res.citations)})")

    print("\n" + "=" * 80)
    if all_passed:
        print(" ALL 17 MATRIX TEST CASES PASSED CLEANLY WITH ZERO REGRESSIONS")
    else:
        print(" SOME TEST CASES FAILED")
    print("=" * 80)

if __name__ == "__main__":
    run_matrix()
