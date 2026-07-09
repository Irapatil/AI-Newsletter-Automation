# Deployment Guide

## 1. Local (Python venv)

```bash
git clone https://github.com/Irapatil/AI-Newsletter-Automation.git
cd AI-Newsletter-Automation

python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate

pip install -r requirements-dev.txt   # or requirements.txt for a runtime-only install
cp .env.example .env                  # fill in real values, or leave as-is for mock mode

make run       # or: uvicorn app.main:app --host 0.0.0.0 --port 8000
make dev       # auto-reload variant, for local development
```

The app is fully functional with an unmodified `.env.example` copy: no
external API key is required to exercise the full LangGraph pipeline (LLM
calls fall back to a deterministic mock, and every news source either needs
no key or degrades gracefully to a free fallback).

## 2. Docker

```bash
cp .env.example .env   # docker-compose reads this file
make docker-build
make docker-up
make docker-logs
```

This builds a slim, non-root `python:3.11-slim` image
([`Dockerfile`](../Dockerfile)) and runs it via
[`docker-compose.yml`](../docker-compose.yml), with:

- `data/history` and `logs` bind-mounted for persistence across container restarts.
- A container `HEALTHCHECK` hitting `GET /health` every 30s.
- Environment variables loaded from `.env` (values already present in the
  container's environment, e.g. from your orchestrator's secret manager,
  take precedence).

To stop: `make docker-down`.

## 3. Cloud deployment (reference patterns)

The app is a stateless FastAPI service (state lives only in
`NEWSLETTER_HISTORY_DIR`), so it fits any container platform:

- **Azure Container Apps / App Service** - natural fit given the Azure
  OpenAI and Power Automate integration; mount `data/history` to Azure Files
  if you need history to survive redeploys, or point
  `NEWSLETTER_HISTORY_DIR` at a mounted volume/blob-backed path.
- **AWS ECS / Fargate** - run the same image behind an ALB; use Secrets
  Manager for `OPENAI_API_KEY` / `API_AUTH_TOKEN`.
- **Kubernetes** - the provided `HEALTHCHECK` maps directly to a liveness
  probe hitting `/health`; use a `Secret` for the `.env` values and a
  `PersistentVolumeClaim` for `NEWSLETTER_HISTORY_DIR` if history durability
  matters.

In all cases, only `POST /generate-newsletter` needs to be reachable by
Power Automate (over HTTPS, with `API_AUTH_TOKEN` set) - it does not need to
be publicly exposed beyond that.

## 4. Secrets

Never commit `.env`. In production, set `API_AUTH_TOKEN` to a long random
value (e.g. `openssl rand -hex 32`) and store it, alongside
`OPENAI_API_KEY`/`AZURE_OPENAI_API_KEY`, in your platform's secret manager
rather than a plain file.

## 5. Scheduling

The pipeline itself has no built-in scheduler - it is triggered externally
by Microsoft Power Automate's daily recurrence trigger (see
[`POWER_AUTOMATE.md`](POWER_AUTOMATE.md)). If you need a scheduler
independent of Power Automate (e.g. for a staging environment), a simple
cron/Task Scheduler entry calling the CLI works too:

```bash
python scripts/generate_newsletter_cli.py --output-dir newsletter_output
```
