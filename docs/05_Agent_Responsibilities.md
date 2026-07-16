# Agent Responsibilities

Every agent below is a node in the compiled LangGraph `StateGraph`
(`app/graph/workflow.py`). The eight collector agents run in parallel; the
remaining five run sequentially after fan-in.

---

## Global News Agent

- **Responsibilities**: Collects general AI industry news from major tech
  publishers and broad search.
- **Inputs**: None (reads configuration only — no upstream graph state).
- **Outputs**: `global_news: list[Article]` — publisher-sourced articles
  tagged `NewsCategory.GLOBAL`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()` — an
  exception yields an empty list plus a logged error; the run continues.
- **Dependencies**: Publisher RSS feeds (TechCrunch, VentureBeat, MIT
  Technology Review, The Verge, Reuters via Google News), NewsAPI.

## Company Agent

- **Responsibilities**: Tracks announcements from specific AI companies.
- **Inputs**: None.
- **Outputs**: `company_news: list[Article]` tagged `NewsCategory.COMPANY`.
- **Failure Handling**: Same per-agent isolation as above; per-company feed
  failures within the agent are further isolated via `gather_isolated()` so
  one company's feed failing doesn't drop the others.
- **Dependencies**: Per-company Google News RSS (OpenAI, Anthropic,
  Microsoft AI, DeepMind, Meta AI, NVIDIA, Amazon AI, xAI).

## Funding Agent

- **Responsibilities**: Tracks AI startup funding rounds and investment
  activity.
- **Inputs**: None.
- **Outputs**: `funding: list[Article]` tagged `NewsCategory.FUNDING`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()`; if
  Crunchbase is unavailable or unconfigured, falls back to a Google News
  provider automatically rather than failing.
- **Dependencies**: Crunchbase API (if `CRUNCHBASE_API_KEY` configured),
  Google News fallback (`app/services/funding_provider.py`).

## Research Agent

- **Responsibilities**: Surfaces significant AI/ML research publications.
- **Inputs**: None.
- **Outputs**: `research: list[Article]` tagged `NewsCategory.RESEARCH`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()`.
- **Dependencies**: arXiv API (`cs.AI`, `cs.LG`, `cs.CL` categories).

## Talent Agent

- **Responsibilities**: Tracks AI hiring trends and notable job postings.
- **Inputs**: None.
- **Outputs**: `talent: list[Article]` tagged `NewsCategory.TALENT`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()`;
  per-board failures isolated individually via `gather_isolated()`.
- **Dependencies**: Greenhouse + Lever public job board APIs, LinkedIn
  provider (mock by default; pluggable for a licensed API — see
  [`10_Future_Roadmap.md`](10_Future_Roadmap.md)).

## Policy Agent

- **Responsibilities**: Tracks AI regulation and government policy
  developments.
- **Inputs**: None.
- **Outputs**: `policy: list[Article]` tagged `NewsCategory.POLICY`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()`.
- **Dependencies**: Google News RSS + NewsAPI (EU AI Act, India AI Mission,
  US AI Executive Orders).

## Open Source Agent

- **Responsibilities**: Tracks trending open-source AI projects and model
  releases on developer platforms.
- **Inputs**: None.
- **Outputs**: `opensource: list[Article]` tagged `NewsCategory.OPENSOURCE`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()`.
- **Dependencies**: GitHub Search API (trending repositories), Hugging
  Face Hub API.

## Model Release Agent

- **Responsibilities**: Tracks new foundation/frontier model announcements
  per AI lab.
- **Inputs**: None.
- **Outputs**: `model_releases: list[Article]` tagged
  `NewsCategory.MODEL_RELEASE`.
- **Failure Handling**: Isolated by `BaseCollectorAgent.collect()`.
- **Dependencies**: Google News RSS, scoped per AI lab.

---

## Aggregator Agent

- **Responsibilities**: Fan-in merge of all eight collectors' output into
  a single article list; no filtering or scoring performed here.
- **Inputs**: `global_news`, `company_news`, `funding`, `research`,
  `talent`, `policy`, `opensource`, `model_releases` (all eight collector
  state keys).
- **Outputs**: `aggregated_articles: list[Article]`.
- **Failure Handling**: Runs only once every collector edge has completed
  (LangGraph fan-in); has no external dependencies to fail against.
- **Dependencies**: None (pure in-process merge).

## Deduplication Agent

- **Responsibilities**: Removes near-duplicate stories reported by
  multiple publishers via semantic similarity, not just exact-text
  matching.
- **Inputs**: `aggregated_articles: list[Article]`.
- **Outputs**: `deduplicated_articles: list[Article]` — freshest surviving
  copy of each distinct story.
- **Failure Handling**: A graph-level `RetryPolicy` is attached to this
  node (it calls the LLM service's embeddings endpoint directly); a
  persistent failure propagates as a `502` to the caller rather than
  silently producing an empty result, since a broken dedup stage would
  otherwise corrupt every downstream stage.
- **Dependencies**: LLM service `embed_texts()` (OpenAI/Azure OpenAI
  Embeddings, or the deterministic mock).

## Ranking Agent

- **Responsibilities**: Scores every de-duplicated article across six
  weighted dimensions and selects the top stories per category.
- **Inputs**: `deduplicated_articles: list[Article]`.
- **Outputs**: `ranked_news: list[Article]`, each with a populated
  `scores` object (freshness, importance, business impact, source
  credibility, research impact, AI relevance, total).
- **Failure Handling**: Pure in-process scoring — no external calls, so
  no network failure mode. Routes to `NoContentFallback` (via conditional
  edge) if the result is empty.
- **Dependencies**: `app/config/sources.py` static source-credibility
  registry; `RANKING_WEIGHT_*` settings.

## Newsletter Generator Agent

- **Responsibilities**: Produces the executive summary, per-article
  summaries, subject line, and "one thing to watch" highlight; assembles
  the structured `NewsletterContent`.
- **Inputs**: `ranked_news: list[Article]`.
- **Outputs**: `newsletter_content: NewsletterContent` (subject, executive
  summary, sections of summarized articles, "one thing to watch").
- **Failure Handling**: A graph-level `RetryPolicy` is attached to this
  node (it calls the LLM service directly for generation); a persistent
  failure propagates as a `502` rather than returning a partially-written
  newsletter.
- **Dependencies**: LLM service `generate_text()` (OpenAI/Azure OpenAI
  GPT, or the deterministic mock).

## HTML Formatter Agent

- **Responsibilities**: Renders the final HTML, Markdown, and JSON
  representations of the newsletter.
- **Inputs**: `newsletter_content: NewsletterContent`.
- **Outputs**: `newsletter_html: str`, `newsletter_markdown: str`,
  `newsletter_json: dict`.
- **Failure Handling**: Pure in-process templating — no external calls.
  A raised exception here propagates as a `502`, since a formatting bug
  would otherwise silently deliver an empty or malformed email.
- **Dependencies**: Jinja2 (HTML template), markdown2 (Markdown
  rendition).

---

## No-Content Fallback (routing node, not a collector)

- **Responsibilities**: Produces a valid, minimal `NewsletterContent` when
  `RankingAgent` returns zero articles for a run (e.g. an unusually quiet
  news day), so the pipeline still completes successfully instead of
  erroring.
- **Inputs**: Graph state at the post-ranking decision point.
- **Outputs**: `newsletter_content: NewsletterContent` with placeholder-free,
  honest copy indicating no significant stories were detected.
- **Failure Handling**: Pure in-process; no external dependencies.
- **Dependencies**: None.
