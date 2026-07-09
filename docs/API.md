# API Documentation

Base URL (local): `http://localhost:8000`. Interactive OpenAPI docs are
served at `/docs` (Swagger UI) and `/redoc` in `development`/`staging`; both
(along with `/openapi.json`) are disabled when `APP_ENV=production`.

## Authentication

`POST /generate-newsletter`, `GET /newsletter/latest`, and
`GET /newsletter/history` are protected by an `X-API-Key` header, checked
against the `API_AUTH_TOKEN` environment variable.

- If `API_AUTH_TOKEN` is **unset** (the default), auth is skipped entirely -
  convenient for local development and CI. This is only permitted when
  `APP_ENV` is `development` or `staging`; the app refuses to start with
  `APP_ENV=production` and an empty `API_AUTH_TOKEN`.
- If it **is** set, every request to a protected route must send
  `X-API-Key: <API_AUTH_TOKEN>` or receive `401 Unauthorized`. The comparison
  is constant-time (`secrets.compare_digest`).

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

**Request body** (optional):

```json
{ "requested_by": "power-automate-daily-trigger" }
```

**Response** — `200 OK`:

```json
{
  "subject": "OpenAI unveils new reasoning model | July 09, 2026",
  "summary": "Executive summary text...",
  "html": "<!DOCTYPE html>...",
  "markdown": "# OpenAI unveils new reasoning model...",
  "json": { "subject": "...", "sections": [ { "key": "global_news", "title": "🌍 Global AI News", "articles": [ /* ... */ ] } ] },
  "timestamp": "2026-07-09T08:00:12Z",
  "errors": []
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
| `errors` | array of strings | Non-fatal collector/generation errors from this run, if any. A non-empty list means the newsletter was still generated, just with fewer sources than usual (e.g. one collector's feed was down) - still a `200`, not a failure. |

A run typically takes 15-40 seconds depending on network latency across the
eight collector sources and, if a live LLM key is configured, GPT summary
latency. If the pipeline itself crashes, or produces no content at all
(a genuine bug, not just "no news today" - that case still returns `200`
with an empty-sections newsletter), the endpoint returns `502` instead of a
fabricated response.

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
| `422` | Invalid request body, or an out-of-range `limit` on `GET /newsletter/history` (must be 1-100) |
| `502` | The LangGraph pipeline crashed, or produced no content at all - see server logs |

## Example: curl

```bash
curl -X POST http://localhost:8000/generate-newsletter \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_AUTH_TOKEN" \
  -d '{}'
```
