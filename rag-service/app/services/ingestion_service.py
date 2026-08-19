import math
import time
import logging
from typing import Dict, Any, List
from app.core.config import settings
from app.langchain_pipeline.loaders import load_pdf_document
from app.langchain_pipeline.chunking import chunk_documents
from app.langchain_pipeline.embeddings import get_embedding_client, validate_embedding_dimension
from app.langchain_pipeline.vectorstore import SupabaseVectorStore

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, vector_store: SupabaseVectorStore = None, embedding_client=None):
        self.vector_store = vector_store or SupabaseVectorStore()
        self.embedding_client = embedding_client or get_embedding_client()

    def _embed_batch_with_retry(
        self,
        texts: List[str],
        batch_idx: int,
        total_batches: int,
        max_retries: int,
        base_delay: float,
    ) -> List[List[float]]:
        """
        Generates embeddings for a single batch of texts with exponential backoff retries.
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  [Batch {batch_idx}/{total_batches}] Embedding {len(texts)} chunks...")
                embeddings = self.embedding_client.embed_documents(texts)

                # Validate embedding dimensions
                if embeddings:
                    validate_embedding_dimension(embeddings[0])

                return embeddings
            except Exception as e:
                if attempt == max_retries:
                    print(f"  [Batch {batch_idx}/{total_batches}] Embedding failed permanently after {max_retries} attempts: {e}")
                    logger.error(f"Embedding batch {batch_idx}/{total_batches} failed after {max_retries} attempts: {e}")
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                print(f"  [Batch {batch_idx}/{total_batches}] Embedding failed (attempt {attempt}/{max_retries}): {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)

        raise RuntimeError(f"Unexpected exit in _embed_batch_with_retry for batch {batch_idx}")

    def _upsert_batch_with_retry(
        self,
        rows: List[Dict[str, Any]],
        batch_idx: int,
        total_batches: int,
        max_retries: int,
        base_delay: float,
    ) -> None:
        """
        Upserts a single batch of chunk rows to Supabase with exponential backoff retries.
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  [Batch {batch_idx}/{total_batches}] Uploading {len(rows)} chunks to Supabase...")
                self.vector_store.upsert_chunks(rows, batch_size=len(rows))
                print(f"  [Batch {batch_idx}/{total_batches}] Batch {batch_idx} succeeded ({len(rows)} chunks)")
                return
            except Exception as e:
                if attempt == max_retries:
                    print(f"  [Batch {batch_idx}/{total_batches}] Upload failed permanently after {max_retries} attempts: {e}")
                    logger.error(f"Upload batch {batch_idx}/{total_batches} failed after {max_retries} attempts: {e}")
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                print(f"  [Batch {batch_idx}/{total_batches}] Upload failed (attempt {attempt}/{max_retries}): {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)

        raise RuntimeError(f"Unexpected exit in _upsert_batch_with_retry for batch {batch_idx}")

    def ingest_pdf(self, document_path: str, document_id: str, title: str) -> Dict[str, Any]:
        """
        Executes a production-safe, batched ingestion pipeline for a PDF document.

        Strategy:
        1. Extract and chunk text page-by-page.
        2. Process chunks in bounded batches (default: 25 chunks).
        3. For each batch: generate embeddings and upsert with exponential backoff retries.
        4. Safe replacement: Existing chunks are NOT deleted prior to insertion.
           Only after all batches succeed, any stale chunks for document_id from older versions
           are safely pruned.
        """
        # 1. Load PDF
        pages = load_pdf_document(document_path, document_id, title)
        if not pages:
            return {
                "document_id": document_id,
                "title": title,
                "chunks_ingested": 0,
                "status": "warning",
                "message": "Document contains no readable text.",
            }

        # 2. Chunk pages
        chunks = chunk_documents(pages, document_id, title)
        total_chunks = len(chunks)
        if total_chunks == 0:
            return {
                "document_id": document_id,
                "title": title,
                "chunks_ingested": 0,
                "status": "warning",
                "message": "Document produced 0 chunks.",
            }

        batch_size = max(1, settings.INGESTION_BATCH_SIZE)
        max_retries = max(1, settings.INGESTION_MAX_RETRIES)
        base_delay = max(0.1, settings.INGESTION_RETRY_DELAY)
        total_batches = math.ceil(total_chunks / batch_size)

        print(f"Ingesting '{title}' ({document_id}): {total_chunks} chunks in {total_batches} batch(es) (batch_size={batch_size})...")

        new_chunk_ids: List[str] = []
        total_ingested = 0

        # 3. Process batch by batch
        for batch_idx in range(1, total_batches + 1):
            start_idx = (batch_idx - 1) * batch_size
            end_idx = min(start_idx + batch_size, total_chunks)
            batch_chunks = chunks[start_idx:end_idx]
            batch_texts = [c.page_content for c in batch_chunks]

            # Generate embeddings for batch
            batch_embeddings = self._embed_batch_with_retry(
                texts=batch_texts,
                batch_idx=batch_idx,
                total_batches=total_batches,
                max_retries=max_retries,
                base_delay=base_delay,
            )

            # Format batch rows
            batch_rows = []
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                c_id = chunk.metadata["chunk_id"]
                new_chunk_ids.append(c_id)
                batch_rows.append({
                    "chunk_id": c_id,
                    "document_id": document_id,
                    "title": title,
                    "page_number": chunk.metadata.get("page_number"),
                    "content": chunk.page_content,
                    "embedding": embedding,
                })

            # Upsert batch rows to Supabase
            self._upsert_batch_with_retry(
                rows=batch_rows,
                batch_idx=batch_idx,
                total_batches=total_batches,
                max_retries=max_retries,
                base_delay=base_delay,
            )

            total_ingested += len(batch_rows)

        # 4. Safe Post-Ingestion Cleanup: prune any stale chunks from older document versions
        stale_deleted = 0
        if hasattr(self.vector_store, "delete_stale_chunks"):
            stale_deleted = self.vector_store.delete_stale_chunks(
                document_id=document_id,
                keep_chunk_ids=new_chunk_ids,
            )

        success_msg = f"Successfully ingested {total_ingested} chunks in {total_batches} batches."
        if stale_deleted > 0:
            success_msg += f" (Cleaned up {stale_deleted} obsolete chunks)."

        print(f"Completed ingestion for '{document_id}': {success_msg}")

        return {
            "document_id": document_id,
            "title": title,
            "chunks_ingested": total_ingested,
            "total_batches": total_batches,
            "status": "success",
            "message": success_msg,
        }
