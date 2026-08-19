# Operational Runbook & Deployment Guide
## Medical RAG System — Type 2 Diabetes Screening Assistant

---

## 1. PROJECT STRUCTURE

The repository is structured as a decoupled three-tier system:

```
MRAG/
├── backend/                          # Laravel 13 Application (API, Sanctum Auth, Persistence, Orchestration)
│   ├── app/
│   │   ├── Http/
│   │   │   ├── Controllers/Api/
│   │   │   │   ├── AuthController.php          # /api/register, /api/login, /api/logout
│   │   │   │   ├── ConversationController.php  # /api/conversations CRUD
│   │   │   │   └── MessageController.php       # /api/conversations/{id}/messages, /api/messages/{id}
│   │   │   ├── Middleware/
│   │   │   │   └── EnsureConversationOwnership.php # Authorization barrier for conversations and messages
│   │   │   ├── Requests/                       # Form validation (RegisterRequest, LoginRequest, StoreMessageRequest)
│   │   │   └── Resources/                      # JsonResources (ConversationResource, MessageResource, MessageCitationResource)
│   │   ├── Jobs/
│   │   │   └── ProcessRagMessageJob.php        # Async queue worker job (3 retries, backoff [10s, 30s, 90s])
│   │   ├── Models/
│   │   │   ├── User.php                        # User model with Sanctum tokens and conversation relation
│   │   │   ├── Conversation.php                # Conversation entity
│   │   │   ├── Message.php                     # User and assistant message entity
│   │   │   └── MessageCitation.php             # Verified citations attached to assistant messages
│   │   ├── Services/
│   │   │   └── RagServiceClient.php            # Guzzle/Http client communicating with FastAPI via X-Internal-Secret
│   │   └── Exceptions/
│   │       └── RagServiceException.php         # Custom exception for RAG upstream communication failures
│   ├── config/
│   │   ├── rag.php                             # RAG service URL, internal secret, timeout config
│   │   └── cors.php                            # CORS configuration restricted to frontend domain
│   ├── database/
│   │   └── migrations/                         # Schema definitions for users, tokens, conversations, messages, citations
│   ├── routes/
│   │   └── api.php                             # API routes with sanctum, throttle, and ownership middleware
│   └── tests/                                  # PHPUnit Unit and Feature tests
│
├── rag-service/                      # Python FastAPI RAG Service
│   ├── app/
│   │   ├── main.py                             # FastAPI app instance, CORS, router mounting
│   │   ├── api/
│   │   │   ├── routes_health.py                # GET /health public liveness probe
│   │   │   ├── routes_query.py                 # POST /rag/query internal chat endpoint
│   │   │   └── routes_ingest.py                # POST /rag/ingest document ingestion endpoint
│   │   ├── core/
│   │   │   ├── config.py                       # Pydantic BaseSettings loading .env
│   │   │   └── security.py                     # Constant-time X-Internal-Secret validation
│   │   ├── schemas/
│   │   │   ├── query.py                        # QueryRequest and Turn schemas
│   │   │   ├── ingest.py                       # IngestRequest and IngestResponse schemas
│   │   │   └── rag_response.py                 # RagResponse schema matching Section 15 contract
│   │   ├── services/
│   │   │   ├── ingestion_service.py            # PDF loading, chunking, embedding, transactional upsert
│   │   │   ├── retrieval_service.py            # Query embedding, Supabase RPC similarity search, context formatting
│   │   │   ├── generation_service.py           # 2-step RAG orchestrator, fail-closed safety enforcement
│   │   │   └── citation_builder.py             # Strict intersection of used chunk IDs with retrieved metadata
│   │   └── langchain_pipeline/
│   │       ├── loaders.py                      # PDF loader (page-by-page, loader-provided metadata only)
│   │       ├── chunking.py                     # RecursiveCharacterTextSplitter, deterministic chunk IDs
│   │       ├── embeddings.py                   # OpenAI/OpenRouter embeddings client + dimension validator
│   │       ├── vectorstore.py                  # Supabase pgvector client adapter (match_document_chunks)
│   │       └── llm_chain.py                    # LangChain structured output chain bound to OpenRouter
│   ├── scripts/
│   │   └── evaluate_rag.py                     # Automated RAG evaluation benchmark script
│   ├── sql/
│   │   ├── 001_create_documents_table.sql      # Supabase document_chunks schema and vector index
│   │   └── 002_similarity_search_function.sql  # match_document_chunks SQL function
│   ├── tests/                                  # Pytest test suite
│   ├── requirements.txt                        # Python dependencies
│   └── pytest.ini                              # Pytest configuration
│
├── frontend/                         # React 19 + TypeScript + Vite + Tailwind CSS Application
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts                       # Axios client with Bearer token interceptor and 401 handler
│   │   ├── components/
│   │   │   ├── ConversationSidebar.tsx         # Sidebar for conversations, new conversation, logout
│   │   │   ├── MessageBubble.tsx               # User and Assistant messages, pending dots, error retry
│   │   │   ├── CitationList.tsx                # Expandable citations chips with similarity score
│   │   │   └── MessageComposer.tsx             # Textarea (1–2000 chars), char counter, send button
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx                   # Clinician authentication
│   │   │   ├── RegisterPage.tsx                # Clinician account registration
│   │   │   └── ChatPage.tsx                    # Main chat interface with 2-second polling
│   │   ├── state/
│   │   │   └── authStore.ts                    # Auth state hook with localStorage sync
│   │   ├── App.tsx                             # Top-level view routing
│   │   ├── main.tsx                            # React DOM entry point
│   │   └── index.css                           # Tailwind CSS v4 styling
│   ├── package.json                            # NPM dependencies and scripts
│   └── vite.config.ts                          # Vite bundler configuration with @tailwindcss/vite
│
└── docs/                             # Documentation and Evaluation Assets
    ├── IMPLEMENTATION.md                       # Architectural specification & requirements
    ├── RUNBOOK.md                              # This operational and deployment runbook
    ├── RAG_SOURCES.md                          # Expected reference documents, ingestion steps, evaluation test set
    ├── POSTMAN_RUNBOOK.md                      # Postman execution runbook
    ├── POSTMAN_COLLECTION.json                 # Postman collection file for manual/automated API verification
    ├── API_CONTRACT.md                         # Detailed API contract documentation
    ├── EVALUATION.md                           # RAG evaluation methodology and benchmark metrics
    └── eval_dataset.json                       # Labeled test dataset for RAG recall and safety testing
```

---

## 2. PREREQUISITES

### System Environment
- **Operating System:** Linux / macOS / Windows (WSL2 recommended on Windows)
- **PHP:** `^8.3` (Installed: `PHP 8.5.8`)
- **Composer:** `^2.2` (Installed: `Composer 2.10.2`)
- **Laravel Framework:** `^13.17` (Installed: `Laravel 13.26.0`)
- **Python:** `^3.11` (Installed: `Python 3.14.6`)
- **Node.js:** `^20.0` or `^22.0` (Installed: `Node v22.22.2`)
- **NPM:** `^10.0` (Installed: `npm 10.9.7`)

### Required PHP Extensions
- `pdo_sqlite` (for local development and testing) or `pdo_pgsql` (for PostgreSQL)
- `curl`, `mbstring`, `openssl`, `tokenizer`, `xml`, `ctype`, `json`, `bcmath`, `filter`

### Required Python Packages (from `rag-service/requirements.txt`)
- `fastapi==0.141.1`, `uvicorn==0.52.4`, `pydantic==2.13.4`, `pydantic-settings==2.15.0`
- `langchain==1.3.15`, `langchain-core==1.5.6`, `langchain-openai==1.5.2`, `langchain-text-splitters==1.1.2`
- `pypdf==6.16.1`, `supabase==2.31.0`, `httpx==0.28.1`, `openai==3.3.0`
- `pytest==9.1.1`, `pytest-asyncio==1.4.0`, `python-dotenv==1.2.3`

### Required Node Packages (from `frontend/package.json`)
- `react@^19.2.8`, `react-dom@^19.2.8`, `axios@^1.19.0`, `lucide-react@^1.33.0`, `tailwindcss@^4.3.3`, `@tailwindcss/vite@^4.3.3`, `vite@^8.2.0`, `typescript@~6.0.2`

### External Accounts & Services
- **Supabase Account:** Free project with PostgreSQL and `pgvector` extension enabled.
- **OpenRouter Account:** Free API key from [openrouter.ai](https://openrouter.ai) with access to generation models (e.g. `openai/gpt-4o-mini`).

---

## 3. ENVIRONMENT VARIABLES

### 3.1 Backend (`backend/.env`)

| Variable | Purpose | Where to Get | Public or Secret | Type |
|---|---|---|---|---|
| `APP_NAME` | Name of the application | Custom (`MedicalRAG`) | Public | Application |
| `APP_ENV` | Environment name | `local`, `staging`, or `production` | Public | Application |
| `APP_KEY` | Laravel encryption key | Generated via `php artisan key:generate` | **SECRET** | Server-only |
| `APP_DEBUG` | Enable debug stacktraces | `true` locally, `false` in production | Public | Application |
| `APP_URL` | Base URL of Laravel backend | E.g. `http://localhost:8000` | Public | Application |
| `DB_CONNECTION` | Database driver | `sqlite` or `pgsql` | Public | Database |
| `DB_HOST` | Database host | E.g. `127.0.0.1` | Public | Database |
| `DB_PORT` | Database port | E.g. `5432` | Public | Database |
| `DB_DATABASE` | Database name or SQLite path | E.g. `medical_rag` | Public | Database |
| `DB_USERNAME` | Database user | Database credentials | **SECRET** | Server-only |
| `DB_PASSWORD` | Database password | Database credentials | **SECRET** | Server-only |
| `QUEUE_CONNECTION` | Queue driver | `database` (local/default) or `redis` | Public | Queue |
| `SANCTUM_STATEFUL_DOMAINS` | Frontend domain for Sanctum | E.g. `localhost:5173` | Public | Security |
| `RAG_SERVICE_URL` | Base URL of FastAPI RAG service | E.g. `http://localhost:8001` | Public | Integration |
| `RAG_INTERNAL_SECRET` | Shared secret token for FastAPI auth | Custom random string (e.g. 64 hex characters) | **SECRET** | Server-only |
| `FRONTEND_URL` | Frontend URL for CORS whitelist | E.g. `http://localhost:5173` | Public | Security |

### 3.2 FastAPI RAG Service (`rag-service/.env`)

| Variable | Purpose | Where to Get | Public or Secret | Type |
|---|---|---|---|---|
| `SUPABASE_URL` | URL of Supabase project | Supabase Dashboard $\rightarrow$ Project Settings $\rightarrow$ API | Public | Database |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for vector operations | Supabase Dashboard $\rightarrow$ Project Settings $\rightarrow$ API (Service Role) | **SECRET** | Server-only |
| `OPENROUTER_API_KEY` | OpenRouter API access key | [openrouter.ai/keys](https://openrouter.ai/keys) | **SECRET** | Server-only |
| `OPENROUTER_MODEL` | Model slug for generation | Default: `openai/gpt-4o-mini` | Public | AI Model |
| `EMBEDDING_MODEL` | Embedding model slug | Default: `text-embedding-3-small` | Public | AI Model |
| `EMBEDDING_DIMENSION` | Dimension of the vector embeddings | Default: `1536` | Public | AI Model |
| `CHUNK_SIZE` | Character count per chunk | Default: `800` | Public | Chunking |
| `CHUNK_OVERLAP` | Character overlap between chunks | Default: `150` | Public | Chunking |
| `TOP_K` | Number of chunks to retrieve | Default: `5` | Public | Retrieval |
| `RAG_INTERNAL_SECRET` | Shared secret token (must match Laravel) | Same string as `RAG_INTERNAL_SECRET` in Laravel | **SECRET** | Server-only |

### 3.3 Frontend (`frontend/.env`)

| Variable | Purpose | Where to Get | Public or Secret | Type |
|---|---|---|---|---|
| `VITE_API_BASE_URL` | Base URL of Laravel API | E.g. `http://localhost:8000/api` | **PUBLIC** | Frontend-safe |

> [!CAUTION]
> Never put `OPENROUTER_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `RAG_INTERNAL_SECRET`, or database passwords into `frontend/.env` or any frontend code. The frontend only communicates with the Laravel backend.

---

## 4. LOCAL DATABASE SETUP

### Step 1: Application Database (Laravel MySQL)
The application database stores users, conversations, messages, citations, and queue jobs in **MySQL**.

In MySQL, create the database:
```sql
CREATE DATABASE medical_rag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Configure `backend/.env`:
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=medical_rag
DB_USERNAME=root
DB_PASSWORD=your_mysql_password
```

*(Note: SQLite `DB_CONNECTION=sqlite` is also supported for local test suites and CI).*

### Step 2: Run Laravel Migrations in MySQL
```bash
cd backend
php artisan migrate
```
This creates:
- `users` (clinicians)
- `personal_access_tokens` (Sanctum)
- `conversations` (chat threads)
- `messages` (user & assistant messages)
- `message_citations` (verified citation chips)
- `jobs` and `failed_jobs` (queue tables)

### Step 3: Supabase pgvector Setup (Vector Store)
Open your Supabase project's **SQL Editor** and execute the two migration files in order:

1. Execute [`rag-service/sql/001_create_documents_table.sql`](file:///home/mohamed/github/MRAG/rag-service/sql/001_create_documents_table.sql):
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id        TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL,
    title           TEXT NOT NULL,
    page_number     INTEGER,
    content         TEXT NOT NULL,
    embedding       VECTOR(1536) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

2. Execute [`rag-service/sql/002_similarity_search_function.sql`](file:///home/mohamed/github/MRAG/rag-service/sql/002_similarity_search_function.sql):
```sql
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
```

---

## 5. RUNNING LARAVEL

Execute the following commands in `backend/`:

```bash
cd backend

# 1. Install dependencies
composer install

# 2. Setup environment
cp .env.example .env

# 3. Generate application key
php artisan key:generate

# 4. Run database migrations
php artisan migrate

# 5. Start the HTTP API server
php artisan serve --port 8000
```
The Laravel API will be reachable at `http://localhost:8000/api`.

---

## 6. RUNNING THE QUEUE

The application uses asynchronous queue jobs to decouple LLM generation latency from the HTTP request cycle.

### How the Queue Works
1. Clinician submits question via `POST /api/conversations/{id}/messages`.
2. Laravel persists user message (`status=completed`), persists assistant placeholder message (`status=pending`), and immediately returns `202 Accepted` with the assistant message ID.
3. `ProcessRagMessageJob` is dispatched to the queue.
4. The queue worker picks up `ProcessRagMessageJob($assistantMessageId)`:
   - Fetches recent conversation history (last 6 turns).
   - Calls FastAPI `POST /rag/query` with `X-Internal-Secret`.
   - On success: updates assistant message (`status=completed`, `content=answer`) and inserts `MessageCitation` rows.
   - On out-of-scope or insufficient-evidence: updates assistant message (`status=completed`) with fixed refusal text and 0 citations.
   - On transient 5xx/network error: triggers Laravel automatic retry with backoff.
   - On permanent failure (3 retries exhausted): `failed()` hook updates message (`status=failed`, `error_message="We couldn't process your question right now. Please try again."`).

### Queue Configuration
In `backend/.env`:
```env
QUEUE_CONNECTION=database
```

### Start the Queue Worker
In a dedicated terminal:
```bash
cd backend
php artisan queue:work --tries=3 --backoff=10,30,90
```

### Inspecting and Retrying Failed Jobs
- **List failed jobs:**
  ```bash
  php artisan queue:failed
  ```
- **Retry a specific failed job:**
  ```bash
  php artisan queue:retry <job_id>
  ```
- **Retry all failed jobs:**
  ```bash
  php artisan queue:retry all
  ```
- **Flush / Clear failed jobs:**
  ```bash
  php artisan queue:flush
  ```

---

## 7. RUNNING THE FASTAPI RAG SERVICE

Execute the following commands in `rag-service/`:

```bash
cd rag-service

# 1. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENROUTER_API_KEY, and RAG_INTERNAL_SECRET

# 4. Start the FastAPI server
uvicorn app.main:app --reload --port 8001
```

### Health Check Verification
In another terminal:
```bash
curl http://localhost:8001/health
```
Expected response:
```json
{"status":"ok"}
```

---

## 8. RUNNING THE FRONTEND

Execute the following commands in `frontend/`:

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Ensure VITE_API_BASE_URL=http://localhost:8000/api

# 3. Start development server
npm run dev
```
The React frontend will be accessible at `http://localhost:5173`.

### Production Build & Preview
```bash
# Compile TypeScript and bundle assets
npm run build

# Preview production build locally
npm run preview
```

---

## 9. STARTING THE COMPLETE SYSTEM (LOCAL ORDER)

Open **4 separate terminal windows**:

```
┌────────────────────────────────────────────────────────┐
│ Terminal 1: FastAPI RAG Service                        │
│ cd rag-service && source venv/bin/activate             │
│ uvicorn app.main:app --port 8001                       │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ Terminal 2: Laravel API Backend                        │
│ cd backend && php artisan serve --port 8000            │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ Terminal 3: Laravel Queue Worker                       │
│ cd backend && php artisan queue:work                   │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ Terminal 4: React Frontend                             │
│ cd frontend && npm run dev                             │
└────────────────────────────────────────────────────────┘
```

---

## 10. RAG KNOWLEDGE BASE

### Accepted File Formats & Requirements
- **Format:** PDF (`.pdf`) documents.
- **Requirement:** Digitally readable PDF with searchable text layers (not scanned images without OCR).

### Text Extraction & Chunking Specifications
- **Loader:** `pypdf` via [`load_pdf_document`](file:///home/mohamed/github/MRAG/rag-service/app/langchain_pipeline/loaders.py). Page numbers are normalized to 1-indexed.
- **Splitter:** LangChain `RecursiveCharacterTextSplitter`.
- **Chunk Size (`CHUNK_SIZE`):** `800` characters.
- **Chunk Overlap (`CHUNK_OVERLAP`):** `150` characters.
- **Chunk ID Convention:** Deterministic string formatted as `{document_id}_p{page_number}_c{chunk_index}` (e.g. `ada_standards_2024_p5_c1`).

### Metadata Fields Extracted & Stored
- `chunk_id`: string PK (e.g. `ada_standards_2024_p5_c1`)
- `document_id`: string (e.g. `ada_standards_2024`)
- `title`: string (e.g. `ADA Standards of Care in Diabetes 2024`)
- `page_number`: integer (1-indexed page from source PDF)
- `content`: text of the chunk
- `embedding`: 1536-dimensional vector

> [!IMPORTANT]
> The loader only records metadata actually provided (`source`, `page_number`, `document_id`, `title`). It never fabricates publication dates, author names, or sections.

### Ingestion Execution (API)
To ingest a reference guideline PDF:
```bash
curl -X POST http://localhost:8001/rag/ingest \
  -H "X-Internal-Secret: dev_internal_secret_change_in_prod" \
  -H "Content-Type: application/json" \
  -d '{
    "document_path": "/absolute/path/to/ada_standards_2024.pdf",
    "document_id": "ada_standards_2024",
    "title": "ADA Standards of Care in Diabetes 2024"
  }'
```

### Idempotency, Versioning & Deletion
- **Deterministic Re-ingestion:** `IngestionService` first executes `DELETE FROM document_chunks WHERE document_id = :document_id`, then upserts new chunks using `ON CONFLICT (chunk_id) DO UPDATE`.
- **Versioning:** To update a guideline to a new version, supply a new `document_id` (e.g. `ada_standards_2025`) or overwrite the existing `document_id` to replace old text.

---

## 15. DEPLOYMENT (FREE MVP OPTIONS & ARCHITECTURE)

### Free Service Feasibility Analysis

| Component | Recommended Free Host | Service Type | Free Tier Limitations |
|---|---|---|---|
| **React Frontend** | **Vercel** | Static Web App | 100GB bandwidth/mo. Unlimited deploys. **Zero cold starts.** |
| **FastAPI RAG** | **Render** or **Koyeb** | Web Service (Python) | 512MB RAM, spins down after 15 min inactivity (50s cold start). |
| **Laravel Backend** | **Render** or **Fly.io** | Web Service (PHP/Docker) | 512MB RAM. Spins down on free tier if using Render. |
| **Queue Worker** | **Shared background loop / Cron** | Worker / Web process | Free tier hosts (Render/Koyeb) do **not** provide free always-on background worker instances. |
| **Vector Store** | **Supabase** | Managed Postgres + pgvector | 500MB database, 2 free projects, pgvector pre-installed. |
| **LLM Provider** | **OpenRouter** | API | Free tier / pay-as-you-go per token (free models available). |

### Handling the Queue on Free Tier
Because free hosting tiers (Render, Railway, Koyeb) charge for separate background worker services, there are two viable free architectures:
1. **Option A (Recommended for Free MVP):** Run a lightweight queue worker command in the background of the same container as the Laravel web server using a process supervisor (e.g. `supervisord` or `php artisan queue:work & php artisan serve`).
2. **Option B (Cron Driver):** Set `QUEUE_CONNECTION=sync` for instant synchronous execution in low-traffic demos, or trigger `php artisan queue:work --max-time=50` via a free cron job (e.g. cron-job.org or Vercel Cron).

---

## 16. FREE MVP DEPLOYMENT SPECIFICATION

### 1. Frontend (Vercel)
- **Platform:** Vercel
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variables:**
  - `VITE_API_BASE_URL`: `https://your-laravel-api.onrender.com/api`

### 2. FastAPI RAG Service (Render)
- **Platform:** Render
- **Service Type:** Web Service
- **Root Directory:** `rag-service`
- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `SUPABASE_URL`: `https://your-project.supabase.co`
  - `SUPABASE_SERVICE_ROLE_KEY`: `your-supabase-service-role-key`
  - `OPENROUTER_API_KEY`: `your-openrouter-api-key`
  - `OPENROUTER_MODEL`: `openai/gpt-4o-mini`
  - `EMBEDDING_MODEL`: `text-embedding-3-small`
  - `EMBEDDING_DIMENSION`: `1536`
  - `RAG_INTERNAL_SECRET`: `generate_a_secure_random_64_char_secret`

### 3. Laravel API Backend & Queue (Render / Docker)
- **Platform:** Render
- **Service Type:** Web Service (Docker)
- **Root Directory:** `backend`
- **Build Command:** `composer install --no-dev --optimize-autoloader`
- **Start Command:** `php artisan migrate --force && (php artisan queue:work --tries=3 & php artisan serve --host 0.0.0.0 --port $PORT)`
- **Environment Variables:**
  - `APP_NAME`: `MedicalRAG`
  - `APP_ENV`: `production`
  - `APP_DEBUG`: `false`
  - `APP_KEY`: `base64:...` (generate locally with `php artisan key:generate --show`)
  - `APP_URL`: `https://your-laravel-api.onrender.com`
  - `DB_CONNECTION`: `pgsql`
  - `DB_HOST`: `aws-0-us-east-1.pooler.supabase.com` (from Supabase DB settings)
  - `DB_PORT`: `5432` (or `6543` for connection pooling)
  - `DB_DATABASE`: `postgres`
  - `DB_USERNAME`: `postgres.your-project`
  - `DB_PASSWORD`: `your-supabase-db-password`
  - `QUEUE_CONNECTION`: `database`
  - `RAG_SERVICE_URL`: `https://your-fastapi-service.onrender.com`
  - `RAG_INTERNAL_SECRET`: `same_secret_as_in_fastapi`
  - `FRONTEND_URL`: `https://your-frontend.vercel.app`

---

## 17. DEPLOYMENT ORDER

Follow this exact deployment sequence:

```
1. Supabase Project Setup
   ├── Enable pgvector extension
   ├── Execute 001_create_documents_table.sql
   └── Execute 002_similarity_search_function.sql
          ↓
2. FastAPI RAG Service Deployment
   ├── Deploy to Render / Koyeb
   ├── Set SUPABASE_URL, SERVICE_ROLE_KEY, OPENROUTER_API_KEY, RAG_INTERNAL_SECRET
   └── Ingest reference screening PDF via POST /rag/ingest
          ↓
3. Laravel Backend Deployment
   ├── Deploy to Render
   ├── Set DB connection pointing to Supabase PostgreSQL
   ├── Set RAG_SERVICE_URL & RAG_INTERNAL_SECRET
   └── Run migrations (`php artisan migrate --force`)
          ↓
4. React Frontend Deployment
   ├── Deploy to Vercel
   └── Set VITE_API_BASE_URL pointing to Laravel production URL
          ↓
5. CORS & Security Verification
   ├── Set FRONTEND_URL in Laravel .env to your Vercel domain
   └── Test login and screening query end-to-end
```

---

## 18. ONLINE SMOKE TEST PROCEDURE

Verify each link in the chain in sequence:

1. **Test FastAPI Liveness:**
   ```bash
   curl https://your-fastapi-service.onrender.com/health
   ```
   *Expected:* `{"status": "ok"}`

2. **Test Direct RAG Query (Internal Secret):**
   ```bash
   curl -X POST https://your-fastapi-service.onrender.com/rag/query \
     -H "X-Internal-Secret: your_production_secret" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is universal screening age for T2D?", "conversation_history": [], "request_id": "smoke-1"}'
   ```
   *Expected:* `status="answered"`, `safety_status="in_scope"`, with verified citations.

3. **Test Clinician Registration (Laravel API):**
   ```bash
   curl -X POST https://your-laravel-api.onrender.com/api/register \
     -H "Content-Type: application/json" \
     -d '{"name": "Dr. Online Test", "email": "online.test@clinic.org", "password": "securepassword123", "password_confirmation": "securepassword123"}'
   ```
   *Expected:* `201 Created` with Bearer token.

4. **Test Web UI End-to-End:**
   - Open `https://your-frontend.vercel.app`.
   - Log in with `online.test@clinic.org`.
   - Send: *"What are the cutoff criteria for Fasting Plasma Glucose (FPG) in diabetes screening?"*
   - Verify: `202 Accepted` response with animated dots $\rightarrow$ completed answer with citation chip (document title, page number, similarity match).

---

## 19. TROUBLESHOOTING

| Issue | Root Cause | Resolution |
|---|---|---|
| **CORS error in browser** | `FRONTEND_URL` in `backend/.env` does not match the actual Vercel origin. | Update `FRONTEND_URL=https://your-app.vercel.app` in `backend/.env` and `config/cors.php`. |
| **401 Unauthorized on Laravel routes** | Missing or expired Sanctum Bearer token in request header. | Re-login or check `localStorage.getItem('mrag_token')`. |
| **401 Unauthorized on FastAPI `/rag/query`** | `RAG_INTERNAL_SECRET` in `backend/.env` does not match `rag-service/.env`. | Synchronize `RAG_INTERNAL_SECRET` across both services. |
| **403 Forbidden on Conversation / Message** | Requesting user does not own the conversation (`user_id !== auth()->id()`). | Authenticate with the user account that created the conversation. |
| **422 Unprocessable Entity on Message send** | Message content is empty or exceeds 2000 characters. | Ensure question is between 1 and 2000 characters. |
| **Queue jobs stay `pending` indefinitely** | `php artisan queue:work` is not running. | Start queue worker with `php artisan queue:work` or inspect `failed_jobs`. |
| **502 Bad Gateway from Laravel to FastAPI** | FastAPI service is down or experiencing a cold start on free hosting. | Check FastAPI logs with `curl https://your-rag-service/health` to warm up container. |
| **Supabase vector error / Dimension mismatch** | Embedding model output dimension does not match `vector(1536)` column. | Ensure `EMBEDDING_DIMENSION=1536` matches model (`text-embedding-3-small`). |
| **OpenRouter 401 / 402 error** | Invalid `OPENROUTER_API_KEY` or exhausted credits on OpenRouter. | Verify API key at [openrouter.ai/keys](https://openrouter.ai/keys). |
| **Render cold start delay (~50s)** | Free web services spin down after 15 minutes of inactivity. | Send a ping request or upgrade to paid tier for instant response. |

---

## 20. FINAL OPERATIONAL CHECKLIST

- [ ] Repository cloned
- [ ] Environment variables configured (`backend/.env`, `rag-service/.env`, `frontend/.env`)
- [ ] Supabase project configured with `pgvector` extension
- [ ] Tables created (`001_create_documents_table.sql` and `002_similarity_search_function.sql`)
- [ ] Application database migrated (`php artisan migrate:fresh`)
- [ ] RAG source guideline PDFs placed and verified
- [ ] Documents ingested via `POST /rag/ingest`
- [ ] Embeddings dimension verified (`1536`)
- [ ] Retrieval verified with test query
- [ ] FastAPI running on port 8001
- [ ] Laravel running on port 8000
- [ ] Queue worker running (`php artisan queue:work`)
- [ ] Frontend running on port 5173
- [ ] PHPUnit tests passing (`php artisan test` $\rightarrow$ 29 passed)
- [ ] Pytest tests passing (`pytest` $\rightarrow$ 16 passed)
- [ ] Frontend build passing (`npm run build`)
- [ ] Evaluation harness verified (`python scripts/evaluate_rag.py`)
- [ ] Postman collection verified
- [ ] Security rules and ownership verified
