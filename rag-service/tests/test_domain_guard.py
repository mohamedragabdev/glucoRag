import pytest

from app.services.domain_guard import DomainGuard, IntentType


@pytest.mark.parametrize(
    ("question", "expected_intent"),
    [
        ("How do I treat diabetes?", IntentType.OUT_OF_SCOPE_TREATMENT),
        ("What medication should I take?", IntentType.OUT_OF_SCOPE_TREATMENT),
        ("Diagnose my symptoms.", IntentType.OUT_OF_SCOPE_DIAGNOSIS),
        ("What emergency treatment should I use?", IntentType.OUT_OF_SCOPE_EMERGENCY),
        ("What antibiotic should I take?", IntentType.OUT_OF_SCOPE_TREATMENT),
        ("What cancer treatment should I use?", IntentType.OUT_OF_SCOPE_TREATMENT),
    ],
)
def test_domain_guard_refuses_unsupported_medical_requests(question, expected_intent):
    intent, response = DomainGuard.classify_intent(question)

    assert intent == expected_intent
    assert response is not None


def test_domain_guard_allows_screening_questions_to_reach_grounded_rag():
    intent, response = DomainGuard.classify_intent(
        "What tests are used for Type 2 diabetes screening?"
    )

    assert intent in (IntentType.UNKNOWN, IntentType.IN_SCOPE_SCREENING)
    assert response is None
