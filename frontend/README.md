# AI Newsletter Automation — Copilot Console

An enterprise chat-first console for the LangGraph + FastAPI newsletter
automation pipeline: execute the automation workflow, watch real-time
execution telemetry stream in per agent, review the generated newsletter,
and monitor the Power Automate → Outlook delivery pipeline.

Built with **React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui (Radix
primitives, hand-integrated) + Framer Motion + React Markdown + Lucide icons
+ Axios + TanStack React Query**.

> **This frontend only reads from / triggers existing backend endpoints.**
> No LangGraph, agent, or business logic was touched. See `../docs/API.md`
> for the full response schema.

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
| `VITE_API_KEY` | *(empty)* | Sent as `X-API-Key` on protected routes. **Security note:** this is bundled into client-side JS and visible to anyone loading the page — acceptable for an internal deployment against a trusted backend, not appropriate for a public-facing production deployment (proxy through a backend-for-frontend instead). |

## Pages

1. **Copilot** (`/`) — the primary chat surface. Suggested prompts (or free-text, routed by keyword) trigger the real pipeline via `POST /demo/generate`, animate the LangGraph execution timeline with real per-node telemetry, and render the executive summary, section cards, newsletter HTML preview, and execution metrics from the actual response — `GET /newsletter/history` powers the "Recent Editions" strip.
2. **Power Automate** (`/power-automate`) — a production-style monitoring console for the Daily Schedule → FastAPI Endpoint → Content Aggregation → AI Summarization → HTML Generation → Receive JSON → Extract → Compose → Send → Outlook Delivery flow. **Execute Automation** runs the same real pipeline call and threads real per-node timing into each step; **Automation Insights** narrates each step in plain English as it happens; the Outlook email preview renders the real generated HTML. Power Automate and Outlook are not live-connected integrations in this deployment and are labeled accordingly (`Not Configured` / `Awaiting Outlook Integration`) rather than implying a real send.
3. **About** (`/about`) — business context, architecture, and technology stack.

## Architecture notes

- **Data fetching**: [TanStack React Query](https://tanstack.com/query) (`src/lib/queryClient.ts`, `src/hooks/use-health.ts`, `src/hooks/use-newsletter.ts`, `src/hooks/use-automation-workflow.ts`) handles server state — caching, loading/error states, polling (`useHealth` refetches every 30s), and mutations. `useCopilotChat` (`src/hooks/use-copilot-chat.ts`) drives the conversational turn history on the Copilot page; `useAutomationWorkflow` drives the Power Automate page's step-by-step execution state.
- **API client**: `src/lib/api.ts` wraps Axios with a typed error (`ApiError`) that translates 401/404/502/network failures into readable messages, and retries idempotent GETs (health/history/latest) with exponential backoff on network errors or 5xx.
- **Real telemetry, presentational pacing**: every execution timing and item count shown (LangGraph node durations, articles collected, tokens, cost) comes directly from the backend response. Where a step has no real distinct latency of its own (e.g. Power Automate's own Parse JSON / Compose actions), the UI paces its reveal for readability but never fabricates a response.
- **Theming**: a hand-rolled `ThemeProvider` (`src/hooks/use-theme.tsx`) toggles a `light`/`dark` class on `<html>`, persisted to `localStorage`, defaulting to dark.
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

- History detail view is metadata-only (no per-edition GET endpoint exists) — only the latest edition's full content is retrievable.
- Token/cost figures are rough server-computed estimates, not real OpenAI billing data (see `docs/API.md`).
- Power Automate and Outlook delivery are not live-connected in this deployment; the Power Automate page labels this explicitly rather than implying a real send.
- `VITE_API_KEY` in a pure static frontend is inherently visible client-side — acceptable for an internal deployment, not for a public production deployment.
