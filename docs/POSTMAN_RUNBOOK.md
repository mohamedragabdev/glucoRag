# Postman API Execution Runbook
## Medical RAG System — Type 2 Diabetes Screening API

This runbook guides you through testing the entire API lifecycle of the Medical RAG System using Postman.
Import the collection file from [`docs/POSTMAN_COLLECTION.json`](file:///home/mohamed/github/MRAG/docs/POSTMAN_COLLECTION.json) or execute each request manually using the specifications below.

---

## Postman Environment Variables

Set up a Postman Environment with the following variables:

| Variable | Initial Value | Description |
|---|---|---|
| `base_url` | `http://localhost:8000/api` | Laravel Backend API base URL |
| `rag_service_url` | `http://localhost:8001` | FastAPI RAG Service base URL |
| `token` | *(leave empty)* | Automatically set after Register/Login |
| `conversation_id` | *(leave empty)* | Automatically set after Create Conversation |
| `assistant_message_id` | *(leave empty)* | Automatically set after Send Message |
| `internal_secret` | `dev_internal_secret_change_in_prod` | Secret header for direct FastAPI debugging |

---

## Complete API Execution Sequence

### Request 1: Clinician Registration
- **Method:** `POST`
- **Endpoint:** `{{base_url}}/register`
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body (raw JSON):**
```json
{
  "name": "Dr. Sarah Jenkins",
  "email": "sarah.jenkins@clinic.org",
  "password": "securepassword123",
  "password_confirmation": "securepassword123"
}
```
- **Expected Status:** `201 Created`
- **Postman Test Script (auto-sets token):**
```javascript
var data = pm.response.json();
if (data.token) {
    pm.collectionVariables.set("token", data.token);
}
```
- **Expected Response Shape:**
```json
{
  "user": {
    "id": 1,
    "name": "Dr. Sarah Jenkins",
    "email": "sarah.jenkins@clinic.org",
    "created_at": "2026-08-19T14:00:00.000000Z"
  },
  "token": "1|abcdef123456..."
}
```

---

### Request 2: Clinician Login
- **Method:** `POST`
- **Endpoint:** `{{base_url}}/login`
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body (raw JSON):**
```json
{
  "email": "sarah.jenkins@clinic.org",
  "password": "securepassword123"
}
```
- **Expected Status:** `200 OK`
- **Postman Test Script:**
```javascript
var data = pm.response.json();
if (data.token) {
    pm.collectionVariables.set("token", data.token);
}
```
- **Expected Response Shape:**
```json
{
  "user": {
    "id": 1,
    "name": "Dr. Sarah Jenkins",
    "email": "sarah.jenkins@clinic.org",
    "created_at": "2026-08-19T14:00:00.000000Z"
  },
  "token": "2|fedcba654321..."
}
```

---

### Request 3: Get Authenticated User
- **Method:** `GET`
- **Endpoint:** `{{base_url}}/user`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Accept: application/json`
- **Body:** None
- **Expected Status:** `200 OK`
- **Expected Response Shape:**
```json
{
  "user": {
    "id": 1,
    "name": "Dr. Sarah Jenkins",
    "email": "sarah.jenkins@clinic.org",
    "created_at": "2026-08-19T14:00:00.000000Z",
    "updated_at": "2026-08-19T14:00:00.000000Z"
  }
}
```

---

### Request 4: Create Conversation
- **Method:** `POST`
- **Endpoint:** `{{base_url}}/conversations`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body (raw JSON):**
```json
{
  "title": "ADA Universal Screening Inquiries"
}
```
- **Expected Status:** `201 Created`
- **Postman Test Script (auto-sets conversation_id):**
```javascript
var data = pm.response.json();
if (data.data && data.data.id) {
    pm.collectionVariables.set("conversation_id", data.data.id);
}
```
- **Expected Response Shape:**
```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "ADA Universal Screening Inquiries",
    "created_at": "2026-08-19T14:02:00.000000Z",
    "updated_at": "2026-08-19T14:02:00.000000Z"
  }
}
```

---

### Request 5: Send Question (Asynchronous RAG Dispatch)
- **Method:** `POST`
- **Endpoint:** `{{base_url}}/conversations/{{conversation_id}}/messages`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Body (raw JSON):**
```json
{
  "content": "What is the recommended universal screening age for Type 2 Diabetes according to ADA guidelines?"
}
```
- **Expected Status:** `202 Accepted`
- **Postman Test Script (auto-sets assistant_message_id):**
```javascript
var data = pm.response.json();
if (data.data && data.data.assistant_message) {
    pm.collectionVariables.set("assistant_message_id", data.data.assistant_message.id);
}
```
- **Expected Response Shape:**
```json
{
  "data": {
    "user_message": {
      "id": 101,
      "conversation_id": 1,
      "role": "user",
      "content": "What is the recommended universal screening age for Type 2 Diabetes according to ADA guidelines?",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-08-19T14:03:00.000000Z"
    },
    "assistant_message": {
      "id": 102,
      "conversation_id": 1,
      "role": "assistant",
      "content": null,
      "status": "pending",
      "error_message": null,
      "created_at": "2026-08-19T14:03:00.000000Z"
    }
  }
}
```

---

### Request 6: Poll Single Message Status (Pending $\rightarrow$ Completed)
- **Method:** `GET`
- **Endpoint:** `{{base_url}}/messages/{{assistant_message_id}}`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Accept: application/json`
- **Expected Status:** `200 OK`
- **Expected Response Shape (When Pending):**
```json
{
  "data": {
    "id": 102,
    "conversation_id": 1,
    "role": "assistant",
    "content": null,
    "status": "pending",
    "error_message": null,
    "created_at": "2026-08-19T14:03:00.000000Z",
    "updated_at": "2026-08-19T14:03:00.000000Z",
    "citations": []
  }
}
```
- **Expected Response Shape (When Completed with Citations):**
```json
{
  "data": {
    "id": 102,
    "conversation_id": 1,
    "role": "assistant",
    "content": "According to the American Diabetes Association (ADA) Standards of Care, universal screening for prediabetes and type 2 diabetes should begin at age 35 for all asymptomatic adults regardless of risk factors.",
    "status": "completed",
    "error_message": null,
    "created_at": "2026-08-19T14:03:00.000000Z",
    "updated_at": "2026-08-19T14:03:02.000000Z",
    "citations": [
      {
        "id": 501,
        "message_id": 102,
        "document_id": "ada_standards_of_care_2024",
        "chunk_id": "ada_standards_of_care_2024_p5_c1",
        "source_title": "ADA Standards of Care in Diabetes 2024",
        "page_number": 5,
        "similarity_score": 0.9421,
        "created_at": "2026-08-19T14:03:02.000000Z"
      }
    ]
  }
}
```

---

### Request 7: Get Conversation Details
- **Method:** `GET`
- **Endpoint:** `{{base_url}}/conversations/{{conversation_id}}`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Accept: application/json`
- **Expected Status:** `200 OK`
- **Expected Response Shape:**
```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "title": "What is the recommended universal...",
    "created_at": "2026-08-19T14:02:00.000000Z",
    "updated_at": "2026-08-19T14:03:02.000000Z",
    "messages": [ ... ]
  }
}
```

---

### Request 8: List Conversation Messages
- **Method:** `GET`
- **Endpoint:** `{{base_url}}/conversations/{{conversation_id}}/messages`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Accept: application/json`
- **Expected Status:** `200 OK`
- **Expected Response Shape:**
```json
{
  "data": [
    {
      "id": 101,
      "conversation_id": 1,
      "role": "user",
      "content": "What is the recommended universal screening age for Type 2 Diabetes according to ADA guidelines?",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-08-19T14:03:00.000000Z",
      "citations": []
    },
    {
      "id": 102,
      "conversation_id": 1,
      "role": "assistant",
      "content": "According to the American Diabetes Association (ADA)...",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-08-19T14:03:00.000000Z",
      "citations": [ ... ]
    }
  ]
}
```

---

### Request 9: Logout
- **Method:** `POST`
- **Endpoint:** `{{base_url}}/logout`
- **Headers:**
  - `Authorization: Bearer {{token}}`
  - `Accept: application/json`
- **Expected Status:** `204 No Content`

---

## Negative & Security Test Cases

| Scenario | Request | Expected Status | Reason |
|---|---|---|---|
| **Unauthenticated Request** | `GET {{base_url}}/conversations` without `Authorization` header | `401 Unauthorized` | Protected by `auth:sanctum` |
| **Empty Question** | `POST {{base_url}}/conversations/1/messages` with `{"content": ""}` | `422 Unprocessable Entity` | Validation requires min 1 character |
| **Oversized Question** | `POST {{base_url}}/conversations/1/messages` with 2001 chars | `422 Unprocessable Entity` | Validation bounds question at max 2000 chars |
| **Cross-User Conversation Access** | `GET {{base_url}}/conversations/2` with user 1 token | `403 Forbidden` | Enforced by `EnsureConversationOwnership` middleware |
| **Direct FastAPI without Secret** | `POST {{rag_service_url}}/rag/query` without secret header | `401 Unauthorized` | Enforced by `verify_internal_secret` |
| **Direct FastAPI with Invalid Secret** | `POST {{rag_service_url}}/rag/query` with wrong secret | `401 Unauthorized` | Constant-time secret mismatch |
