# Environment Variables

Copy `.env.example` to `.env` and fill in real values. Every external
integration has a mock or free fallback, so the app runs end-to-end even
with an empty `.env` — see [`app/config/settings.py`](../app/config/settings.py)
for the authoritative defaults.

## Application

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` \| `staging` \| `production` |
| `APP_HOST` | `0.0.0.0` | Bind host for uvicorn |
| `APP_PORT` | `8000` | Bind port for uvicorn |
| `LOG_LEVEL` | `INFO` | Python logging level. In `development`, logs render as human-readable colorized text; otherwise as JSON. |
| `API_AUTH_TOKEN` | *(empty)* | Shared secret required as `X-API-Key` on protected routes. Empty disables auth on `development`/`staging`. **Required when `APP_ENV=production`** - the app refuses to start otherwise. Stored as `SecretStr` (masked in logs). |
| `ALLOWED_HOSTS` | `*` | Comma-separated `Host` header allowlist (`TrustedHostMiddleware`). Set to your real domain(s) in production. |

## LLM Provider

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` \| `azure_openai` \| `mock` |
| `OPENAI_API_KEY` | *(empty)* | Required to use the OpenAI provider (falls back to `mock` if empty). Stored as `SecretStr`. |
| `OPENAI_MODEL` | `gpt-4o` | Chat model for summarization. Set to your available GPT-5 deployment name if you have one. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model used for deduplication |
| `AZURE_OPENAI_API_KEY` | *(empty)* | Required to use the Azure OpenAI provider. Stored as `SecretStr`. |
| `AZURE_OPENAI_ENDPOINT` | *(empty)* | e.g. `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_VERSION` | `2024-08-01-preview` | Azure OpenAI REST API version |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | *(empty)* | Azure deployment name for chat. Required (along with the embedding deployment, key, and endpoint) for the Azure provider to be considered configured. |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | *(empty)* | Azure deployment name for embeddings |

If no key is configured for the selected provider, `LLMService` falls back
to `MockLLMService` automatically (deterministic summaries + hash-based
embeddings) so the pipeline, tests, and CI never require a live API key.

## News Source Providers (all optional)

| Variable | Default | Used by |
|---|---|---|
| `NEWSAPI_API_KEY` | *(empty)* | `GlobalNewsAgent`, `PolicyAgent` (supplementary source). Stored as `SecretStr`. |
| `GITHUB_TOKEN` | *(empty)* | `OpenSourceAgent` (raises GitHub Search rate limit 60 -> 5000 req/hr). Stored as `SecretStr`. |
| `CRUNCHBASE_API_KEY` | *(empty)* | `FundingAgent` (uses Google News fallback if empty; real Crunchbase calls are a POST per API v4). Stored as `SecretStr`. |
| `GREENHOUSE_BOARD_TOKENS` | `stripe,airbnb,openai` | `TalentAgent` (comma-separated Greenhouse board tokens) |
| `LEVER_COMPANY_SLUGS` | `netflix,palantir` | `TalentAgent` (comma-separated Lever company slugs) |
| `LINKEDIN_JOBS_PROVIDER` | `mock` | `mock` \| `api` (LinkedIn has no public jobs API; `api` requires a partner integration you implement) |
| `LINKEDIN_API_KEY` | *(empty)* | Only used when `LINKEDIN_JOBS_PROVIDER=api`. Stored as `SecretStr`. |

## Deduplication & Ranking

| Variable | Default | Description |
|---|---|---|
| `DEDUP_SIMILARITY_THRESHOLD` | `0.88` | Cosine similarity above which two articles are treated as duplicates |
| `RANKING_TOP_STORIES_PER_SECTION` | `5` | Max articles kept per category after ranking. Must be >= 1. |
| `RANKING_WEIGHT_FRESHNESS` | `0.20` | Weight for the freshness dimension |
| `RANKING_WEIGHT_IMPORTANCE` | `0.25` | Weight for the importance dimension |
| `RANKING_WEIGHT_BUSINESS_IMPACT` | `0.20` | Weight for the business-impact dimension |
| `RANKING_WEIGHT_SOURCE_CREDIBILITY` | `0.15` | Weight for the source-credibility dimension |
| `RANKING_WEIGHT_RESEARCH_IMPACT` | `0.10` | Weight for the research-impact dimension |
| `RANKING_WEIGHT_AI_RELEVANCE` | `0.10` | Weight for the AI-relevance dimension |

Each weight must be within `[0.0, 1.0]`, and all six must sum to ~1.0
(±0.01) - `Settings` validates this at startup and refuses to load
otherwise, since a non-normalized set of weights would silently skew every
article's ranking score.

## Newsletter

| Variable | Default | Description |
|---|---|---|
| `NEWSLETTER_TIMEZONE` | `UTC` | Display timezone (informational; timestamps are stored in UTC) |
| `NEWSLETTER_SENDER_NAME` | `AI Newsletter Automation` | Shown in the HTML header and Markdown footer |
| `NEWSLETTER_HISTORY_DIR` | `data/history` | Filesystem directory for persisted newsletter JSON |
| `MAX_ARTICLE_AGE_HOURS` | `48` | Articles older than this are dropped by every collector agent. Must be >= 1. |
| `NEWSLETTER_MAX_TOTAL_ARTICLES` | `24` | Hard cap on total articles across all sections (keeps the newsletter ~2 pages) |

## HTTP / Networking

| Variable | Default | Description |
|---|---|---|
| `HTTP_TIMEOUT_SECONDS` | `15` | Per-request timeout for all outbound HTTP calls |
| `HTTP_MAX_RETRIES` | `3` | Retry attempts (exponential backoff) for transient HTTP failures (5xx / network errors only - 4xx responses never retry). Must be >= 1. |
