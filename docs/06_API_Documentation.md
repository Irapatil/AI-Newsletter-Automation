# API Documentation

Base URL (local): `http://localhost:8000`. Interactive Swagger UI is
served at `/docs` and ReDoc at `/redoc` in `development`/`staging`; both
(along with `/openapi.json`) are disabled when `APP_ENV=production`. Full
field-level schemas and error responses are in
[`API.md`](API.md) — this document is the client-facing summary.

Authentication: `X-API-Key` is required on all endpoints below marked
**Protected**, but only when `APP_ENV=production`. In development/staging
it is not enforced, so local testing and Swagger's "Try it out" never need
a key configured.

---

### `GET /`

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/` |
| **Auth** | Public |
| **Request** | None |
| **Response** | `{ "name": "AI Newsletter Automation", "version": "1.0.0", "description": "...", "docs_url": "/docs" }` |

> 📸 *Swagger screenshot placeholder: `GET /` response in Swagger UI.*

---

### `GET /health`

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/health` |
| **Auth** | Public |
| **Request** | None |
| **Response** | `{ "status": "ok", "timestamp": "...", "version": "1.0.0", "providers": { "api": "ok", "openai": "configured", "newsapi": "configured", "github": "authenticated", "rss": "available", "langgraph": "operational" } }` |

A call-free, per-integration configuration check — no outbound calls are
made to any provider.

> 📸 *Swagger screenshot placeholder: `GET /health` response in Swagger UI.*

---

### `POST /generate-newsletter`

| | |
|---|---|
| **Method** | `POST` |
| **Endpoint** | `/generate-newsletter` |
| **Auth** | Protected |
| **Request** | `{ "requested_by": "power-automate-daily-trigger" }` (optional body; empty `{}` accepted) |
| **Response** | Full newsletter payload — `subject`, `summary`, `newsletter_html`, `newsletter_markdown`, `newsletter_json`, `statistics`, `sources_used`, `agent_execution`, `provider`, `status`, `token_usage`, `estimated_cost_usd`, `errors` |

This is the Power Automate integration point — runs the complete LangGraph
pipeline and persists the result to history.

> 📸 *Swagger screenshot placeholder: `POST /generate-newsletter` request/response in Swagger UI.*

---

### `GET /newsletter/latest`

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/newsletter/latest` |
| **Auth** | Protected |
| **Request** | None |
| **Response** | Same shape as `POST /generate-newsletter`, read from persisted history (`404` if none exists yet) |

> 📸 *Swagger screenshot placeholder: `GET /newsletter/latest` response in Swagger UI.*

---

### `GET /newsletter/latest/html`

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/newsletter/latest/html` |
| **Auth** | Protected |
| **Request** | None |
| **Response** | Raw `text/html` — the rendered newsletter, viewable directly in a browser |

> 📸 *Swagger screenshot placeholder: `GET /newsletter/latest/html` rendered output.*

---

### `GET /newsletter/history`

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/newsletter/history?limit=20` |
| **Auth** | Protected |
| **Request** | Query parameter `limit` (1-100, default 20) |
| **Response** | `{ "items": [ { "id": "...", "subject": "...", "timestamp": "..." } ], "count": N }` — metadata only, newest first |

> 📸 *Swagger screenshot placeholder: `GET /newsletter/history` response in Swagger UI.*

---

### `POST /demo/generate`

| | |
|---|---|
| **Method** | `POST` |
| **Endpoint** | `/demo/generate` |
| **Auth** | Protected |
| **Request** | None |
| **Response** | Same pipeline run as `POST /generate-newsletter`, without the large inline HTML — includes `html_preview_url` pointing at `GET /newsletter/latest/html` |

Functionally identical to `POST /generate-newsletter` (same LangGraph
pipeline, same persistence); built for the Copilot console and live
walkthroughs so the response stays readable directly in Swagger.

> 📸 *Swagger screenshot placeholder: `POST /demo/generate` response in Swagger UI.*

---

### `POST /integration/outlook/status`

| | |
|---|---|
| **Method** | `POST` |
| **Endpoint** | `/integration/outlook/status` |
| **Auth** | Protected |
| **Request** | `{ "status": "delivered", "timestamp": "2026-07-15T08:01:32Z", "message_id": "flow-run-id", "recipient_count": 42 }` |
| **Response** | `{ "delivery_status": "delivered", "last_delivery_time": "2026-07-15T08:01:32Z", "message_id": "flow-run-id", "recipient_count": 42 }` |

Called by the Power Automate flow immediately after its "Send an email
(V2)" action completes or fails — see
[`POWER_AUTOMATE.md`](POWER_AUTOMATE.md) for the flow configuration.

> 📸 *Swagger screenshot placeholder: `POST /integration/outlook/status` request/response in Swagger UI.*

---

### `GET /integration/outlook/status`

| | |
|---|---|
| **Method** | `GET` |
| **Endpoint** | `/integration/outlook/status` |
| **Auth** | Public |
| **Request** | None |
| **Response** | `{ "delivery_status": "pending", "last_delivery_time": null, "message_id": null, "recipient_count": null }` until the first real callback arrives, then reflects the last reported delivery |

Polled by the frontend every 30 seconds so the console's Outlook delivery
status is always real, never hardcoded.

> 📸 *Swagger screenshot placeholder: `GET /integration/outlook/status` response in Swagger UI.*

---

## Error Responses (all endpoints)

| Status | Meaning |
|---|---|
| `401` | Missing/incorrect `X-API-Key` — only possible when `APP_ENV=production` |
| `404` | Requested resource does not exist yet (e.g. no newsletter generated) |
| `422` | Invalid request body or query parameter |
| `502` | The LangGraph pipeline crashed or produced no content — see server logs |
