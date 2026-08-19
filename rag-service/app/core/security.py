import secrets
from fastapi import Header, HTTPException, status
from app.core.config import settings


def verify_internal_secret(x_internal_secret: str = Header(None)) -> bool:
    if not x_internal_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Internal-Secret header",
        )
    if not secrets.compare_digest(x_internal_secret, settings.RAG_INTERNAL_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal secret",
        )
    return True
