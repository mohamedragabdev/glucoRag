# GlucoRAG — Production Deployment Guide & Runbook

This document provides a step-by-step deployment guide for taking **GlucoRAG** online with a production-grade, low-cost / free-tier architecture.

---

## 1. Hosting Architecture Overview

```
                                 [ User Browser ]
                                        │
                                        ▼ (HTTPS)
                         ┌─────────────────────────────┐
                         │  Frontend (Vercel / Render) │
                         │       React 19 + Vite       │
                         └──────────────┬──────────────┘
                                        │ (HTTPS / CORS)
                                        ▼
                         ┌─────────────────────────────┐
                         │   Backend API (Render)      │
                         │   Laravel 11 Web Service    │
                         │  + Async Queue Worker       │
                         └──────┬───────────────┬──────┘
                                │               │
          (Server-to-Server)    │               │ (MySQL Wire Protocol)
          (X-Internal-Secret)   │               ▼
                                │     ┌────────────────────────┐
                                │     │  MySQL Application DB  │
                                │     │  (Aiven / TiDB / etc.) │
                                │     │  Users, Chats, Queue   │
                                │     └────────────────────────┘
                                ▼
                 ┌─────────────────────────────┐
                 │  RAG Service (Vercel/Render)│
                 │      FastAPI + LangChain    │
                 └──────┬───────────────┬──────┘
                        │               │
  (PostgreSQL / pgvector)│               │ (HTTPS)
                        ▼               ▼
          ┌───────────────────────┐   ┌────────────────────────┐
          │  Supabase Cloud (RAG) │   │  OpenRouter AI (LLM)   │
          │   document_chunks     │   │     openrouter/free    │
          │  match_document_chunks│   └────────────────────────┘
          └───────────────────────┘
```

---

## 2. Selected Cloud Providers & Free-Tier Suitability

| Component | Recommended Provider | Free Tier Details | Why Selected |
|---|---|---|---|
| **Frontend** | **Vercel** (or Render Static Site) | Generous permanent free tier (Unlimited bandwidth/SSL). | Global edge CDN, fast builds, native SPA routing with zero configuration. |
| **Laravel Backend** | **Render Web Service** (Docker) | Free Tier (512MB RAM, spins down on 15m idle). | Docker containerization allows running PHP 8.2, web server, and background queue worker together. |
| **FastAPI RAG** | **Render Web Service** (Python/Docker) | Free Tier (512MB RAM, spins down on 15m idle). | Native FastAPI/uvicorn support, automatic SSL, direct health checks. |
| **RAG Vector DB** | **Supabase Cloud** (Existing) | Free Tier (500MB DB, pgvector, RPC functions). | Already configured with `document_chunks` and embeddings. |
| **Laravel MySQL** | **Aiven MySQL** (or **TiDB Serverless**) | Free Tier (Aiven free plan or TiDB Serverless 5GB free). | Dedicated, permanent cloud MySQL without breaking the two-database architecture. |
| **LLM Provider** | **OpenRouter** | Free routing via `openrouter/free`. | Dynamic routing across top open-source models with zero token cost. |

---

## 3. Environment Variables Matrix

### A. Frontend (`frontend/.env`)
| Variable | Scope | Description | Production Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | Public (Build-time) | Full URL of the deployed Laravel API ending in `/api` | `https://glucorag-backend.onrender.com/api` |

### B. Laravel Backend (`backend/.env`)
| Variable | Scope | Description | Production Example |
|---|---|---|---|
| `APP_NAME` | Public | Application name | `GlucoRAG` |
| `APP_ENV` | Secret | Environment mode | `production` |
| `APP_KEY` | Secret | 32-byte encryption key (generate via `php artisan key:generate --show`) | `base64:79G9EGKkAtqI/2mQJOBGPIJdpM0oSze/fHLxubG+8Ks=` |
| `APP_DEBUG` | Secret | Disable stack traces in production | `false` |
| `APP_URL` | Secret | Public URL of the backend web service | `https://glucorag-backend.onrender.com` |
| `DB_CONNECTION` | Secret | Database driver | `mysql` |
| `DB_HOST` | Secret | MySQL host from Aiven / TiDB | `mysql-prod.aivencloud.com` |
| `DB_PORT` | Secret | MySQL port | `3306` (or `4000` for TiDB) |
| `DB_DATABASE` | Secret | MySQL database name | `defaultdb` |
| `DB_USERNAME` | Secret | MySQL username | `avnadmin` |
| `DB_PASSWORD` | Secret | MySQL password | `your_secure_password` |
| `SESSION_DRIVER` | Secret | Session storage | `database` |
| `CACHE_STORE` | Secret | Cache storage | `database` |
| `QUEUE_CONNECTION` | Secret | Asynchronous queue driver | `database` |
| `FRONTEND_URL` | Secret | Comma-separated allowed frontend origins for CORS | `https://glucorag.vercel.app` |
| `SANCTUM_STATEFUL_DOMAINS` | Secret | Frontend domain without protocol | `glucorag.vercel.app` |
| `RAG_SERVICE_URL` | Secret | URL of the deployed FastAPI RAG service | `https://glucorag-rag.onrender.com` |
| `RAG_INTERNAL_SECRET` | Secret | Shared secret between Laravel and FastAPI (min 32 chars) | `1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f` |

### C. FastAPI RAG Service (`rag-service/.env`)
| Variable | Scope | Description | Production Example |
|---|---|---|---|
| `SUPABASE_URL` | Secret | Supabase project URL | `https://xidfjvukhkworjszayrr.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret | Supabase service-role secret key | `sb_secret_OisR4gr__cYBRBpRaTrveQ_FhrZBxkb` |
| `OPENROUTER_API_KEY` | Secret | OpenRouter API Key | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | Secret | Model ID | `openrouter/free` |
| `EMBEDDING_MODEL` | Secret | Embedding model name | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | Secret | Vector dimension | `1536` |
| `CHUNK_SIZE` | Secret | Chunk size | `800` |
| `CHUNK_OVERLAP` | Secret | Chunk overlap | `150` |
| `TOP_K` | Secret | Retrieved context chunks | `5` |
| `RAG_INTERNAL_SECRET` | Secret | Shared secret matching Laravel | `1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f` |

---

## 4. Step-by-Step Deployment Walkthrough

### STEP 1: Set Up Cloud MySQL Database (e.g. Aiven)
1. Go to [Aiven Console](https://console.aiven.io/) (or [TiDB Cloud](https://tidbcloud.com/)).
2. Create a new **Free Tier MySQL** service (select region closest to your Render services, e.g. Frankfurt / Oregon / Virginia).
3. Save the connection details:
   - `Host`
   - `Port`
   - `User`
   - `Password`
   - `Database Name`

---

### STEP 2: Push Repository to GitHub
Ensure all code and deployment files are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "chore: prepare production deployment configuration"
git push origin main
```

---

### STEP 3: Deploy FastAPI RAG Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository.
4. Configure service settings:
   - **Name:** `glucorag-rag`
   - **Root Directory:** `rag-service`
   - **Runtime:** `Python 3` (or `Docker`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
5. In **Environment Variables**, add:
   ```
   SUPABASE_URL = https://xidfjvukhkworjszayrr.supabase.co
   SUPABASE_SERVICE_ROLE_KEY = <your-supabase-service-role-key>
   OPENROUTER_API_KEY = <your-openrouter-api-key>
   OPENROUTER_MODEL = openrouter/free
   EMBEDDING_MODEL = text-embedding-3-small
   EMBEDDING_DIMENSION = 1536
   CHUNK_SIZE = 800
   CHUNK_OVERLAP = 150
   TOP_K = 5
   RAG_INTERNAL_SECRET = 1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f
   ```
6. Click **Deploy Web Service**.
7. Copy your deployed RAG Service URL (e.g., `https://glucorag-rag.onrender.com`).

---

### STEP 4: Deploy Laravel Backend on Render
1. On Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name:** `glucorag-backend`
   - **Root Directory:** `backend`
   - **Runtime:** `Docker` (Render will automatically detect `backend/Dockerfile`)
   - **Plan:** Free
4. In **Environment Variables**, add:
   ```
   APP_NAME = GlucoRAG
   APP_ENV = production
   APP_DEBUG = false
   APP_KEY = base64:79G9EGKkAtqI/2mQJOBGPIJdpM0oSze/fHLxubG+8Ks=
   APP_URL = https://glucorag-backend.onrender.com
   DB_CONNECTION = mysql
   DB_HOST = <your-mysql-host>
   DB_PORT = 3306
   DB_DATABASE = <your-db-name>
   DB_USERNAME = <your-db-username>
   DB_PASSWORD = <your-db-password>
   SESSION_DRIVER = database
   CACHE_STORE = database
   QUEUE_CONNECTION = database
   FRONTEND_URL = https://glucorag.vercel.app,http://localhost:5173
   SANCTUM_STATEFUL_DOMAINS = glucorag.vercel.app
   RAG_SERVICE_URL = https://glucorag-rag.onrender.com
   RAG_INTERNAL_SECRET = 1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f
   ```
5. Click **Deploy Web Service**.
   - The container `docker-entrypoint.sh` will automatically run `php artisan migrate --force`, cache configurations, start the background queue worker, and launch the API server.
6. Copy your deployed Backend URL (e.g., `https://glucorag-backend.onrender.com`).

---

### STEP 5: Deploy Frontend on Vercel
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository.
4. In Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click Edit and select `frontend`.
5. In **Environment Variables**:
   ```
   VITE_API_BASE_URL = https://glucorag-backend.onrender.com/api
   ```
6. Click **Deploy**.
7. Vercel will build and assign your production domain (e.g., `https://glucorag.vercel.app`).
8. *(If different from initial setup)*: Update `FRONTEND_URL` and `SANCTUM_STATEFUL_DOMAINS` on Render backend settings to match your exact Vercel URL.

---

### STEP 6: Document Ingestion into Supabase RAG Database

Because reference clinical PDFs (ADA 2024 / USPSTF 2021) are copyrighted medical publications, they are ingested once into Supabase pgvector from your local administrative environment:

1. Place the official PDFs in your local `rag-service/data/` folder:
   - `ada_standards_of_care_2024.pdf`
   - `uspstf_t2d_screening_2021.pdf`
2. Run ingestion using `POST /rag/ingest`:
   ```bash
   # Ingest ADA Guidelines
   curl -X POST https://glucorag-rag.onrender.com/rag/ingest \
     -H "X-Internal-Secret: 1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f" \
     -H "Content-Type: application/json" \
     -d '{
       "document_path": "data/ada_standards_of_care_2024.pdf",
       "document_id": "ada_standards_of_care_2024",
       "title": "ADA Standards of Care in Diabetes 2024"
     }'

   # Ingest USPSTF Guidelines
   curl -X POST https://glucorag-rag.onrender.com/rag/ingest \
     -H "X-Internal-Secret: 1eb5de452e9aad63346f4b705dddda179d96b7bba0969855e165195b9ce3e48f" \
     -H "Content-Type: application/json" \
     -d '{
       "document_path": "data/uspstf_t2d_screening_2021.pdf",
       "document_id": "uspstf_t2d_screening_2021",
       "title": "USPSTF Screening for Prediabetes and Type 2 Diabetes"
     }'
   ```
3. Verify chunk insertion in Supabase SQL Editor:
   ```sql
   SELECT document_id, COUNT(*) AS total_chunks, MIN(page_number) AS min_page, MAX(page_number) AS max_page
   FROM document_chunks
   GROUP BY document_id;
   ```

---

## 5. Production Health Check URLs

After completing deployment, verify each layer using these public endpoints:

1. **RAG Service Health:**
   `https://<your-rag-service>.onrender.com/health`  
   *Expected response:* `{"status": "ok"}`

2. **Laravel Backend Health:**
   `https://<your-backend-service>.onrender.com/api/health`  
   *Expected response:* `{"status": "ok", "service": "GlucoRAG Backend API", "timestamp": "..."}`

3. **Frontend Health:**
   `https://<your-frontend>.vercel.app/login`  
   *Expected response:* GlucoRAG login screen loads cleanly with zero console errors.

---

## 6. End-to-End Verification Checklist

Perform these test cases directly in your live browser application:

- [ ] **Account Creation:** Register a clinician user at `/register`.
- [ ] **Authentication:** Log out and log in again at `/login`.
- [ ] **Conversation Lifecycle:** Click **+ New Screening Query**; verify new thread appears in sidebar.
- [ ] **English Screening (USPSTF):**
  - Prompt: `"What is the recommended screening age according to the USPSTF?"`
  - Expected: Status becomes `completed`, grounded clinical answer is displayed with clickable citations.
- [ ] **Arabic Screening (ADA/USPSTF):**
  - Prompt: `"ما هي توصيات USPSTF لفحص السكري من النوع الثاني؟"`
  - Expected: Evidence-grounded answer rendered in professional Arabic with citations.
- [ ] **Conversational Greeting:**
  - Prompt: `"Hi"` / `"السلام عليكم"`
  - Expected: Instant polite GlucoRAG introduction without vector retrieval latency.
- [ ] **Prohibited Category Refusal:**
  - Prompt: `"How do I treat diabetes?"` / `"ما جرعة الميتفورمين؟"`
  - Expected: Standard concise refusal explaining that GlucoRAG is specialized exclusively for screening guidance.
