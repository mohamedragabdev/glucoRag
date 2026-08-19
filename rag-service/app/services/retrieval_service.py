from typing import List, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.langchain_pipeline.embeddings import get_embedding_client, validate_embedding_dimension
from app.langchain_pipeline.vectorstore import SupabaseVectorStore


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    page_number: Optional[int] = None
    content: str
    similarity: float


class RetrievalService:
    def __init__(self, vector_store: SupabaseVectorStore = None, embedding_client=None):
        self.vector_store = vector_store or SupabaseVectorStore()
        self.embedding_client = embedding_client or get_embedding_client()

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        """
        Embeds the query and performs vector similarity search against Supabase.
        Returns top-k RetrievedChunk objects sorted by similarity.
        """
        k = top_k or settings.TOP_K

        query_embedding = self.embedding_client.embed_query(query)
        validate_embedding_dimension(query_embedding)

        results = self.vector_store.similarity_search(query_embedding, match_count=k)

        chunks = []
        for row in results:
            chunk = RetrievedChunk(
                chunk_id=str(row["chunk_id"]),
                document_id=str(row["document_id"]),
                title=str(row["title"]),
                page_number=row.get("page_number"),
                content=str(row["content"]),
                similarity=float(row.get("similarity", 0.0)),
            )
            chunks.append(chunk)

        # Sort descending by similarity
        chunks.sort(key=lambda x: x.similarity, reverse=True)
        return chunks

    @staticmethod
    def format_context(chunks: List[RetrievedChunk]) -> str:
        """
        Formats retrieved chunks into a standardized context string for the LLM.
        Each chunk is labeled with [chunk_id={id}].
        """
        if not chunks:
            return ""

        context_blocks = []
        for chunk in chunks:
            block = f"[chunk_id={chunk.chunk_id}]\n{chunk.content.strip()}"
            context_blocks.append(block)

        return "\n\n".join(context_blocks)
