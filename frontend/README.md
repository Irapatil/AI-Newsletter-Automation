# AI Newsletter Automation — Frontend

An enterprise-styled dashboard for demoing the LangGraph + FastAPI newsletter
pipeline: trigger a run, watch simulated agent-by-agent progress, review the
rendered newsletter, browse history, and check integration health.

Built with **React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui (Radix
primitives, hand-integrated) + Lucide icons + Axios + TanStack React Query**.

> **This frontend only reads/writes existing backend endpoints.** No
> LangGraph, agent, or business logic was touched. Two backend endpoints
> gained small, additive, backward-compatible fields to support this UI:
> `GET /health` now returns a `providers` breakdown, and
> `POST /generate-newsletter` / `GET /newsletter/latest` now include a
> `stats` object. See `../docs/API.md` for the full schema.

## ⚠️ Important: this was built without a local Node.js runtime

This codebase was authored in an environment where Node.js/npm were not
available, so **`npm install` and `npm run dev` were never actually executed
or verified here.** Every file was written carefully and reviewed by hand,
but you should treat the very first `npm install && npm run dev` as the real
first test. If anything doesn't compile, it's most likely a small import
path or dependency-version mismatch — please report it back so it can be
fixed immediately.

## Prerequisites

- Node.js 20+ and npm
- The FastAPI backend running (see the repository root `README.md`) —
  by default at `http://localhost:8000`

## Setup

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env: set VITE_API_KEY to match the backend's API_AUTH_TOKEN
# (leave both empty if the backend has auth disabled in development)
npm run dev
```

Visit `http://localhost:5173`.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with HMR |
| `npm run build` | Type-check (`tsc -b`) and build for production into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | FastAPI backend base URL |
| `VITE_API_KEY` | *(empty)* | Sent as `X-API-Key` on protected routes. **Security note:** this is bundled into client-side JS and visible to anyone loading the page — fine for an internal demo hitting a dev backend, not appropriate for a public-facing production deployment (proxy through a backend-for-frontend instead). |

## Pages

1. **Dashboard** — system health (Backend/LangGraph/OpenAI, from `GET /health`), last newsletter generated + next scheduled run (a static note — scheduling lives in Power Automate, not this API), and Quick Stats (articles collected/duplicates removed/stories selected from the latest edition).
2. **Generate Newsletter** — the trigger button. Since the backend runs the whole pipeline synchronously and returns only the final result (no SSE/WebSocket streaming exists today), progress is **simulated** node-by-node while the real request is in flight, and only snaps to "complete" once the actual response arrives — it never reports success before the API genuinely responds. On failure, the real error is shown with a manual retry (not auto-retried, since re-running the full pipeline is expensive).
3. **Newsletter** — the generated/most-recent edition: rendered HTML (sandboxed iframe, also used for the Print action via `contentWindow.print()`), a structured section/article view, raw Markdown, plus a metrics panel (execution time, articles collected, duplicates removed, stories ranked, stories selected — all real; OpenAI tokens/cost are clearly-labeled client-side **estimates**, since the API doesn't return actual usage data) and download/copy/print actions.
4. **History** — timeline view from `GET /newsletter/history`, with client-side search-by-subject. The API only ever returns full content for the single latest edition (`GET /newsletter/latest`) — there's no per-edition detail endpoint yet, so history rows show metadata only (this is called out in the UI, not hidden).
5. **Health** — `GET /health`'s per-provider breakdown (FastAPI, OpenAI, NewsAPI, GitHub, RSS, LangGraph), each with a tooltip explaining exactly what the status means and how it was determined (all are config/compile checks — no outbound calls are made to any provider during a health check).

## Architecture notes

- **Data fetching**: [TanStack React Query](https://tanstack.com/query) (`src/lib/queryClient.ts`, `src/hooks/use-health.ts`, `src/hooks/use-newsletter-queries.ts`) handles all server state — caching, loading/error states, polling (`useHealth` refetches every 30s), and retry. `useGenerateNewsletter()` is a mutation whose `onSuccess` seeds the `["newsletter","latest"]` query cache directly, so the Generate and Newsletter pages share data with no prop-drilling or hand-rolled context.
- **API client**: `src/lib/api.ts` wraps Axios with a typed error (`ApiError`) that translates 401/404/502/network failures into readable messages, and retries idempotent GETs (health/history/latest) with exponential backoff on network errors or 5xx — `POST /generate-newsletter` is intentionally not auto-retried (React Query's own `retry` is also disabled for it).
- **Theming**: a hand-rolled `ThemeProvider` (`src/hooks/use-theme.tsx`) toggles a `light`/`dark` class on `<html>`, persisted to `localStorage`, respecting `prefers-color-scheme` on first load.
- **UI primitives**: `src/components/ui/*` follow the shadcn/ui pattern (Radix primitives + `class-variance-authority` + Tailwind) — copied into the project rather than depending on a component library, per shadcn's own convention.

## Docker

```bash
docker build -t ai-newsletter-frontend \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  --build-arg VITE_API_KEY=your-token \
  .
docker run -p 4173:80 ai-newsletter-frontend
```

Note: Vite bakes `VITE_*` variables in at **build** time, not container
start — rebuild the image if the backend URL or key changes.

## Known limitations

- Progress during generation is simulated, not streamed (see Generate Newsletter above).
- History detail view is metadata-only (no per-edition GET endpoint exists).
- Token/cost figures are rough client-side estimates, not real OpenAI usage data.
- `VITE_API_KEY` in a pure static frontend is inherently visible client-side — acceptable for this demo, not for a public production deployment.
