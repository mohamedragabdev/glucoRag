from typing import List
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


def get_embedding_client() -> OpenAIEmbeddings:
    """
    Returns an OpenAIEmbeddings instance configured according to environment settings.
    """
    # OpenRouter or OpenAI embedding endpoint
    api_key = settings.OPENROUTER_API_KEY or "dummy-key"
    base_url = "https://openrouter.ai/api/v1"

    # If user provided a specific OpenAI key or standard endpoint
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=api_key,
        openai_api_base=base_url,
        check_embedding_ctx_length=False,
    )


def validate_embedding_dimension(embedding: List[float]) -> bool:
    """
    Validates that the generated embedding matches the configured vector dimension.
    Fails fast if there is a mismatch.
    """
    dim = len(embedding)
    if dim != settings.EMBEDDING_DIMENSION:
        raise ValueError(
            f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSION}, got {dim}. "
            "Mixing embedding dimensions will corrupt vector similarity search."
        )
    return True
