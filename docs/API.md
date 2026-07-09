# API Documentation

Base URL (local): `http://localhost:8000`. Interactive OpenAPI docs are
served at `/docs` (Swagger UI) and `/redoc` whenever the app is running.

## Authentication

`POST /generate-newsletter`, `GET /newsletter/latest`, and
`GET /newsletter/history` are protected by an `X-API-Key` header, checked
against the `API_AUTH_TOKEN` environment variable.

- If `API_AUTH_TOKEN` is **unset** (the default), auth is skipped entirely -
  convenient for local development and CI.
- If it **is** set, every request to a protected route must send
  `X-API-Key: <API_AUTH_TOKEN>` or receive `401 Unauthorized`.

`GET /` and `GET /health` are always public (used for infra health checks).

## Endpoints

### `GET /`

Returns basic service metadata.

```json
{
  "name": "AI Newsletter Automation",
  "version": "1.0.0",
  "description": "Enterprise multi-agent AI newsletter pipeline built with LangGraph and FastAPI.",
  "docs_url": "/docs"
}
```

### `GET /health`

Liveness/readiness probe.

```json
{ "status": "ok", "timestamp": "2026-07-09T06:00:00Z", "version": "1.0.0" }
```

### `POST /generate-newsletter`

Runs the full LangGraph pipeline end-to-end (collection -> dedup -> ranking
-> GPT summarization -> rendering) and persists the result to history. This
is the endpoint Power Automate's daily trigger calls.

**Request body** (optional; both fields are optional):

```json
{ "force_refresh": false, "requested_by": "power-automate-daily-trigger" }
```

**Response** — `200 OK`:

```json
{
  "subject": "OpenAI unveils new reasoning model | July 09, 2026",
  "summary": "Executive summary text...",
  "html": "<!DOCTYPE html>...",
  "markdown": "# OpenAI unveils new reasoning model...",
  "json": { "subject": "...", "sections": [ { "key": "global_news", "title": "🌍 Global AI News", "articles": [ /* ... */ ] } ] },
  "timestamp": "2026-07-09T08:00:12Z"
}
```

| Field | Type | Description |
|---|---|---|
| `subject` | string | Suggested email subject line |
| `summary` | string | Executive summary (3-4 sentences) |
| `html` | string | Full HTML email body |
| `markdown` | string | Markdown rendition (for Slack/archival/SharePoint) |
| `json` | object | Structured `NewsletterContent` payload (sections, articles, scores) |
| `timestamp` | string (ISO-8601) | Generation time (UTC) |

A run typically takes 15-40 seconds depending on network latency across the
eight collector sources and, if a live LLM key is configured, GPT summary
latency.

### `GET /newsletter/latest`

Returns the most recently generated newsletter (same shape as the
`generate-newsletter` response). `404` if none has been generated yet.

### `GET /newsletter/history`

Returns a paginated list of past newsletters.

Query params: `limit` (default `20`).

```json
{
  "items": [
    { "id": "4ea3ed0a3f7f", "subject": "...", "timestamp": "2026-07-09T08:00:12Z" }
  ],
  "count": 1
}
```

## Error responses

| Status | When |
|---|---|
| `401` | Missing/incorrect `X-API-Key` when `API_AUTH_TOKEN` is set |
| `404` | `GET /newsletter/latest` called before any newsletter exists |
| `422` | Invalid request body on `POST /generate-newsletter` |

## Example: curl

```bash
curl -X POST http://localhost:8000/generate-newsletter \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_AUTH_TOKEN" \
  -d '{}'
```
