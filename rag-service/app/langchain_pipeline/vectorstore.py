import logging
from typing import Any, Dict, List, Optional
from supabase import Client, create_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseVectorStore:
    def __init__(self, client: Optional[Client] = None):
        if client is not None:
            self.client = client
        else:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )

    def delete_by_document_id(self, document_id: str) -> None:
        """
        Deletes all chunks belonging to a document_id.
        """
        self.client.table("document_chunks").delete().eq("document_id", document_id).execute()

    def delete_stale_chunks(self, document_id: str, keep_chunk_ids: List[str]) -> int:
        """
        Safely deletes chunks for document_id that are NOT in keep_chunk_ids.
        This cleans up obsolete chunks from previous versions without premature deletion.
        """
        if not keep_chunk_ids:
            return 0

        try:
            # Query existing chunk IDs for this document
            response = (
                self.client.table("document_chunks")
                .select("chunk_id")
                .eq("document_id", document_id)
                .execute()
            )
            existing_rows = response.data or []
            existing_ids = {r["chunk_id"] for r in existing_rows}
            stale_ids = list(existing_ids - set(keep_chunk_ids))

            if stale_ids:
                logger.info(f"Cleaning up {len(stale_ids)} stale chunks for document '{document_id}'...")
                # Delete in small batches of 50 to avoid URL/query length limits
                batch_size = 50
                for i in range(0, len(stale_ids), batch_size):
                    batch = stale_ids[i : i + batch_size]
                    self.client.table("document_chunks").delete().in_("chunk_id", batch).execute()
                return len(stale_ids)
            return 0
        except Exception as e:
            logger.warning(f"Error during stale chunk cleanup for document '{document_id}': {e}")
            return 0

    def upsert_chunks(self, rows: List[Dict[str, Any]], batch_size: Optional[int] = None) -> None:
        """
        Upserts chunk rows into document_chunks table using batching.
        """
        if not rows:
            return

        bs = batch_size or settings.INGESTION_BATCH_SIZE or 25
        for i in range(0, len(rows), bs):
            batch = rows[i : i + bs]
            self.client.table("document_chunks").upsert(batch, on_conflict="chunk_id").execute()

    def similarity_search(
        self,
        query_embedding: List[float],
        match_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Executes RPC function match_document_chunks to perform cosine similarity search.
        """
        response = self.client.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
            },
        ).execute()

        return response.data or []
