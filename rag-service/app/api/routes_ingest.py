import logging

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_internal_secret
from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/rag", tags=["RAG Ingest"])
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse, dependencies=[Depends(verify_internal_secret)])
def ingest_document(request: IngestRequest):
    try:
        service = IngestionService()
        result = service.ingest_pdf(
            document_path=request.document_path,
            document_id=request.document_id,
            title=request.title,
        )
        return IngestResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.exception("RAG document ingestion failed", extra={"document_id": request.document_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to ingest the document at this time.",
        )
