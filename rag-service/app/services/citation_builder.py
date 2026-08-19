from typing import List, Set
from app.schemas.rag_response import Citation
from app.services.retrieval_service import RetrievedChunk


def build_citations(
    used_chunk_ids: List[str],
    retrieved_chunks: List[RetrievedChunk],
) -> List[Citation]:
    """
    Builds verified Citation objects by taking the intersection of used_chunk_ids
    with the actual retrieved chunks.

    Retrieved chunk metadata is the sole source of truth.
    Any chunk ID referenced by the LLM that was not actually retrieved is dropped.
    The LLM is never trusted for citation metadata.
    """
    retrieved_map = {chunk.chunk_id: chunk for chunk in retrieved_chunks}
    seen_ids: Set[str] = set()
    citations: List[Citation] = []

    for chunk_id in used_chunk_ids:
        chunk_id = chunk_id.strip()
        if chunk_id in retrieved_map and chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            chunk = retrieved_map[chunk_id]
            citations.append(
                Citation(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    page_number=chunk.page_number,
                    similarity_score=round(chunk.similarity, 4),
                )
            )

    return citations
