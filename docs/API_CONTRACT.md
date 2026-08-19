# API Contract — Medical RAG System (Type 2 Diabetes Screening)

## 1. Authentication & Security

- **Authentication Method:** Laravel Sanctum Bearer Tokens.
- **Client Base URL:** `http://localhost:8000/api`
- **Protected Endpoints:** Require HTTP header `Authorization: Bearer <token>`.
- **Internal Service Authentication (Laravel -> FastAPI):** Header `X-Internal-Secret: <secret>`.

---

## 2. Public Authentication Endpoints

### `POST /api/register`
Creates a new clinician account and issues a Sanctum token.

- **Request Body:**
```json
{
  "name": "Dr. Jane Smith",
  "email": "jane.smith@clinic.org",
  "password": "securepassword123",
  "password_confirmation": "securepassword123"
}
```
- **Response `201 Created`:**
```json
{
  "user": {
    "id": 1,
    "name": "Dr. Jane Smith",
    "email": "jane.smith@clinic.org",
    "created_at": "2026-08-19T12:00:00.000000Z"
  },
  "token": "1|abcdef123456..."
}
```
- **Errors:** `422 Unprocessable Entity` (validation failure).

---

### `POST /api/login`
Authenticates a clinician and issues a token.

- **Request Body:**
```json
{
  "email": "jane.smith@clinic.org",
  "password": "securepassword123"
}
```
- **Response `200 OK`:**
```json
{
  "user": {
    "id": 1,
    "name": "Dr. Jane Smith",
    "email": "jane.smith@clinic.org",
    "created_at": "2026-08-19T12:00:00.000000Z"
  },
  "token": "2|fedcba654321..."
}
```
- **Errors:** `422 Unprocessable Entity` (invalid credentials).

---

### `POST /api/logout`
Revokes the current access token.

- **Headers:** `Authorization: Bearer <token>`
- **Response `204 No Content`**
- **Errors:** `401 Unauthorized`.

---

## 3. Conversations Endpoints

### `GET /api/conversations`
Lists the authenticated clinician's conversations ordered by `updated_at` desc.

- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:**
```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "title": "ADA Universal Screening Thresholds",
      "created_at": "2026-08-19T12:00:00.000000Z",
      "updated_at": "2026-08-19T12:05:00.000000Z"
    }
  ]
}
```

---

### `POST /api/conversations`
Creates a new conversation.

- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
```json
{
  "title": "T2D Screening in Asymptomatic Adults"
}
```
- **Response `201 Created`:**
```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "T2D Screening in Asymptomatic Adults",
    "created_at": "2026-08-19T12:00:00.000000Z",
    "updated_at": "2026-08-19T12:00:00.000000Z"
  }
}
```

---

### `GET /api/conversations/{id}`
Retrieves a single conversation owned by the authenticated clinician, including its messages and citations.

- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:**
```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "T2D Screening in Asymptomatic Adults",
    "created_at": "2026-08-19T12:00:00.000000Z",
    "updated_at": "2026-08-19T12:05:00.000000Z",
    "messages": [ ... ]
  }
}
```
- **Errors:** `403 Forbidden` (if not owner), `404 Not Found`.

---

### `DELETE /api/conversations/{id}`
Deletes a conversation and cascades to its messages and citations.

- **Headers:** `Authorization: Bearer <token>`
- **Response `204 No Content`**
- **Errors:** `403 Forbidden`, `404 Not Found`.

---

## 4. Messages Endpoints

### `GET /api/conversations/{id}/messages`
Lists all messages in a conversation in chronological order.

- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:**
```json
{
  "data": [
    {
      "id": 101,
      "conversation_id": 1,
      "role": "user",
      "content": "What is the recommended universal screening age for T2D according to ADA?",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-08-19T12:01:00.000000Z",
      "citations": []
    },
    {
      "id": 102,
      "conversation_id": 1,
      "role": "assistant",
      "content": "The American Diabetes Association (ADA) recommends that universal screening for type 2 diabetes begin at age 35 for all asymptomatic adults.",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-08-19T12:01:02.000000Z",
      "citations": [
        {
          "id": 501,
          "message_id": 102,
          "document_id": "ada_standards_2024",
          "chunk_id": "ada_standards_2024_p5_c1",
          "source_title": "ADA Standards of Medical Care in Diabetes 2024",
          "page_number": 5,
          "similarity_score": 0.9421,
          "created_at": "2026-08-19T12:01:02.000000Z"
        }
      ]
    }
  ]
}
```

---

### `POST /api/conversations/{id}/messages`
Submits a screening question, persists the user message (`status=completed`), persists a pending assistant message placeholder (`status=pending`), dispatches the asynchronous queue worker, and returns `202 Accepted`.

- **Headers:** `Authorization: Bearer <token>`
- **Rate Limit:** 20 requests/minute per user.
- **Request Body:**
```json
{
  "content": "What are the cutoff criteria for fasting plasma glucose in screening?"
}
```
- **Response `202 Accepted`:**
```json
{
  "data": {
    "user_message": {
      "id": 103,
      "conversation_id": 1,
      "role": "user",
      "content": "What are the cutoff criteria for fasting plasma glucose in screening?",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-08-19T12:05:00.000000Z",
      "citations": []
    },
    "assistant_message": {
      "id": 104,
      "conversation_id": 1,
      "role": "assistant",
      "content": null,
      "status": "pending",
      "error_message": null,
      "created_at": "2026-08-19T12:05:00.000000Z",
      "citations": []
    }
  }
}
```

---

### `GET /api/messages/{id}`
Polls the processing status of an individual message.

- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:**
```json
{
  "data": {
    "id": 104,
    "conversation_id": 1,
    "role": "assistant",
    "content": "Fasting Plasma Glucose (FPG) screening cutoff values are: Normal: < 100 mg/dL; Prediabetes: 100–125 mg/dL; Diabetes screening threshold: ≥ 126 mg/dL.",
    "status": "completed",
    "error_message": null,
    "created_at": "2026-08-19T12:05:00.000000Z",
    "updated_at": "2026-08-19T12:05:03.000000Z",
    "citations": [ ... ]
  }
}
```

---

## 5. Internal FastAPI RAG Endpoints (Service-to-Service)

### `GET /health`
Public liveness probe.
- **Response `200 OK`:** `{"status": "ok"}`

### `POST /rag/query`
Internal RAG execution.
- **Headers:** `X-Internal-Secret: <secret>`
- **Request Body:**
```json
{
  "question": "What is the recommended universal screening age?",
  "conversation_history": [
    { "role": "user", "content": "Prior message" }
  ],
  "request_id": "c42f5391-1541-4124-a16d-4e8af7182cf5"
}
```
- **Response `200 OK`:**
```json
{
  "request_id": "c42f5391-1541-4124-a16d-4e8af7182cf5",
  "status": "answered",
  "answer": "Universal screening begins at age 35 for all asymptomatic adults.",
  "confidence": "high",
  "safety_status": "in_scope",
  "model": "openai/gpt-4o-mini",
  "citations": [
    {
      "chunk_id": "ada_2024_p5_c1",
      "document_id": "ada_2024",
      "title": "ADA Standards of Care 2024",
      "page_number": 5,
      "similarity_score": 0.9421
    }
  ]
}
```
