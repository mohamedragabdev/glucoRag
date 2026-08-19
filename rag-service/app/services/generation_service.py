import logging
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.schemas.query import Turn
from app.schemas.rag_response import (
    RagResponse,
    RagStatus,
    ConfidenceLevel,
    SafetyStatus,
)
from app.services.retrieval_service import RetrievalService, RetrievedChunk
from app.services.citation_builder import build_citations
from app.services.domain_guard import (
    DomainGuard,
    IntentType,
    is_arabic,
    MSG_GREETING_EN,
    MSG_GREETING_AR,
    MSG_APP_INFO_EN,
    MSG_APP_INFO_AR,
    MSG_REFUSAL_EN,
    MSG_REFUSAL_AR,
    MSG_INSUFFICIENT_EN,
    MSG_INSUFFICIENT_AR,
)
from app.langchain_pipeline.llm_chain import (
    get_llm_chain,
    SYSTEM_PROMPT,
    format_history_messages,
    LLMGenerationOutput,
)

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_chain=None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_chain = llm_chain or get_llm_chain()

    def generate_response(
        self,
        question: str,
        conversation_history: List[Turn],
        request_id: str,
    ) -> RagResponse:
        """
        Executes full Domain Guard + 2-Step RAG pipeline:
        1. Pre-retrieval Domain Guard classification
        2. Retrieval from Supabase (for allowed in-scope screening queries)
        3. Context construction & Structured LLM Generation
        4. Citation verification from retrieved metadata
        5. Fail-closed safety validation & bilingual handling
        """
        arabic = is_arabic(question)
        default_refusal = MSG_REFUSAL_AR if arabic else MSG_REFUSAL_EN
        default_insufficient = MSG_INSUFFICIENT_AR if arabic else MSG_INSUFFICIENT_EN

        # Stage 1: Domain Guard Pre-Classification
        intent, precomputed_answer = DomainGuard.classify_intent(question, conversation_history)

        if intent in (IntentType.GREETING, IntentType.APP_INFO):
            logger.info("DomainGuard classified as %s (request_id: %s)", intent.value, request_id)
            return RagResponse(
                request_id=request_id,
                status=RagStatus.ANSWERED,
                answer=precomputed_answer,
                confidence=ConfidenceLevel.HIGH,
                safety_status=SafetyStatus.IN_SCOPE,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        if intent == IntentType.OUT_OF_SCOPE_DIAGNOSIS:
            logger.info("DomainGuard refused diagnosis (request_id: %s)", request_id)
            return RagResponse(
                request_id=request_id,
                status=RagStatus.OUT_OF_SCOPE,
                answer=precomputed_answer or default_refusal,
                confidence=None,
                safety_status=SafetyStatus.REFUSED_DIAGNOSIS,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        if intent == IntentType.OUT_OF_SCOPE_TREATMENT:
            logger.info("DomainGuard refused treatment/medication (request_id: %s)", request_id)
            return RagResponse(
                request_id=request_id,
                status=RagStatus.OUT_OF_SCOPE,
                answer=precomputed_answer or default_refusal,
                confidence=None,
                safety_status=SafetyStatus.REFUSED_TREATMENT,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        if intent == IntentType.OUT_OF_SCOPE_EMERGENCY:
            logger.info("DomainGuard refused emergency (request_id: %s)", request_id)
            return RagResponse(
                request_id=request_id,
                status=RagStatus.OUT_OF_SCOPE,
                answer=precomputed_answer or default_refusal,
                confidence=None,
                safety_status=SafetyStatus.REFUSED_EMERGENCY,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        if intent == IntentType.OUT_OF_SCOPE_GENERAL:
            logger.info("DomainGuard refused general off-topic (request_id: %s)", request_id)
            return RagResponse(
                request_id=request_id,
                status=RagStatus.OUT_OF_SCOPE,
                answer=precomputed_answer or default_refusal,
                confidence=None,
                safety_status=SafetyStatus.OUT_OF_SCOPE,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        # Stage 2: RAG Retrieval from Supabase
        retrieved_chunks: List[RetrievedChunk] = []
        try:
            retrieved_chunks = self.retrieval_service.retrieve(question)
            logger.info("Retrieved %d chunks for query (request_id: %s)", len(retrieved_chunks), request_id)
        except Exception as e:
            logger.warning("Retrieval failed or offline: %s (request_id: %s)", e, request_id)
            retrieved_chunks = []

        # Stage 3: Context formatting
        context_str = self.retrieval_service.format_context(retrieved_chunks)

        # Prepare messages
        system_msg = SystemMessage(content=SYSTEM_PROMPT.format(context=context_str))
        history_msgs = format_history_messages(conversation_history)
        user_msg = HumanMessage(content=question)
        messages = [system_msg] + history_msgs + [user_msg]

        # Stage 4: LLM Generation
        try:
            llm_output: LLMGenerationOutput = self.llm_chain.invoke(messages)
        except Exception as e:
            logger.exception("LLM generation invocation failed: %s (request_id: %s)", e, request_id)
            return RagResponse(
                request_id=request_id,
                status=RagStatus.ERROR,
                answer=None,
                confidence=None,
                safety_status=SafetyStatus.OUT_OF_SCOPE,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        # Map status & safety_status safely
        status = RagStatus(llm_output.status)
        safety_status = SafetyStatus(llm_output.safety_status)

        # 1. Out of scope / Refusals
        if status == RagStatus.OUT_OF_SCOPE or safety_status != SafetyStatus.IN_SCOPE:
            refusal_text = llm_output.answer or default_refusal
            return RagResponse(
                request_id=request_id,
                status=RagStatus.OUT_OF_SCOPE,
                answer=refusal_text,
                confidence=None,
                safety_status=safety_status,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        # 2. Insufficient Evidence
        if status == RagStatus.INSUFFICIENT_EVIDENCE:
            insufficient_text = llm_output.answer or default_insufficient
            return RagResponse(
                request_id=request_id,
                status=RagStatus.INSUFFICIENT_EVIDENCE,
                answer=insufficient_text,
                confidence=None,
                safety_status=SafetyStatus.IN_SCOPE,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        # 3. Answered Case
        citations = build_citations(llm_output.used_chunk_ids, retrieved_chunks)

        # If LLM gave an answer with no chunk citations:
        # Check if it is a conversational greeting/intro that bypassed pre-classification
        is_greeting = any(
            greet in question.strip().lower()
            for greet in ["hi", "hello", "hey", "good morning", "who are you", "what is glucorag", "what can you help", "مين انت", "اهلا", "مرحبا"]
        )

        if not citations and not is_greeting:
            # Substantive medical question without matching citation -> fail closed
            return RagResponse(
                request_id=request_id,
                status=RagStatus.INSUFFICIENT_EVIDENCE,
                answer=default_insufficient,
                confidence=None,
                safety_status=SafetyStatus.IN_SCOPE,
                model=settings.OPENROUTER_MODEL,
                citations=[],
            )

        confidence = ConfidenceLevel(llm_output.confidence) if llm_output.confidence else ConfidenceLevel.HIGH

        return RagResponse(
            request_id=request_id,
            status=RagStatus.ANSWERED,
            answer=llm_output.answer,
            confidence=confidence,
            safety_status=SafetyStatus.IN_SCOPE,
            model=settings.OPENROUTER_MODEL,
            citations=citations,
        )
