# Troubleshooting

## The pipeline runs but the newsletter looks generic / summaries are just truncated text

You're on the mock LLM provider. Check `GET /health` — implicitly, or run:

```bash
python -c "from app.config.settings import get_settings; print(get_settings().uses_mock_llm)"
```

If `True`, set `OPENAI_API_KEY` (or `AZURE_OPENAI_API_KEY` +
`AZURE_OPENAI_ENDPOINT` + deployment names, with `LLM_PROVIDER=azure_openai`)
in `.env`. See [`ENVIRONMENT_VARIABLES.md`](ENVIRONMENT_VARIABLES.md).

## `POST /generate-newsletter` returns `401 Unauthorized`

This only happens when `APP_ENV=production` (auth is skipped entirely on
`development`/`staging`, regardless of whether `API_AUTH_TOKEN` is set - so
a leftover token in `.env` should never cause this locally). In production,
your request is missing (or has the wrong) `X-API-Key` header - send
`X-API-Key: <API_AUTH_TOKEN>`, or double-check `APP_ENV` if you didn't
intend to run as production.

## `GET /newsletter/latest` returns `404`

No newsletter has been generated yet in this environment. Call
`POST /generate-newsletter` first — history is filesystem-backed
(`NEWSLETTER_HISTORY_DIR`), so a fresh container/deploy starts empty.

## A collector agent logs warnings but the run still succeeds

This is expected and by design. Every collector agent
(`BaseCollectorAgent.collect()`) isolates its own exceptions — a single
broken RSS feed, a 404 from a misconfigured Greenhouse board token, or a
rate-limited API returns an empty list for that source and logs a
`*_fetch_failed` warning, rather than failing the whole pipeline. Check
`execution_logs` / `errors` in the API's underlying `GraphState`, or the
structured JSON logs, to see exactly which source degraded.

Common examples:
- `greenhouse_fetch_failed` for a board token that company doesn't actually
  use — update `GREENHOUSE_BOARD_TOKENS` to real board slugs for the
  companies you care about (find them at
  `https://boards.greenhouse.io/<token>`).
- `rss_feed_unavailable` for a publisher that changed or removed its RSS
  feed URL — update `app/config/sources.py:GLOBAL_NEWS_RSS_FEEDS`, or let it
  fall back to a Google News query the same way `Reuters AI`/`The Verge AI`
  already do.

## `ranked_news` (or the newsletter) is empty

Either every source returned zero fresh articles (check
`MAX_ARTICLE_AGE_HOURS` isn't too aggressive, and that outbound network
access isn't blocked), or every article was deduplicated away. The workflow
handles this gracefully via the `no_content_fallback` node/route — you'll
get a valid, well-formed "no major updates" newsletter rather than an error.

## Tests fail with network errors

They shouldn't — the test suite mocks all outbound HTTP via `respx` and
never calls a real LLM (it uses `MockLLMService`/monkeypatched settings). If
you see a real network call in a test failure, check that the test isn't
missing its `respx.mock` context or that a new service module bypasses
`app/services/http_client.py`.

## `pip install` fails with a numpy/langchain dependency conflict

`langchain==0.3.14` pins `numpy<2` on Python < 3.12. The project doesn't use
numpy directly (deduplication uses pure-Python cosine similarity in
`app/utils/text_utils.py`), so make sure you haven't reintroduced a `numpy`
line in `requirements.txt`.

## Docker container is unhealthy

The `HEALTHCHECK` in the `Dockerfile` hits `GET /health` inside the
container. If it's failing:
- Confirm the container actually started (`docker compose logs -f`) — a
  missing `.env` file (docker-compose's `env_file: .env` requires the file
  to exist) is the most common cause.
- Confirm `APP_PORT`/`APP_HOST` weren't overridden to something the
  healthcheck's hardcoded `localhost:8000` can't reach.

## Windows-specific: emoji/Unicode `UnicodeEncodeError` when printing to a terminal

This is a console-encoding issue (`cp1252`), not an application bug — the
generated HTML/Markdown content (section emoji, "👀 One Thing To Watch") is
valid UTF-8. Set `PYTHONIOENCODING=utf-8` before running a script that
prints newsletter content directly to a Windows terminal.
