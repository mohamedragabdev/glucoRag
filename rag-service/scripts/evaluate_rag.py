import json
import argparse
import sys
import os
import time
from typing import List, Dict, Any

# Ensure app root is on pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.generation_service import GenerationService
from app.schemas.rag_response import RagResponse


def run_evaluation(dataset_path: str, dry_run: bool = False):
    if not os.path.exists(dataset_path):
        print(f"Error: Evaluation dataset not found at {dataset_path}")
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    print("=" * 70)
    print(" MEDICAL RAG SYSTEM — EVALUATION HARNESS")
    print(f" Dataset: {dataset_path} ({len(cases)} test cases)")
    print("=" * 70)

    service = GenerationService()

    total = len(cases)
    passed_status = 0
    passed_safety = 0
    citation_checks = 0
    citation_passed = 0

    results = []

    for idx, case in enumerate(cases, 1):
        case_id = case["id"]
        category = case["category"]
        question = case["question"]
        expected_status = case["expected_status"]
        expected_safety = case["expected_safety_status"]

        print(f"\n[{idx}/{total}] Running Case {case_id} ({category})...")
        print(f"  Question: {question}")

        start_time = time.time()
        try:
            if dry_run:
                # In dry run mode, return simulated response
                res = RagResponse(
                    request_id=f"eval-{idx}",
                    status=expected_status,
                    answer="Sample clinical answer" if expected_status == "answered" else None,
                    confidence="high" if expected_status == "answered" else None,
                    safety_status=expected_safety,
                    model="openai/gpt-4o-mini",
                    citations=[],
                )
            else:
                res = service.generate_response(
                    question=question,
                    conversation_history=[],
                    request_id=f"eval-{case_id}",
                )

            elapsed = time.time() - start_time

            status_match = res.status.value == expected_status
            safety_match = res.safety_status.value == expected_safety

            if status_match:
                passed_status += 1
            if safety_match:
                passed_safety += 1

            # Check citations
            if res.status.value == "answered":
                citation_checks += 1
                if len(res.citations) > 0 and all(c.chunk_id and c.source_title for c in res.citations):
                    citation_passed += 1

            print(f"  Status: {res.status.value} (Expected: {expected_status}) -> {'✓' if status_match else '✗'}")
            print(f"  Safety: {res.safety_status.value} (Expected: {expected_safety}) -> {'✓' if safety_match else '✗'}")
            print(f"  Latency: {elapsed:.2f}s | Citations: {len(res.citations)}")

            results.append({
                "id": case_id,
                "category": category,
                "status_match": status_match,
                "safety_match": safety_match,
                "latency_sec": elapsed,
            })

        except Exception as e:
            print(f"  Execution Error: {str(e)}")
            results.append({
                "id": case_id,
                "category": category,
                "error": str(e),
            })

    print("\n" + "=" * 70)
    print(" EVALUATION SUMMARY REPORT")
    print("=" * 70)
    print(f" Total Cases Evaluated: {total}")
    print(f" Status Matching Accuracy: {passed_status}/{total} ({passed_status/total*100:.1f}%)")
    print(f" Safety Refusal Adherence: {passed_safety}/{total} ({passed_safety/total*100:.1f}%)")
    if citation_checks > 0:
        print(f" Citation Grounding Integrity: {citation_passed}/{citation_checks} ({citation_passed/citation_checks*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Medical RAG Pipeline")
    parser.add_argument("--dataset", type=str, default="../docs/eval_dataset.json", help="Path to evaluation dataset")
    parser.add_argument("--dry-run", action="store_true", help="Run evaluation with simulated mock responses")
    args = parser.parse_args()

    run_evaluation(args.dataset, dry_run=args.dry_run)
