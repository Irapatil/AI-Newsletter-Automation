# API Documentation

Base URL (local): `http://localhost:8000`. Interactive OpenAPI docs are
served at `/docs` (Swagger UI) and `/redoc` in `development`/`staging`; both
(along with `/openapi.json`) are disabled when `APP_ENV=production`.

Endpoints are grouped into four Swagger tags: **System**, **Health**,
**Newsletter**, and **Demo**. Every response model below carries a
realistic example, visible directly in Swagger's "Example Value" tab for
each endpoint - no need to actually run a request to see the expected
shape.

## Authentication

`POST /generate-newsletter`, `GET /newsletter/latest`,
`GET /newsletter/latest/html`, `GET /newsletter/history`, and
`POST /demo/generate` are protected by an `X-API-Key` header, checked
against the `API_AUTH_TOKEN` environment variable.

- If `API_AUTH_TOKEN` is **unset** (the default), auth is skipped entirely -
  convenient for local development, CI, and interview demos. This is only
  permitted when `APP_ENV` is `development` or `staging`; the app refuses to
  start with `APP_ENV=production` and an empty `API_AUTH_TOKEN`.
- If it **is** set, every request to a protected route must send
  `X-API-Key: <API_AUTH_TOKEN>` or receive `401 Unauthorized`. The comparison
  is constant-time (`secrets.compare_digest`).

`GET /` and `GET /health` are always public (used for infra health checks).

## Endpoints

### `GET /` — System

Returns basic service metadata.

```json
{
  "name": "AI Newsletter Automation",
  "version": "1.0.0",
  "description": "Enterprise multi-agent AI newsletter pipeline built with LangGraph and FastAPI.",
  "docs_url": "/docs"
}
```

### `GET /health` — Health

Liveness/readiness probe, plus a call-free, per-integration status summary
(no outbound network calls are made - this reads already-loaded settings and
confirms the LangGraph workflow compiles, it does not verify each provider
is actually reachable).

```json
{
  "status": "ok",
  "timestamp": "2026-07-10T06:00:00Z",
  "version": "1.0.0",
  "providers": {
    "api": "ok",
    "openai": "configured",
    "newsapi": "configured",
    "github": "authenticated",
    "rss": "available",
    "langgraph": "operational"
  }
}
```

| Provider | Possible values | Meaning |
|---|---|---|
| `api` | `ok` | The endpoint responded |
| `openai` | `configured` \| `mock` | Real key present vs. falling back to `MockLLMService` |
| `newsapi` | `configured` \| `not_configured` | Optional supplemental source |
| `github` | `authenticated` \| `public` | Whether `GITHUB_TOKEN` raises the Search API rate limit |
| `rss` | `available` | RSS/Atom collection needs no credentials |
| `langgraph` | `operational` \| `error` | Whether the compiled `StateGraph` built without raising |

### `POST /generate-newsletter` — Newsletter

Runs the complete LangGraph pipeline end-to-end - Orchestrator -> 8 parallel
collector agents -> Aggregator -> semantic Deduplication -> Ranking ->
Newsletter Generator (GPT summarization) -> HTML Formatter - and persists
the result to history. This is the endpoint Power Automate's daily trigger
calls; the response feeds directly into the Outlook "Send an email" action
(see [`POWER_AUTOMATE.md`](POWER_AUTOMATE.md)).

**Request body** (optional):

```json
{ "requested_by": "power-automate-daily-trigger" }
```

**Response** — `200 OK`:

```json
{
  "subject": "OpenAI unveils new reasoning model | July 10, 2026",
  "summary": "OpenAI announced a new reasoning-focused model; three AI startups raised over $500M combined; and the EU published new AI Act guidance for foundation models.",
  "generated_at": "2026-07-10T08:00:12Z",
  "execution_time_seconds": 42.7,
  "newsletter_html": "<!DOCTYPE html><html>...</html>",
  "newsletter_markdown": "# OpenAI unveils new reasoning model...",
  "newsletter_json": { "subject": "...", "sections": [ { "key": "global_news", "title": "🌍 Global AI News", "articles": [ /* ... */ ] } ] },
  "statistics": {
    "aggregated_count": 1298,
    "duplicates_removed": 192,
    "ranked_count": 40,
    "stories_selected": 24
  },
  "sources_used": ["TechCrunch AI", "VentureBeat AI", "arXiv", "GitHub Trending", "..."],
  "agent_execution": [
    { "node": "Orchestrator", "status": "success", "execution_time_seconds": 0.0, "items_processed": 8 },
    { "node": "GlobalNewsAgent", "status": "success", "execution_time_seconds": 4.21, "items_processed": 160 },
    { "node": "DeduplicationAgent", "status": "success", "execution_time_seconds": 8.44, "items_processed": 1106 },
    { "node": "NewsletterGeneratorAgent", "status": "success", "execution_time_seconds": 11.36, "items_processed": 24 }
  ],
  "provider": "openai",
  "status": "success",
  "token_usage": { "prompt_and_completion_tokens": 18420, "is_estimated": true },
  "estimated_cost_usd": 0.0461,
  "errors": []
}
```

| Field | Type | Description |
|---|---|---|
| `subject` | string | Suggested email subject line |
| `summary` | string | Executive summary (3-4 sentences) |
| `generated_at` | string (ISO-8601) | Generation timestamp (UTC) |
| `execution_time_seconds` | number | Wall-clock time for the full LangGraph run |
| `newsletter_html` | string | Full HTML email body |
| `newsletter_markdown` | string | Markdown rendition (for Slack/archival/SharePoint) |
| `newsletter_json` | object | Structured `NewsletterContent` payload (sections, articles, scores) |
| `statistics` | object | `aggregated_count` (raw articles collected across all 8 agents), `duplicates_removed` (by semantic dedup), `ranked_count` (post-ranking candidates), `stories_selected` (final articles in the newsletter) |
| `sources_used` | array of strings | Distinct publisher/API source names that contributed at least one article |
| `agent_execution` | array of objects | One entry per LangGraph node, in execution order: `node`, `status`, `execution_time_seconds`, `items_processed` - the full workflow execution report (see [PART 3 example below](#langgraph-execution-report)) |
| `provider` | string | Effective LLM provider for this run: `openai` \| `azure_openai` \| `mock` |
| `status` | string | `success` \| `partial_success` (one or more collectors failed, but the pipeline still produced a newsletter from the remaining sources - still a `200`, not a failure) |
| `token_usage` | object | `prompt_and_completion_tokens`, `is_estimated` - a character-based heuristic (~4 chars/token), since there is no real usage/billing API to query |
| `estimated_cost_usd` | number | Rough cost estimate for this run's LLM usage (`LLM_COST_PER_MILLION_TOKENS_USD` \* tokens / 1,000,000) - not real billing data |
| `errors` | array of strings | Non-fatal collector/generation errors from this run, if any |

A run typically takes 15-40 seconds depending on network latency across the
eight collector sources and, if a live LLM key is configured, GPT summary
latency. If the pipeline itself crashes, or produces no content at all
(a genuine bug, not just "no news today" - that case still returns `200`
with an empty-sections newsletter), the endpoint returns `502` instead of a
fabricated response.

#### LangGraph execution report

`agent_execution` always contains exactly one entry per node that actually
ran, in graph order:

```
Orchestrator → GlobalNewsAgent → CompanyNewsAgent → FundingAgent →
ResearchAgent → TalentAgent → PolicyAgent → OpenSourceAgent →
ModelReleaseAgent → AggregatorAgent → DeduplicationAgent → RankingAgent →
NewsletterGeneratorAgent → HTMLFormatterAgent
```

(the 8 collector agents run in parallel, so their relative order in the
array reflects completion order, not a fixed sequence). If the pipeline hit
the "no significant news" fallback instead of generating content, you'll see
a `NoContentFallback` entry in place of `NewsletterGeneratorAgent`.

### `GET /newsletter/latest` — Newsletter

Returns the most recently generated newsletter (same shape as the
`generate-newsletter` response, read from persisted history rather than
triggering a new run). `404` if none has been generated yet.

### `GET /newsletter/latest/html` — Newsletter

Returns the latest newsletter's HTML **directly** (`Content-Type: text/html`),
not wrapped in a JSON envelope. Open
`http://localhost:8000/newsletter/latest/html` in a browser to see the
rendered email exactly as Outlook would display it. `404` (JSON error body)
if none has been generated yet.

### `GET /newsletter/history` — Newsletter

Returns metadata for past editions, newest first.

Query params: `limit` (default `20`, range `1`-`100`).

```json
{
  "items": [
    { "id": "4ea3ed0a3f7f", "subject": "OpenAI unveils new reasoning model | July 10, 2026", "timestamp": "2026-07-10T08:00:12Z" }
  ],
  "count": 1
}
```

Only the single latest edition's full content is retrievable
(`GET /newsletter/latest`) - there is no per-edition detail endpoint.

### `POST /demo/generate` — Demo

Runs the exact same LangGraph pipeline as `POST /generate-newsletter` (same
persistence to history), but returns a smaller, Swagger-friendly payload:
everything from the full response **except** `newsletter_html` and
`newsletter_json` (the large payloads), plus an `html_preview_url` pointing
at `GET /newsletter/latest/html`. Built for live interview walkthroughs -
`POST /generate-newsletter` remains the integration point for Power
Automate.

```json
{
  "subject": "OpenAI unveils new reasoning model | July 10, 2026",
  "generated_at": "2026-07-10T08:00:12Z",
  "execution_time_seconds": 42.7,
  "provider": "openai",
  "status": "success",
  "statistics": { "aggregated_count": 1298, "duplicates_removed": 192, "ranked_count": 40, "stories_selected": 24 },
  "sources_used": ["TechCrunch AI", "arXiv", "..."],
  "agent_execution": [ /* same shape as generate-newsletter, above */ ],
  "token_usage": { "prompt_and_completion_tokens": 18420, "is_estimated": true },
  "estimated_cost_usd": 0.0461,
  "newsletter_markdown": "# OpenAI unveils new reasoning model...",
  "html_preview_url": "/newsletter/latest/html",
  "errors": []
}
```

## Error responses

| Status | When |
|---|---|
| `401` | Missing/incorrect `X-API-Key` when `API_AUTH_TOKEN` is set |
| `404` | `GET /newsletter/latest`(`/html`) called before any newsletter exists |
| `422` | Invalid request body, or an out-of-range `limit` on `GET /newsletter/history` (must be 1-100) |
| `502` | The LangGraph pipeline crashed, or produced no content at all - see server logs |

## Example: curl

```bash
# Trigger generation (Power Automate's integration point)
curl -X POST http://localhost:8000/generate-newsletter \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_AUTH_TOKEN" \
  -d '{}'

# Interview demo: compact report + link to the rendered HTML
curl -X POST http://localhost:8000/demo/generate -H "X-API-Key: $API_AUTH_TOKEN"

# View the rendered newsletter in a browser
open http://localhost:8000/newsletter/latest/html
```
