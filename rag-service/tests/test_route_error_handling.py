from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes_ingest import ingest_document
from app.api.routes_query import query_rag
from app.schemas.ingest import IngestRequest
from app.schemas.query import QueryRequest


def test_query_route_hides_internal_error_details():
    request = QueryRequest(question="What tests are used for screening?", request_id="req-1")

    with patch("app.api.routes_query.GenerationService") as service:
        service.return_value.generate_response.side_effect = RuntimeError("provider token leaked")
        try:
            query_rag(request)
            raise AssertionError("Expected HTTPException")
        except HTTPException as exception:
            assert exception.status_code == 500
            assert exception.detail == "Unable to process the RAG query at this time."
            assert "token" not in exception.detail


def test_ingest_route_hides_internal_error_details():
    request = IngestRequest(document_path="/missing.pdf", document_id="doc-1", title="Document")

    with patch("app.api.routes_ingest.IngestionService") as service:
        service.return_value.ingest_pdf.side_effect = RuntimeError("database credential leaked")
        try:
            ingest_document(request)
            raise AssertionError("Expected HTTPException")
        except HTTPException as exception:
            assert exception.status_code == 500
            assert exception.detail == "Unable to ingest the document at this time."
            assert "credential" not in exception.detail
