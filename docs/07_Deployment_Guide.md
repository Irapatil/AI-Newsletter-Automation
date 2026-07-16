# Deployment Guide

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm (frontend only)
- An OpenAI API key (optional — the mock LLM provider runs the full
  pipeline offline for testing/demos)
- Docker (optional, for containerized deployment)

## Python Setup

```bash
git clone https://github.com/Irapatil/AI-Newsletter-Automation.git
cd AI-Newsletter-Automation
```

## Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

## Dependencies

```bash
pip install -r requirements.txt        # runtime dependencies
pip install -r requirements-dev.txt    # + testing/linting tools
```

Or via `make`:

```bash
make install
make install-dev
```

## Environment Variables

```bash
cp .env.example .env
```

Every field has a safe default — the application runs end-to-end (mock
LLM, no external keys) even with an empty `.env`. Key variables:

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development` \| `staging` \| `production` — gates authentication and Swagger availability |
| `API_AUTH_TOKEN` | Shared secret Power Automate sends as `X-API-Key`. Only enforced when `APP_ENV=production` |
| `LLM_PROVIDER` | `openai` \| `azure_openai` \| `mock` |
| `OPENAI_API_KEY` | Required for real GPT summaries/embeddings (falls back to mock if empty) |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed to call the API directly (your deployed frontend's URL) |
| `ALLOWED_HOSTS` | `Host` header allowlist — set to your real domain(s) in production |
| `OUTLOOK_STATUS_FILE` | Path to the persisted Outlook delivery status (default `data/outlook_status.json`) |

Full reference: [`ENVIRONMENT_VARIABLES.md`](ENVIRONMENT_VARIABLES.md).

## Running the Backend

```bash
# Development (auto-reload)
make dev
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production-style (no reload)
make run
```

Verify: `curl http://localhost:8000/health` should return `{"status": "ok", ...}`.
Swagger UI: `http://localhost:8000/docs` (development/staging only).

## Running the Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env: VITE_API_BASE_URL should point at the backend above
npm run dev
```

Visit `http://localhost:5173`. For a production build:

```bash
npm run build     # outputs to frontend/dist/
npm run preview   # serve the production build locally
```

## Power Automate Integration

1. Deploy the backend somewhere with a **public HTTPS URL** — Power
   Automate is a cloud service and cannot reach `localhost` directly
   (a tunnel such as `ngrok` works for testing only, never production).
2. Set `APP_ENV=production` and a real `API_AUTH_TOKEN`
   (`openssl rand -hex 32`) — production refuses to start without one.
3. Build the flow described in [`POWER_AUTOMATE.md`](POWER_AUTOMATE.md):
   Recurrence trigger → HTTP (`POST /generate-newsletter`) → Parse JSON →
   Compose → Outlook Send Email (V2) → HTTP callback
   (`POST /integration/outlook/status`).
4. An importable flow definition reference is provided at
   [`../power-automate/definition.json`](../power-automate/definition.json)
   (see [`../power-automate/README.md`](../power-automate/README.md) for
   how to use it and its limitations).

## Outlook Integration

Outlook delivery uses the standard **Office 365 Outlook connector**'s
"Send an email (V2)" action inside the Power Automate flow — no custom
connector or app registration is required for a user-delegated flow. A
shared mailbox as the sender requires **Send As**/**Send on Behalf**
permission granted to the flow's connection owner.

Delivery status is reported back to the platform in real time via
`POST /integration/outlook/status`, and the frontend's Power Automate
console reflects it automatically (`Connected` once a real delivery is
confirmed, `Integration Ready` beforehand, `Delivery Failed` if the flow
reports a failure) — see [`08_User_Guide.md`](08_User_Guide.md).

## Production Deployment

### Docker

```bash
cp .env.example .env    # fill in real production values first
make docker-build
make docker-up
make docker-logs
```

This builds and runs both the backend (`python:3.11-slim`) and frontend
(Nginx-served static build) containers via `docker-compose.yml`. See
[`DEPLOYMENT.md`](DEPLOYMENT.md) for cloud-specific patterns (Azure
Container Apps, AWS ECS, Kubernetes) and secrets-management guidance.

### Production checklist

| Item | Requirement |
|---|---|
| `APP_ENV` | `production` |
| `API_AUTH_TOKEN` | Set to a real, high-entropy secret |
| `ALLOWED_HOSTS` | Your real domain(s), not `*` |
| `CORS_ALLOWED_ORIGINS` | Your deployed frontend's exact origin |
| `OPENAI_API_KEY` (or Azure equivalent) | Set for real GPT output |
| `/docs`, `/redoc`, `/openapi.json` | Automatically disabled in production |
| TLS | Terminate HTTPS at your reverse proxy / load balancer / container platform |
| History persistence | `NEWSLETTER_HISTORY_DIR` and `OUTLOOK_STATUS_FILE` should live on a durable, writable volume |

### Verification after deploy

```bash
curl https://<your-host>/health
curl -X POST https://<your-host>/generate-newsletter -H "X-API-Key: $API_AUTH_TOKEN"
curl https://<your-host>/newsletter/latest/html
```
