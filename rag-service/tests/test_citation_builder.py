from app.services.citation_builder import build_citations
from app.services.retrieval_service import RetrievedChunk


def test_citation_builder_matches_retrieved_chunks():
    retrieved = [
        RetrievedChunk(
            chunk_id="ada_p1_c1",
            document_id="ada_2024",
            title="ADA Standards 2024",
            page_number=1,
            content="Screening starts at age 35.",
            similarity=0.95123,
        ),
        RetrievedChunk(
            chunk_id="ada_p2_c1",
            document_id="ada_2024",
            title="ADA Standards 2024",
            page_number=2,
            content="Repeat every 3 years if normal.",
            similarity=0.88456,
        ),
    ]

    used_ids = ["ada_p1_c1", "hallucinated_chunk_id", "ada_p2_c1"]

    citations = build_citations(used_ids, retrieved)

    # Hallucinated chunk should be completely dropped
    assert len(citations) == 2
    assert citations[0].chunk_id == "ada_p1_c1"
    assert citations[0].title == "ADA Standards 2024"
    assert citations[0].page_number == 1
    assert citations[0].similarity_score == 0.9512

    assert citations[1].chunk_id == "ada_p2_c1"
    assert citations[1].title == "ADA Standards 2024"
    assert citations[1].page_number == 2
    assert citations[1].similarity_score == 0.8846


def test_citation_builder_deduplicates():
    retrieved = [
        RetrievedChunk(
            chunk_id="ada_p1_c1",
            document_id="ada_2024",
            title="ADA Standards 2024",
            page_number=1,
            content="Screening content",
            similarity=0.91,
        )
    ]

    used_ids = ["ada_p1_c1", "ada_p1_c1", "ada_p1_c1"]
    citations = build_citations(used_ids, retrieved)

    assert len(citations) == 1
