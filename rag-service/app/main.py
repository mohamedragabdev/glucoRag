from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_health, routes_query, routes_ingest

app = FastAPI(
    title="Medical RAG Service - Type 2 Diabetes Screening",
    description="Dedicated RAG service for primary-care clinician Type 2 Diabetes screening guidance.",
    version="1.0.0",
)

# CORS (Restricted to internal / local development origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
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
