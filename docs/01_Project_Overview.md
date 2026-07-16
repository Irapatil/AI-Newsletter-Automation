# Project Overview

## Business Problem

Staying current on developments across the AI industry — funding rounds,
model releases, research breakthroughs, hiring trends, open-source
activity, and policy changes — requires monitoring dozens of scattered
sources every day. Doing this manually is time-consuming, inconsistent,
and doesn't scale across a team. A simple RSS digest doesn't solve it
either: raw feeds contain heavy duplication (the same story reported by
five publishers), no relevance ranking, and no synthesis into an
executive-readable summary.

## Business Objective

Deliver a fully automated daily AI intelligence newsletter — collected,
deduplicated, ranked, and summarized without manual intervention — direct
to a distribution list's Outlook inbox every morning, with zero recurring
labor cost per edition once deployed.

## Solution Overview

AI Newsletter Automation is a multi-agent pipeline that:

1. Collects AI-related content from eight independent categories in
   parallel (global news, company announcements, funding, research,
   hiring, open source, policy, and model releases).
2. Merges, deduplicates (via semantic embedding similarity, not just exact
   text matches), and ranks the results across six weighted dimensions.
3. Uses GPT to generate an executive summary, per-article summaries, a
   subject line, and a "one thing to watch" highlight.
4. Renders the result as a production-ready HTML email, Markdown document,
   and structured JSON payload.
5. Delivers it via a Microsoft Power Automate flow through Office 365
   Outlook on a daily schedule, with real delivery-status feedback wired
   back into the platform.

The backend is a FastAPI service orchestrating a LangGraph workflow; the
frontend is a chat-first console for triggering, observing, and monitoring
the pipeline and its delivery pipeline.

## Key Features

| Feature | Description |
|---|---|
| Multi-agent collection | 8 parallel collector agents, each scoped to one content category and one set of sources |
| Semantic deduplication | Embedding-based cosine-similarity dedup, not just URL/title matching — catches the same story from different publishers |
| Multi-dimensional ranking | 6 weighted scoring dimensions (freshness, importance, business impact, source credibility, research impact, AI relevance) |
| GPT summarization | Executive summary, per-article summaries, subject line, and a highlighted "one thing to watch" |
| Multi-format output | HTML (email-ready), Markdown (Slack/Confluence/archival), and structured JSON |
| Full execution telemetry | Every pipeline run reports per-agent timing and item counts — no black-box runs |
| Real Outlook delivery tracking | Power Automate reports real delivery status back to the platform; the frontend reflects it live, never a hardcoded value |
| Resilient collection | A failing source never aborts the run — the pipeline degrades gracefully to a `partial_success` result |
| Interactive console | A chat-first frontend to trigger runs, watch execution progress, and review results without needing Swagger |

## Business Benefits

- **Zero recurring labor cost** — once deployed, the newsletter requires no
  manual curation, writing, or sending.
- **Consistency** — every edition follows the same collection, ranking, and
  summarization methodology; quality doesn't depend on who's available
  that day.
- **Speed to market on new sources** — adding a new collection category
  means adding one new agent, not redesigning the pipeline.
- **Auditability** — every run's statistics and per-agent execution report
  are available via the API, so a stakeholder can verify how any edition
  was assembled.
- **Low operating cost** — the LLM cost per run is in the low cents (GPT
  usage is limited to summarization of already-ranked, already-deduplicated
  content, not raw collection).

## End-to-End Workflow

```
Daily 8:00 AM trigger (Power Automate)
        │
        ▼
FastAPI receives POST /generate-newsletter
        │
        ▼
LangGraph orchestrates 8 parallel collector agents
        │
        ▼
Aggregation → Semantic Deduplication → Ranking
        │
        ▼
GPT generates the newsletter content
        │
        ▼
HTML / Markdown / JSON rendering
        │
        ▼
FastAPI returns the response to Power Automate
        │
        ▼
Power Automate sends the email via Office 365 Outlook
        │
        ▼
Power Automate reports delivery status back to the platform
        │
        ▼
Frontend reflects real delivery status automatically
```

## Expected Outcomes

- A daily newsletter delivered to the distribution list's inbox with no
  human involvement after initial deployment.
- A verifiable, inspectable pipeline — every run's collection counts,
  deduplication rate, ranking result, and per-agent timing are available
  via the API and visible in the console.
- A platform that degrades gracefully: a single failed data source reduces
  coverage for that run, never blocks the newsletter from going out.
- A foundation for the enhancements described in
  [`10_Future_Roadmap.md`](10_Future_Roadmap.md) — personalization,
  additional delivery channels, and expanded governance/analytics.
