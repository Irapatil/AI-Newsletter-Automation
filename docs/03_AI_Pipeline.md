# AI Pipeline — Detailed Walkthrough

This document traces one pipeline run end to end, step by step, from the
inbound API request to the rendered newsletter. It is the technical
companion to [`02_System_Architecture.md`](02_System_Architecture.md).

## Step 1 — API Request

A run starts with `POST /generate-newsletter` (the Power Automate
integration point) or `POST /demo/generate` (a lighter-weight companion
endpoint returning the same pipeline's results without the large inline
HTML). Both build an initial `GraphState` and invoke the compiled LangGraph
workflow (`app/graph/workflow.py`). Authentication (`X-API-Key`) is
enforced only when `APP_ENV=production`.

## Step 2 — LangGraph Orchestrator

The `Orchestrator` node is the graph's entry point. It performs no
collection itself — it exists purely to give the graph one well-defined
starting node with edges fanning out to all eight collector agents, which
LangGraph then executes concurrently within the same superstep.

## Step 3 — 8 Parallel AI Agents

Each collector agent inherits `BaseCollectorAgent` (`app/agents/base_agent.py`)
and is responsible for exactly one category and one dedicated `GraphState`
field:

| Agent | Category | Sources |
|---|---|---|
| **Global News Agent** | `global_news` | Publisher RSS (TechCrunch, VentureBeat, MIT Technology Review, The Verge, Reuters via Google News) + NewsAPI |
| **Company Agent** | `company_news` | Per-company Google News RSS (OpenAI, Anthropic, Microsoft AI, DeepMind, Meta AI, NVIDIA, Amazon AI, xAI) |
| **Funding Agent** | `funding` | Crunchbase API (if a key is configured), Google News fallback otherwise |
| **Research Agent** | `research` | arXiv API (`cs.AI`, `cs.LG`, `cs.CL`) |
| **Talent Agent** | `talent` | Greenhouse + Lever public job boards, LinkedIn provider (mock or API) |
| **Policy Agent** | `policy` | Google News RSS + NewsAPI (EU AI Act, India AI Mission, US AI Executive Orders) |
| **Open Source Agent** | `opensource` | GitHub Search API (trending) + Hugging Face Hub API |
| **Model Release Agent** | `model_releases` | Google News RSS per AI lab, new model-release announcements |

**Failure isolation**: `BaseCollectorAgent.collect()` wraps each agent's
`fetch()` call. If an agent raises, the exception is caught, logged, and
the agent contributes an empty article list plus an error message — it
never aborts the graph or the other seven agents. This is what allows the
pipeline to return `status: "partial_success"` (still a `200`, not a
failure) when one or more sources are unavailable.

**Freshness filtering**: every collected article is filtered against
`MAX_ARTICLE_AGE_HOURS` before being returned, so stale stories never enter
aggregation at all.

## Step 4 — Aggregation

The `AggregatorAgent` node runs once all eight collector edges have
completed (LangGraph's fan-in). It performs a straightforward merge — no
filtering or scoring — of all eight categories' article lists into one
combined list, annotated with `items_processed` for the execution report.

## Step 5 — Semantic Deduplication

The `DeduplicationAgent` removes near-duplicate stories — the same event
reported by multiple publishers — that a simple URL or title match would
miss.

**Embeddings**: each article's title + snippet is passed through the
configured LLM service's `embed_texts()` (OpenAI/Azure OpenAI embeddings,
or a deterministic hash-based mock for offline runs) to produce a
fixed-dimension vector representation.

**Cosine similarity**: articles are sorted freshest-first, then processed
greedily — an article is kept only if its cosine similarity to *every*
already-kept article is below `DEDUP_SIMILARITY_THRESHOLD` (default
`0.88`). Because the freshest copy is evaluated first, the most recent
report of a story is the one that survives when duplicates are found.

**Semantic search**, in this context, refers to this similarity-based
retrieval technique — comparing meaning-bearing vector representations
rather than exact text — as opposed to keyword or substring matching. The
same embedding representation is what would back a future "search past
newsletters by topic" feature (see
[`10_Future_Roadmap.md`](10_Future_Roadmap.md)).

## Step 6 — Ranking Engine

The `RankingAgent` scores every surviving article across six weighted
dimensions and keeps the top `RANKING_TOP_STORIES_PER_SECTION` per
category:

| Dimension | Default Weight | Methodology |
|---|---|---|
| Freshness | 0.20 | Linear decay over `MAX_ARTICLE_AGE_HOURS` |
| Importance | 0.25 | Keyword density (`breakthrough`, `unveils`, `milestone`, ...) |
| Business impact | 0.20 | Keyword density (`funding`, `acquisition`, `IPO`, ...) |
| Source credibility | 0.15 | Static per-publisher registry, with a category-aware default fallback |
| Research impact | 0.10 | Category-aware boost for `research`/`model_releases`, plus keyword density (`benchmark`, `sota`, ...) |
| AI relevance | 0.10 | Keyword density against a curated AI-terms list |

Each dimension is normalized to `[0, 1]` and combined via its configured
weight (`RANKING_WEIGHT_*` environment variables) into a single `total`
score per article. Weights are validated at startup to sum to
approximately `1.0`. `NewsletterGeneratorAgent` applies one further global
cap (`NEWSLETTER_MAX_TOTAL_ARTICLES`, default 24) so the rendered
newsletter stays to roughly two pages — this cap reserves each category's
top story first, so a single global cutoff can never erase an entire
section.

If ranking produces zero articles for a run (nothing cleared the
relevance bar), the graph conditionally routes to a `NoContentFallback`
node instead of the generator, producing a valid — if minimal — newsletter
rather than an error.

## Step 7 — LangChain Integration

The LLM abstraction layer (`app/services/llm_service.py`) uses **LangChain**
for its provider-agnostic chat and embeddings clients:

- **LLM Calls**: `ChatOpenAI` / `AzureChatOpenAI` (`langchain_openai`),
  invoked asynchronously via `.ainvoke()` with `SystemMessage`/`HumanMessage`
  (`langchain_core.messages`). This is what lets the same calling code work
  unmodified against OpenAI, Azure OpenAI, or a dependency-free mock
  implementation, selected automatically based on which credentials are
  configured.
- **Embeddings**: `OpenAIEmbeddings` / `AzureOpenAIEmbeddings`, used by the
  deduplication stage above.

**Prompt Templates**: prompts are plain Python string constants (one
system prompt per generation task — summary, executive summary, subject
line, "one thing to watch" — see `app/agents/newsletter_generator_agent.py`),
not LangChain `PromptTemplate` objects. This is a deliberate simplicity
choice: the prompts have no runtime-variable substitution beyond the
article text itself, so a templating layer would add indirection without
adding capability.

**Output Parser / Structured Output**: generation calls return plain text
(`generate_text() -> str`); there is no LangChain output-parser or
structured-output chain in this pipeline. Structuring happens in ordinary
Python: `NewsletterGeneratorAgent` assembles the returned strings directly
into the `NewsletterContent` Pydantic model (subject, executive summary,
per-section articles, "one thing to watch"). This keeps the mock LLM path
(used in tests, CI, and offline demos) trivially compatible with the real
path — both return a string, and both feed the same assembly code.

## Step 8 — GPT Newsletter Generation

`NewsletterGeneratorAgent` orchestrates four generation calls, the first
sequential and the remaining three concurrent:

1. **Per-article summaries** — each ranked article gets a 1-2 sentence
   factual summary (bounded concurrency, 5 in flight at a time).
2. **Executive Summary** — a 3-4 sentence synthesis across the day's top
   15 headlines, written for a C-suite audience.
3. **Subject line** — a compelling, under-90-character subject derived
   from the top story.
4. **Business Insights** ("one thing to watch") — a 2-sentence highlight
   of the single most important story for the reader to track going
   forward.

Every generation call uses a distinct, purpose-written system prompt (see
`app/agents/newsletter_generator_agent.py`) so tone and length are
controlled per output type rather than through one generic prompt.

## Step 9 — HTML Formatter

`HTMLFormatterAgent` renders the assembled `NewsletterContent` into three
parallel outputs: a Jinja2-templated HTML document (email-client-safe,
inline CSS, no external assets), a Markdown rendition (for Slack,
Confluence, or archival), and the structured JSON payload. All three are
returned in the same API response and persisted to history.

## Step 10 — Power Automate

A Microsoft Power Automate cloud flow triggers the pipeline on a daily
schedule via `POST /generate-newsletter`, parses the JSON response, and
composes the email body from `newsletter_html`. See
[`07_Deployment_Guide.md`](07_Deployment_Guide.md) and
[`../docs/POWER_AUTOMATE.md`](POWER_AUTOMATE.md) for the exact flow
configuration, including retry policy and failure handling.

## Step 11 — Outlook Delivery

The flow's final action, **Outlook: Send an email (V2)**, delivers the
composed HTML to the configured distribution list. Immediately afterward,
the flow calls back to `POST /integration/outlook/status` with the real
delivery outcome (`delivered` or `failed`), which the frontend polls and
reflects live — there is no simulated or hardcoded delivery state anywhere
in this path.

## End-to-End Execution Report

Every node in the graph is wrapped with a stopwatch that appends one
`AgentExecutionRecord` (node name, status, execution time, items processed)
to the response's `agent_execution` field on successful completion — a
complete, per-node execution report for every run, with zero effect on
routing, retries, or agent logic. A raising node's exception still
propagates untouched, so this instrumentation can never mask a real
failure.
