-- Match Document Chunks Function for Cosine Similarity Search
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    chunk_id TEXT,
    document_id TEXT,
    title TEXT,
    page_number INT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        chunk_id,
        document_id,
        title,
        page_number,
        content,
        1 - (embedding <=> query_embedding) AS similarity
    FROM document_chunks
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
