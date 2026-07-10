# Interview Demo Guide

A complete, no-frontend demonstration of Enterprise AI Newsletter Automation:
FastAPI + Swagger UI, LangGraph, and (optionally) Microsoft Power Automate +
Outlook. Everything below was verified against a running instance of this
exact codebase.

## The 5-minute demo

```
1. uvicorn app.main:app --reload
2. Open http://localhost:8000/docs
3. Execute POST /demo/generate
4. Point out the LangGraph execution report + statistics in the response
5. Open http://localhost:8000/newsletter/latest/html — the rendered newsletter
6. (Optional) Show the Power Automate flow
7. (Optional) Show the resulting Outlook email
```

No frontend, no build step, no browser extension - Swagger IS the demo
surface.

---

## 1. Architecture

```
Microsoft Power Automate (daily 8AM trigger)
        │  HTTP POST
        ▼
FastAPI  ──►  LangGraph StateGraph  ──►  Persisted history (JSON)
        │
        ▼
JSON response  ──►  Parse JSON  ──►  Outlook: Send an email
```

- **FastAPI** exposes 7 endpoints across 4 tags (System, Health, Newsletter,
  Demo) - see [`docs/API.md`](docs/API.md) for the full reference.
- **LangGraph** runs a compiled `StateGraph`: one Orchestrator node fans out
  to 8 parallel collector agents, which fan back in at an Aggregator, then
  flow sequentially through Deduplication → Ranking → Newsletter Generator →
  HTML Formatter. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the
  full diagram and design rationale (why LangGraph over an AutoGen-style
  conversational-agent framework).
- **No frontend.** Swagger's "Try it out" plus a browser tab for
  `/newsletter/latest/html` are the entire demo surface.

## 2. Workflow

```
START
  │
  ▼
Orchestrator
  │
  ├──► Global News Agent ─────┐
  ├──► Company Agent ─────────┤
  ├──► Funding Agent ─────────┤
  ├──► Research Agent ────────┼──► Aggregator
  ├──► Talent Agent ──────────┤
  ├──► Policy Agent ──────────┤
  ├──► Open Source Agent ─────┤
  └──► Model Release Agent ───┘
                                     │
                                     ▼
                          Semantic Deduplication
                                     │
                                     ▼
                                 Ranking
                                     │
                        ┌────────────┴────────────┐
                   (articles found)          (nothing cleared the bar)
                        │                          │
                        ▼                          ▼
            Newsletter Generator          NoContentFallback
                        │                          │
                        └────────────┬─────────────┘
                                     ▼
                             HTML Formatter
                                     │
                                     ▼
                                    END
```

The 8 collector agents run **in parallel** (LangGraph's fan-out/fan-in),
not sequentially - the `agent_execution` report in every response shows
each one's actual wall-clock time, which typically overlap rather than sum.

## 3. Agent Responsibilities

| Agent | Responsibility | Real source(s) |
|---|---|---|
| `GlobalNewsAgent` | Global AI industry news | TechCrunch, VentureBeat, MIT Tech Review, The Verge, Reuters (RSS/Google News) + NewsAPI |
| `CompanyNewsAgent` | Per-company moves | Google News RSS, scoped to OpenAI/Anthropic/Microsoft/DeepMind/Meta/NVIDIA/Amazon/xAI |
| `FundingAgent` | Investment rounds | Crunchbase API v4 (if key present) or Google News fallback |
| `ResearchAgent` | Academic research | arXiv API (`cs.AI`, `cs.LG`, `cs.CL`) |
| `TalentAgent` | Hiring trends | Greenhouse + Lever public job boards, LinkedIn (mock or partner API) |
| `PolicyAgent` | Regulation | Google News RSS + NewsAPI (EU AI Act, India AI Mission, US Executive Orders) |
| `OpenSourceAgent` | OSS releases | GitHub Search API (trending) + Hugging Face Hub API |
| `ModelReleaseAgent` | New model announcements | Google News RSS, one query per major lab |
| `AggregatorAgent` | Merges all 8 collector outputs into one list | - |
| `DeduplicationAgent` | Embedding cosine-similarity near-duplicate removal | - |
| `RankingAgent` | 6-dimension weighted scoring, top-N per section | - |
| `NewsletterGeneratorAgent` | GPT per-article summaries, executive summary, subject, "one thing to watch" | - |
| `HTMLFormatterAgent` | Renders HTML, Markdown, and JSON | - |

## 4. Execution Flow (what actually happens on a request)

1. Power Automate (or Swagger, or curl) calls `POST /generate-newsletter`
   (or `POST /demo/generate` for the compact demo variant).
2. FastAPI invokes the cached, compiled LangGraph workflow
   (`get_compiled_workflow()` - compiled once per process, not per request).
3. All 8 collector agents run concurrently; each is wrapped by
   `BaseCollectorAgent.collect()`, which isolates that agent's own failures
   (one broken RSS feed never aborts the run) and drops stale articles.
4. Aggregator merges everything into one list; Deduplication embeds each
   article and drops near-duplicates (cosine similarity ≥ `DEDUP_SIMILARITY_THRESHOLD`);
   Ranking scores and keeps the top N per category.
5. If any articles survived, Newsletter Generator summarizes each one via
   the configured LLM (real OpenAI/Azure OpenAI, or a deterministic mock if
   no key is configured) and writes the executive summary/subject/"one
   thing to watch". Otherwise, `NoContentFallback` produces a graceful
   "no major updates today" edition.
6. HTML Formatter renders the final HTML/Markdown/JSON.
7. The API persists the result to `data/history/` and returns the full
   response - including a per-node `agent_execution` report and estimated
   token/cost figures.

## 5. API Walkthrough

| Endpoint | Tag | Purpose |
|---|---|---|
| `GET /` | System | Service identity |
| `GET /health` | Health | Liveness + per-integration config status |
| `POST /generate-newsletter` | Newsletter | The production trigger (what Power Automate calls) |
| `GET /newsletter/latest` | Newsletter | Re-read the latest edition as JSON |
| `GET /newsletter/latest/html` | Newsletter | **Open this in a browser** to see the rendered newsletter |
| `GET /newsletter/history` | Newsletter | List past editions (metadata only) |
| `POST /demo/generate` | Demo | Same pipeline, compact response - built for this walkthrough |

Full request/response schemas, every field explained: [`docs/API.md`](docs/API.md).

## 6. Swagger Demo Steps

1. `uvicorn app.main:app --reload`
2. Open `http://localhost:8000/docs`.
3. Expand **Demo → POST /demo/generate**, click **Try it out → Execute**.
   - Takes 15-40 seconds (real network calls to 8+ live sources).
4. In the response body, walk through:
   - `agent_execution` - the full LangGraph execution report: every node,
     its status, timing, and items processed, in the order things actually
     completed.
   - `statistics` - articles aggregated → duplicates removed → ranked →
     selected, showing the funnel.
   - `sources_used` - which real publishers/APIs contributed this run.
   - `provider` / `token_usage` / `estimated_cost_usd` - what actually
     generated the content, and a transparent cost estimate.
5. Copy `html_preview_url` (or just navigate to `/newsletter/latest/html`)
   and open it in a new tab - the fully rendered, professionally styled
   newsletter, exactly as Outlook would display it.
6. Optionally, expand **Health → GET /health** to show the per-integration
   status grid, and **Newsletter → GET /newsletter/history** to show
   persisted runs.

Every response model in Swagger has a populated **Example Value** tab, so
even without executing a request, the schema alone tells the whole story.

## 7. Power Automate Demo

See [`docs/POWER_AUTOMATE.md`](docs/POWER_AUTOMATE.md) for the complete
flow build (Recurrence trigger → HTTP → Parse JSON → Compose → Outlook Send
Email → optional SharePoint archive), including the exact Parse JSON
schema and field-by-field mapping.

**Talking point:** the API contract didn't just happen to work with Power
Automate - `POST /generate-newsletter` returns `newsletter_html` as a plain
string specifically so a "Compose" step (or the Outlook action directly)
can consume it with zero transformation, and `status: "partial_success"`
lets the flow branch (e.g. CC an ops mailbox) without treating a
degraded-but-real newsletter as a hard failure.

## 8. Outlook Demo

After running the Power Automate flow (or a manual "Test" run), show the
delivered email: professional inline-styled HTML, sender name from
`NEWSLETTER_SENDER_NAME`, subject line generated by
`NewsletterGeneratorAgent`. If you don't have a live Power Automate
environment handy, `GET /newsletter/latest/html` in a browser is the same
HTML Outlook would render.

---

## 9. Interview Talking Points

- **Why LangGraph, not AutoGen/CrewAI?** This is a deterministic ETL
  pipeline with a fixed step order and fan-out/fan-in shape known at compile
  time - not an open-ended agent negotiation. `StateGraph` gives typed shared
  state, real parallel execution, and inspectable routing for free; a
  conversational-agent framework would add non-determinism this pipeline
  doesn't need or want.
- **Per-agent failure isolation.** Every collector agent's `collect()` wraps
  its own fetch in a try/except - one broken RSS feed or rate-limited API
  never aborts the run. `status: "partial_success"` in the response
  surfaces this instead of hiding it.
- **The `agent_execution` report is real instrumentation, not a mock.**
  It's a stopwatch wrapped around each node's actual call, added without
  touching a single agent's internals - a live demonstration of adding
  observability to an existing system without a rewrite.
- **Semantic deduplication, not string matching.** The same story covered
  by five publishers collapses to one entry via embedding cosine similarity,
  keeping the freshest copy.
- **Six-dimension ranking is fully transparent and configurable** -
  freshness, importance, business impact, source credibility, research
  impact, AI relevance - each a documented, unit-tested heuristic, with
  weights as environment variables that must sum to ~1.0 (validated at
  startup).
- **Everything runs with zero API keys.** Every external integration
  (OpenAI, NewsAPI, GitHub, Crunchbase, LinkedIn) has a mock or free
  fallback, so the full pipeline - and the test suite - runs end-to-end
  before a single credential is configured.
- **`token_usage`/`estimated_cost_usd` are honestly labeled estimates.**
  There's no real OpenAI usage/billing API being queried; the response says
  so explicitly (`is_estimated: true`) rather than presenting a heuristic as
  fact.

## 10. Common Questions and Expected Answers

**Q: What happens if the OpenAI API is down or rate-limited?**
A: `POST /generate-newsletter` returns `502` with a clean error body -
the pipeline doesn't fabricate a fake "success" response. This was verified
live: hitting a real `insufficient_quota` error from OpenAI produced exactly
this behavior in testing, not a silent 200 with empty content.

**Q: What if one news source is temporarily unavailable?**
A: That single collector agent's `collect()` catches the failure, logs it,
and returns an empty list for just that source - the other 7 continue
normally. The response comes back `200` with `status: "partial_success"`
and the specific error(s) listed in `errors`.

**Q: How is deduplication actually implemented?**
A: Each article's title + snippet is embedded (via the configured LLM
service - real or mock), sorted freshest-first, and greedily kept only if
its cosine similarity to every already-kept article is below
`DEDUP_SIMILARITY_THRESHOLD` (default 0.88). See
`app/agents/deduplication_agent.py`.

**Q: Why is there both `POST /generate-newsletter` and `POST /demo/generate`?**
A: Same pipeline, different response shape. `/generate-newsletter` returns
the full payload (including the large inline HTML) because Power Automate
needs the actual content to email. `/demo/generate` omits that in favor of
a link to `/newsletter/latest/html`, so the interview-demo response stays
readable directly in Swagger.

**Q: Is the LangGraph execution report real, or simulated for the demo?**
A: Real. Every node in `app/graph/nodes.py` is timed with
`time.monotonic()` around its actual call; nothing is faked or delayed
artificially. Re-running the same request will show different timings
based on actual network/LLM latency that run.

**Q: How would you scale this?** A: The pipeline runs once/day (or on
manual trigger) and takes 15-40 seconds - horizontal scaling isn't the
bottleneck today. If daily volume or trigger frequency grew significantly,
the natural next steps are: a shared `httpx.AsyncClient` across a single
run (currently each service opens its own), LangGraph checkpointing for
resumable runs, and moving history persistence from local JSON files to a
real datastore for multi-instance deployments - all called out in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

**Q: What's not production-ready yet?**
A: See "Remaining optional improvements" in the project README - honestly,
the main gap is that this hasn't been deployed/load-tested outside local
Docker, and Docker itself should be verified by you (`docker compose up`)
since it couldn't be executed in the authoring environment.
