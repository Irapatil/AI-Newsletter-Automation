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
| `LOG_LEVEL` | `INFO` | Python logging level |
| `API_AUTH_TOKEN` | *(empty)* | Shared secret required as `X-API-Key` on protected routes. Empty disables auth. |

## LLM Provider

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` \| `azure_openai` \| `mock` |
| `OPENAI_API_KEY` | *(empty)* | Required to use the OpenAI provider (falls back to `mock` if empty) |
| `OPENAI_MODEL` | `gpt-4o` | Chat model for summarization. Set to your available GPT-5 deployment name if you have one. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model used for deduplication |
| `AZURE_OPENAI_API_KEY` | *(empty)* | Required to use the Azure OpenAI provider |
| `AZURE_OPENAI_ENDPOINT` | *(empty)* | e.g. `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_VERSION` | `2024-08-01-preview` | Azure OpenAI REST API version |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | *(empty)* | Azure deployment name for chat |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | *(empty)* | Azure deployment name for embeddings |

If no key is configured for the selected provider, `LLMService` falls back
to `MockLLMService` automatically (deterministic summaries + hash-based
embeddings) so the pipeline, tests, and CI never require a live API key.

## News Source Providers (all optional)

| Variable | Default | Used by |
|---|---|---|
| `NEWSAPI_API_KEY` | *(empty)* | `GlobalNewsAgent`, `PolicyAgent` (supplementary source) |
| `GITHUB_TOKEN` | *(empty)* | `OpenSourceAgent` (raises GitHub Search rate limit 60 -> 5000 req/hr) |
| `CRUNCHBASE_API_KEY` | *(empty)* | `FundingAgent` (uses Google News fallback if empty) |
| `GREENHOUSE_BOARD_TOKENS` | `stripe,airbnb,openai` | `TalentAgent` (comma-separated Greenhouse board tokens) |
| `LEVER_COMPANY_SLUGS` | `netflix,palantir` | `TalentAgent` (comma-separated Lever company slugs) |
| `LINKEDIN_JOBS_PROVIDER` | `mock` | `mock` \| `api` (LinkedIn has no public jobs API; `api` requires a partner integration you implement) |
| `LINKEDIN_API_KEY` | *(empty)* | Only used when `LINKEDIN_JOBS_PROVIDER=api` |

## Deduplication & Ranking

| Variable | Default | Description |
|---|---|---|
| `DEDUP_SIMILARITY_THRESHOLD` | `0.88` | Cosine similarity above which two articles are treated as duplicates |
| `RANKING_TOP_STORIES_PER_SECTION` | `5` | Max articles kept per category after ranking |
| `RANKING_WEIGHT_FRESHNESS` | `0.20` | Weight for the freshness dimension |
| `RANKING_WEIGHT_IMPORTANCE` | `0.25` | Weight for the importance dimension |
| `RANKING_WEIGHT_BUSINESS_IMPACT` | `0.20` | Weight for the business-impact dimension |
| `RANKING_WEIGHT_SOURCE_CREDIBILITY` | `0.15` | Weight for the source-credibility dimension |
| `RANKING_WEIGHT_RESEARCH_IMPACT` | `0.10` | Weight for the research-impact dimension |
| `RANKING_WEIGHT_AI_RELEVANCE` | `0.10` | Weight for the AI-relevance dimension |

Weights do not need to sum to 1.0; they're applied as a weighted sum over
each `[0, 1]`-normalized dimension score.

## Newsletter

| Variable | Default | Description |
|---|---|---|
| `NEWSLETTER_TIMEZONE` | `UTC` | Display timezone (informational; timestamps are stored in UTC) |
| `NEWSLETTER_SENDER_NAME` | `AI Newsletter Automation` | Shown in the HTML header and Markdown footer |
| `NEWSLETTER_HISTORY_DIR` | `data/history` | Filesystem directory for persisted newsletter JSON |
| `MAX_ARTICLE_AGE_HOURS` | `48` | Articles older than this are dropped by every collector agent |
| `NEWSLETTER_MAX_TOTAL_ARTICLES` | `24` | Hard cap on total articles across all sections (keeps the newsletter ~2 pages) |

## HTTP / Networking

| Variable | Default | Description |
|---|---|---|
| `HTTP_TIMEOUT_SECONDS` | `15` | Per-request timeout for all outbound HTTP calls |
| `HTTP_MAX_RETRIES` | `3` | Retry attempts (exponential backoff) for transient HTTP failures |
