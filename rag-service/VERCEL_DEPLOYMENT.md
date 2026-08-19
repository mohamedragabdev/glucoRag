# Deploying GlucoRAG FastAPI RAG Service on Vercel

This guide provides step-by-step instructions to deploy the **FastAPI + LangChain RAG service** on **Vercel** using Vercel's native Python Serverless Functions runtime (100% free, no credit card required).

---

## 1. Architecture & Native Vercel Entry Point

The RAG service uses Vercel's native zero-configuration FastAPI discovery:
- **Serverless Root Entry Point:** [`rag-service/index.py`](file:///home/mohamed/github/MRAG/rag-service/index.py) (exposes the exact `app` instance from `app.main`).
- Vercel automatically detects `index.py`, maps all routes (`/health`, `/docs`, `/openapi.json`, `/rag/query`, `/rag/ingest`) directly to the FastAPI app without requiring custom rewrite rules or nested `/api` subfolders.

---

## 2. Redeployment Commands

Commit and push the updated entrypoint to GitHub:

```bash
git add .
git commit -m "fix(rag-service): use native Vercel FastAPI root entrypoint index.py"
git push origin main
```

---

## 3. Vercel Project Settings

1. In [Vercel Dashboard](https://vercel.com/):
   - **Project Name:** `glucorag-rag`
   - **Framework Preset:** `Other`
   - **Root Directory:** `rag-service`
2. **Environment Variables:**
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL` = `openrouter/free`
   - `EMBEDDING_MODEL` = `text-embedding-3-small`
   - `EMBEDDING_DIMENSION` = `1536`
   - `CHUNK_SIZE` = `800`
   - `CHUNK_OVERLAP` = `150`
   - `TOP_K` = `5`
   - `RAG_INTERNAL_SECRET` = `1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f`

---

## 4. Verification

After deployment:
- `https://YOUR-RAG-DEPLOYMENT.vercel.app/health` $\rightarrow$ `{"status":"ok"}`
- `https://YOUR-RAG-DEPLOYMENT.vercel.app/docs` $\rightarrow$ Interactive Swagger UI
- `https://YOUR-RAG-DEPLOYMENT.vercel.app/` $\rightarrow$ `{"service":"Medical RAG Service", ...}`
