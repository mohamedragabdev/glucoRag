# RAG Evaluation Methodology — Medical RAG System (Type 2 Diabetes Screening)

## 1. Overview
This document outlines the evaluation framework, metrics, and procedures for measuring retrieval performance, clinical grounding, citation correctness, and medical safety compliance for the **Type 2 Diabetes Screening Assistant**.

---

## 2. Core Evaluation Metrics

### 2.1 Retrieval Accuracy (Recall@k)
- **Definition:** The fraction of evaluation queries where the ground-truth reference chunk(s) appear in the top-$k$ retrieved results ($k=5$).
- **Target:** $\ge 90\%$ on curated in-scope screening queries.
- **Formula:**
  $$\text{Recall@}k = \frac{\text{Queries with relevant chunk in top } k}{\text{Total in-scope queries}}$$

### 2.2 Citation Correctness & Integrity
- **Definition:** Verifies that:
  1. Every citation attached to an assistant message strictly exists in the retrieved set.
  2. The chunk metadata (title, page number, similarity score) matches the ingested database source of truth.
  3. No citation metadata is fabricated or hallucinated by the LLM.
- **Target:** $100\%$ compliance (enforced deterministically by `citation_builder.py`).

### 2.3 Groundedness & Faithfulness
- **Definition:** Verifies that all clinical claims in generated answers are directly supported by the retrieved context chunks, without unsupported extrinsic medical assertions.
- **Target:** $\ge 95\%$ groundedness.

### 2.4 Medical Safety & Scope Adherence
- **Definition:** Measures accuracy across refusal categories:
  - Diagnosis requests $\rightarrow$ `refused_diagnosis`
  - Treatment/Prescription requests $\rightarrow$ `refused_treatment`
  - Acute emergency/triage requests $\rightarrow$ `refused_emergency`
  - Non-T2D-screening questions $\rightarrow$ `out_of_scope`
  - Low retrieval similarity / unsupported queries $\rightarrow$ `insufficient_evidence`
- **Target:** $100\%$ fail-closed refusal rate on out-of-scope and safety probe queries.

### 2.5 Latency
- **FastAPI internal latency:** Embedding generation + Supabase RPC retrieval + OpenRouter structured generation.
- **End-to-end latency:** Laravel job dispatch to completed DB message persistence.

---

## 3. Evaluation Dataset
The evaluation dataset is located at `docs/eval_dataset.json` and contains:
1. **In-scope screening questions:** ADA universal screening age, asymptomatic risk factor screening, FPG/A1C/OGTT cutoff criteria, repeat screening intervals.
2. **Diagnosis refusal probes:** Individual patient diagnostic inquiries.
3. **Treatment refusal probes:** Drug dosages and therapeutic regimen questions.
4. **Emergency refusal probes:** Acute diabetic ketoacidosis and hyperosmolar triage.
5. **Out-of-scope probes:** Non-diabetes conditions and general medical trivia.
6. **Insufficient evidence probes:** Speculative or unsupported questions.

---

## 4. Running the Automated Evaluation Script

Run the evaluation harness from the `rag-service` directory:

```bash
cd rag-service
source venv/bin/activate
python scripts/evaluate_rag.py --dataset ../docs/eval_dataset.json
```

The script evaluates:
- Status matching (`answered` vs `out_of_scope` vs `insufficient_evidence`)
- Safety status matching (`in_scope`, `refused_diagnosis`, `refused_treatment`, `refused_emergency`, `out_of_scope`)
- Keyword presence in generated answers
- Citation integrity
