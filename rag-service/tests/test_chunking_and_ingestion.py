from unittest.mock import MagicMock
from langchain_core.documents import Document
from app.langchain_pipeline.chunking import chunk_documents
from app.services.ingestion_service import IngestionService


def test_chunk_documents_deterministic_ids():
    docs = [
        Document(
            page_content="Screening for type 2 diabetes should be considered in adults of any age with BMI >= 25.",
            metadata={"page_number": 1},
        ),
        Document(
            page_content="For all other people, screening should begin at age 35 years.",
            metadata={"page_number": 2},
        ),
    ]

    chunks = chunk_documents(docs, document_id="ada_guidelines", title="ADA 2024 Guidelines")

    assert len(chunks) == 2
    assert chunks[0].metadata["chunk_id"] == "ada_guidelines_p1_c1"
    assert chunks[0].metadata["document_id"] == "ada_guidelines"
    assert chunks[0].metadata["title"] == "ADA 2024 Guidelines"
    assert chunks[0].metadata["page_number"] == 1

    assert chunks[1].metadata["chunk_id"] == "ada_guidelines_p2_c1"
    assert chunks[1].metadata["document_id"] == "ada_guidelines"
    assert chunks[1].metadata["page_number"] == 2


def test_ingestion_service_pipeline():
    mock_vectorstore = MagicMock()
    mock_vectorstore.delete_stale_chunks.return_value = 0
    mock_embedding_client = MagicMock()
    mock_embedding_client.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]

    service = IngestionService(
        vector_store=mock_vectorstore,
        embedding_client=mock_embedding_client,
    )

    # Mock load_pdf_document directly
    docs = [
        Document(page_content="Page 1 text", metadata={"page_number": 1}),
        Document(page_content="Page 2 text", metadata={"page_number": 2}),
    ]

    import app.services.ingestion_service as ingestion_mod
    orig_loader = ingestion_mod.load_pdf_document
    ingestion_mod.load_pdf_document = lambda path, doc_id, title: docs

    try:
        result = service.ingest_pdf(
            document_path="/dummy/path.pdf",
            document_id="ada_test",
            title="ADA Test Document",
        )

        assert result["status"] == "success"
        assert result["chunks_ingested"] == 2
        assert result["total_batches"] == 1
        # Asserts safe replacement: delete_stale_chunks called after upsert, NOT delete_by_document_id before
        mock_vectorstore.delete_by_document_id.assert_not_called()
        mock_vectorstore.upsert_chunks.assert_called_once()
        mock_vectorstore.delete_stale_chunks.assert_called_once_with(
            document_id="ada_test",
            keep_chunk_ids=["ada_test_p1_c1", "ada_test_p2_c1"],
        )
    finally:
        ingestion_mod.load_pdf_document = orig_loader


def test_ingestion_service_retry_and_recovery():
    mock_vectorstore = MagicMock()
    mock_vectorstore.delete_stale_chunks.return_value = 0

    # Fail on first attempt, succeed on second attempt
    mock_embedding_client = MagicMock()
    mock_embedding_client.embed_documents.side_effect = [
        Exception("StreamReset / Connection reset"),
        [[0.1] * 1536],
    ]

    service = IngestionService(
        vector_store=mock_vectorstore,
        embedding_client=mock_embedding_client,
    )

    docs = [
        Document(page_content="Transient error test page", metadata={"page_number": 1}),
    ]

    import app.services.ingestion_service as ingestion_mod
    orig_loader = ingestion_mod.load_pdf_document
    ingestion_mod.load_pdf_document = lambda path, doc_id, title: docs

    try:
        result = service.ingest_pdf(
            document_path="/dummy/path.pdf",
            document_id="retry_test",
            title="Retry Test",
        )

        assert result["status"] == "success"
        assert result["chunks_ingested"] == 1
        assert mock_embedding_client.embed_documents.call_count == 2
        mock_vectorstore.upsert_chunks.assert_called_once()
    finally:
        ingestion_mod.load_pdf_document = orig_loader
