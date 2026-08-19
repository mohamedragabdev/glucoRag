import logging

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_internal_secret
from app.schemas.query import QueryRequest
from app.schemas.rag_response import RagResponse
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/rag", tags=["RAG Query"])
logger = logging.getLogger(__name__)


@router.post("/query", response_model=RagResponse, dependencies=[Depends(verify_internal_secret)])
def query_rag(request: QueryRequest):
    try:
        service = GenerationService()
        response = service.generate_response(
            question=request.question,
            conversation_history=request.conversation_history,
            request_id=request.request_id,
        )
        return response
    except Exception:
        logger.exception("RAG query processing failed", extra={"request_id": request.request_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process the RAG query at this time.",
        )
