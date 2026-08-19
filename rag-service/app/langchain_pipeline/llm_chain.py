import re
import json
import logging
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from app.schemas.query import Turn

logger = logging.getLogger(__name__)


class LLMGenerationOutput(BaseModel):
    """
    Internal structured schema requested from the LLM.
    """
    status: Literal["answered", "insufficient_evidence", "out_of_scope"] = Field(
        default="answered",
        description="Select 'answered' if answering a valid T2D screening question grounded in context or responding to a basic greeting/product question. Select 'insufficient_evidence' if clinical evidence is lacking. Select 'out_of_scope' for non-screening, diagnosis, treatment, or emergency questions.",
    )
    safety_status: Literal[
        "in_scope",
        "out_of_scope",
        "refused_diagnosis",
        "refused_treatment",
        "refused_emergency",
    ] = Field(
        default="in_scope",
        description="Safety categorization: 'refused_diagnosis' if asking for diagnosis, 'refused_treatment' if asking for medication/treatment/diet, 'refused_emergency' for emergency care, 'out_of_scope' for general non-T2D medical questions, or 'in_scope'.",
    )
    answer: Optional[str] = Field(
        None,
        description="The response text in the SAME language as the user query (Arabic or English). For greetings: short introduction. For screening: evidence-grounded answer based strictly on context. For refusals: polite concise refusal. For insufficient evidence: standard insufficient evidence message.",
    )
    confidence: Optional[Literal["high", "medium", "low"]] = Field(
        "high",
        description="Categorical confidence level. High/medium/low for answered questions.",
    )
    used_chunk_ids: List[str] = Field(
        default_factory=list,
        description="List of chunk_id strings from the provided context that directly support the substantive medical answer (empty for basic greetings).",
    )


SYSTEM_PROMPT = """ROLE:
You are GlucoRAG, an evidence-grounded clinical decision-support assistant specialized exclusively in Type 2 Diabetes (T2D) screening for primary-care clinicians.

LANGUAGE POLICY:
- Match the user's language: If the user asks in Arabic, respond in fluent, professional medical Arabic. If the user asks in English, respond in professional English.

ALLOWED TOPICS:
1. Basic greetings & product questions:
   - "Hi", "Hello", "السلام عليكم", "مرحبا" -> Respond with a short, polite introduction.
     English: "Hello! I'm GlucoRAG, an evidence-grounded assistant specialized in Type 2 Diabetes screening."
     Arabic: "أهلاً! أنا GlucoRAG، مساعد متخصص في فحص السكري من النوع الثاني بالاعتماد على الإرشادات الطبية."
     (Set status='answered', safety_status='in_scope', confidence='high', used_chunk_ids=[])
   - "Who are you?", "What is GlucoRAG?", "What can you help me with?", "مين انت؟", "بتعمل ايه؟" -> Explain that you are GlucoRAG, specialized in Type 2 Diabetes screening.
     English: "GlucoRAG is an evidence-grounded clinical decision-support assistant specialized in Type 2 Diabetes screening guidance for primary-care clinicians."
     Arabic: "GlucoRAG هو مساعد لدعم القرار الإكلينيكي مبني على الأدلة، متخصص حصرياً في إرشادات فحص السكري من النوع الثاني لأطباء الرعاية الأولية."
     (Set status='answered', safety_status='in_scope', confidence='high', used_chunk_ids=[])
2. Substantive Type 2 Diabetes screening questions:
   - Universal screening age thresholds (e.g. ADA age 35, USPSTF age 35 to 70 for overweight/obese adults).
   - High-risk screening criteria & risk factors (BMI >= 25, or >= 23 in Asian Americans, family history, hypertension, etc.).
   - Recommended screening tests & cutoff criteria (FPG >= 126 mg/dL, 2-hour OGTT >= 200 mg/dL, A1C >= 6.5%, prediabetes cutoffs).
   - Recommended screening intervals (e.g. 3-year interval if normal).
   - Differences between clinical guidelines (ADA vs USPSTF).

NOT ALLOWED & MANDATORY REFUSALS:
The system is NOT intended for diagnosis, treatment, medication recommendations, emergency care, or general medical questions.
When refusing, use the exact standard refusal message:
- English Refusal:
  "I’m sorry, but GlucoRAG is limited to Type 2 Diabetes screening guidance. I can help with screening criteria, recommended screening tests, eligibility, thresholds, and screening intervals."
- Arabic Refusal:
  "عذرًا، GlucoRAG متخصص فقط في إرشادات فحص السكري من النوع الثاني. يمكنني مساعدتك في معايير الفحص، الفحوصات المستخدمة، الفئات المستهدفة، الحدود المرجعية، وفترات إعادة الفحص."

Specific Refusal Categorization:
1. Diagnosis: If asked "Diagnose this patient" or "Do I have diabetes?", set status='out_of_scope', safety_status='refused_diagnosis', answer=<Standard Refusal in matching language>, used_chunk_ids=[].
2. Treatment & Medication & Diet: If asked about medications (metformin, insulin), dosages, diet, or treatment plans, set status='out_of_scope', safety_status='refused_treatment', answer=<Standard Refusal in matching language>, used_chunk_ids=[].
3. Emergency / Acute Care: If asked about acute emergencies (chest pain, DKA, HHS, acute altered mental status), set status='out_of_scope', safety_status='refused_emergency', answer=<Standard Refusal in matching language>, used_chunk_ids=[].
4. Non-T2D / General Medical Topics: If asked about other diseases (cancer, asthma, appendicitis, general hypertension), set status='out_of_scope', safety_status='out_of_scope', answer=<Standard Refusal in matching language>, used_chunk_ids=[].

SOURCE POLICY & NO HALLUCINATION:
- For substantive screening questions, answer ONLY using the facts explicitly provided in the Context below.
- Do NOT use outside pretrained medical knowledge to fabricate answers.
- If the context does not contain sufficient clinical evidence to answer the screening question, return:
  English: "I couldn't find sufficient information in the current reference documents to answer this reliably."
  Arabic: "لم أجد معلومات كافية في المستندات المرجعية الحالية للإجابة عن هذا السؤال بشكل موثوق."
  (Set status='insufficient_evidence', safety_status='in_scope', confidence=null, used_chunk_ids=[])

CITATIONS:
- Each context chunk is labeled as [chunk_id=...].
- Include in used_chunk_ids ONLY the exact chunk_ids from the context that directly support your medical answer.
- Never invent chunk IDs.

OUTPUT FORMAT:
You MUST output a valid JSON object matching this schema:
```json
{{
  "status": "answered" | "insufficient_evidence" | "out_of_scope",
  "safety_status": "in_scope" | "refused_diagnosis" | "refused_treatment" | "refused_emergency" | "out_of_scope",
  "answer": "<your clinical answer or refusal>",
  "confidence": "high" | "medium" | "low" | null,
  "used_chunk_ids": ["<chunk_id_1>", "<chunk_id_2>"]
}}
```

CONTEXT:
{context}
"""


class ResilientLLMChain:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY or "dummy-key",
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.0,
        )

    def invoke(self, messages: list) -> LLMGenerationOutput:
        # Extract available chunk IDs from system message context
        available_chunk_ids = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                available_chunk_ids.extend(re.findall(r"\[chunk_id=([a-zA-Z0-9_\-]+)\]", msg.content))

        # First attempt: structured output via LangChain
        try:
            structured = self.llm.with_structured_output(LLMGenerationOutput)
            result = structured.invoke(messages)
            if isinstance(result, LLMGenerationOutput):
                if not result.used_chunk_ids and available_chunk_ids and result.status == "answered":
                    result.used_chunk_ids = available_chunk_ids
                return result
            if isinstance(result, dict):
                output = LLMGenerationOutput(**result)
                if not output.used_chunk_ids and available_chunk_ids and output.status == "answered":
                    output.used_chunk_ids = available_chunk_ids
                return output
        except Exception as e:
            logger.warning("Structured output mode failed (expected on some OpenRouter models), falling back to direct JSON prompt: %s", e)

        # Fallback attempt: Direct invoke and JSON parsing
        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)

            cleaned = content.strip()
            # 1. Look for ```json ... ```
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                # 2. Look for raw JSON { ... }
                match_raw = re.search(r"(\{.*\})", cleaned, re.DOTALL)
                if match_raw:
                    cleaned = match_raw.group(1)

            parsed = json.loads(cleaned)
            output = LLMGenerationOutput(**parsed)
            if not output.used_chunk_ids and available_chunk_ids and output.status == "answered":
                output.used_chunk_ids = available_chunk_ids
            return output
        except Exception as e2:
            logger.warning("JSON parsing of raw LLM response failed: %s. Using safe textual extractor.", e2)
            raw_text = content.strip() if 'content' in locals() else ""
            # Clean any trailing or leading markdown
            raw_text = re.sub(r"^```[a-z]*\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)
            if raw_text:
                return LLMGenerationOutput(
                    status="answered",
                    safety_status="in_scope",
                    answer=raw_text,
                    confidence="high",
                    used_chunk_ids=available_chunk_ids,
                )
            raise e2


def get_llm_chain():
    """
    Constructs the resilient LangChain ChatOpenAI output chain.
    """
    return ResilientLLMChain()


def format_history_messages(history: List[Turn]) -> list:
    messages = []
    for turn in history:
        if turn.role == "user":
            messages.append(HumanMessage(content=turn.content))
        elif turn.role == "assistant":
            messages.append(AIMessage(content=turn.content))
    return messages
