# Deploying GlucoRAG FastAPI RAG Service on Vercel

This guide provides step-by-step instructions to deploy the **FastAPI + LangChain RAG service** on **Vercel** using Vercel's native Python Serverless Functions runtime (100% free, no credit card required).

---

## 1. Architecture & Vercel Entry Point

The RAG service is exposed to Vercel via:
- **Serverless Entry Point:** [`rag-service/api/index.py`](file:///home/mohamed/github/MRAG/rag-service/api/index.py) (re-exports the existing `app` from `app.main`).
- **Rewrite Rules:** [`rag-service/vercel.json`](file:///home/mohamed/github/MRAG/rag-service/vercel.json) routes all incoming requests directly to `/api/index.py`.

```
Incoming Request (e.g. GET /health or POST /rag/query)
                  │
                  ▼
         [ Vercel Edge Router ]
                  │
                  ▼ (vercel.json rewrite)
         [ api/index.py ]
                  │
                  ▼
         [ app.main:app (FastAPI) ]
```

---

## 2. Prerequisites & GitHub Push

Ensure your latest code and Vercel configuration files are committed and pushed to GitHub:

```bash
git add .
git commit -m "feat: prepare RAG service for Vercel deployment"
git push origin main
```

---

## 3. Step-by-Step Vercel Deployment

1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select and import your GitHub repository (`MRAG` / `glucoRag`).
4. In the **Configure Project** screen:
   - **Project Name:** `glucorag-rag` (or your preferred name)
   - **Framework Preset:** `Other`
   - **Root Directory:** Click **Edit** and select **`rag-service`** (IMPORTANT: do not leave it at root).
5. In **Environment Variables**, add the following variables:

| Variable Name | Required Value Description | Example / Default |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | `https://xidfjvukhkworjszayrr.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase `service_role` secret key | `sb_secret_...` |
| `OPENROUTER_API_KEY` | Your OpenRouter API Key | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | OpenRouter Model ID | `openrouter/free` |
| `EMBEDDING_MODEL` | Embedding Model Name | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | Vector Dimension | `1536` |
| `CHUNK_SIZE` | Chunk size in characters | `800` |
| `CHUNK_OVERLAP` | Overlap size in characters | `150` |
| `TOP_K` | Number of context chunks | `5` |
| `RAG_INTERNAL_SECRET` | Shared secret between Laravel & RAG | `1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f` |
| `ALLOWED_ORIGINS` | *(Optional)* Allowed CORS origins | `https://glucorag.vercel.app,http://localhost:5173` |

6. Click **Deploy**.
7. Vercel will install dependencies from `requirements.txt`, detect Python runtime, and deploy your serverless application.

---

## 4. Verification & Testing

Once deployed, copy your assigned Vercel URL (e.g. `https://glucorag-rag.vercel.app`).

### A. Health Check Test
Open in your browser or run in terminal:
```bash
curl https://glucorag-rag.vercel.app/health
```
**Expected output:**
```json
{"status":"ok"}
```

### B. Root Endpoint Test
```bash
curl https://glucorag-rag.vercel.app/
```
**Expected output:**
```json
{
  "service": "Medical RAG Service",
  "scope": "Type 2 Diabetes Screening",
  "status": "online"
}
```

---

## 5. Updating Laravel Backend Configuration

In your Laravel backend deployment (on Render or cloud host), update the RAG service URL in its environment variables:

```ini
RAG_SERVICE_URL=https://glucorag-rag.vercel.app
RAG_INTERNAL_SECRET=1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f
```

---

## 6. Local Development Remains Unchanged

You can continue developing and running the RAG service locally with standard uvicorn:

```bash
cd rag-service
./venv/bin/uvicorn app.main:app --reload --port 8001
```
