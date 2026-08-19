from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes_health, routes_query, routes_ingest

app = FastAPI(
    title="Medical RAG Service - Type 2 Diabetes Screening",
    description="Dedicated RAG service for primary-care clinician Type 2 Diabetes screening guidance.",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers
app.include_router(routes_health.router)
app.include_router(routes_query.router)
app.include_router(routes_ingest.router)


@app.get("/")
def root():
    return {
        "service": "Medical RAG Service",
        "scope": "Type 2 Diabetes Screening",
        "status": "online",
    }
