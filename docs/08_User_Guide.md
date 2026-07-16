# User Guide

The frontend is a single chat-first **Copilot console** (not a traditional
multi-page dashboard), plus a dedicated **Power Automate** monitoring page
and an **About** page. This guide maps each requested capability —
dashboard, generation, history, health, delivery — to where it actually
lives in the shipped UI, so this document matches what you'll click on,
not an earlier design.

## Dashboard (Copilot Home)

The home page (`/`) is the primary surface: a centered chat window with
suggested prompts ("Generate today's newsletter", "Show funding updates",
"Show OpenAI news", etc.) and a free-text input. Typing a question routes
by keyword to the closest supported view — there is no separate
"Dashboard" tab because the chat surface *is* the dashboard: every
suggested prompt is backed by the same one real pipeline call, filtered to
the relevant section of the result.

## Generate Newsletter

Click **"Generate today's newsletter"** (or type a request) on the Copilot
home page. This triggers the real LangGraph pipeline via
`POST /demo/generate` and:

1. Animates the LangGraph execution timeline live, with real per-agent
   timing and item counts as each node completes.
2. Displays the Executive Summary and "One Thing To Watch".
3. Displays each populated section (Global AI News, Company Moves,
   Investments, Talent Trends, Research Highlights, Open Source, Policy &
   Regulation) as its own card.
4. Displays a Newsletter Preview panel (rendered HTML) with **View HTML
   Newsletter**, **Download HTML**, **Download Markdown**, **Copy HTML**,
   and **Copy Markdown** actions.
5. Displays Execution Metrics (execution time, articles collected,
   duplicates removed, stories ranked, stories selected, token usage,
   estimated cost) and the full agent execution timeline.

On the **Power Automate** page, the equivalent action is the **"Execute
Automation"** button, which runs the same real pipeline call but presents
it as a step-by-step workflow console instead of a chat reply.

## History

The Copilot home page shows a **Recent Editions** strip, populated from
`GET /newsletter/history` — subject and relative timestamp for past runs,
newest first. Only the single latest edition's full content is
retrievable (there is no per-edition detail view); the strip is a
lightweight audit trail, not a full archive browser.

## Health

Health is surfaced on the **Power Automate** page's **Workflow Status**
panel, polling `GET /health` every 30 seconds:

| Indicator | Meaning |
|---|---|
| **FastAPI** | `Healthy` if the backend responds; `Unavailable` otherwise |
| **LangGraph** | `Operational` if the compiled workflow loads successfully |
| **Power Automate** | Always `Not Configured` in this console — reference only, since there is no live connection from this app *to* Power Automate (Power Automate calls *into* this API, not the reverse) |
| **Outlook** | `Connected` once a real delivery has been confirmed, `Delivery Failed` if the last reported delivery failed, `Integration Ready` otherwise |

## Power Automate

The **Power Automate** page (`/power-automate`) is a production-style
monitoring console for the full daily automation flow: Daily Schedule →
FastAPI Endpoint → Content Aggregation → AI Summarization → HTML
Generation → Receive JSON → Extract → Compose Outlook Email → Send Outlook
Email → Outlook Delivery. Each step shows its status (`Queued` / `Running`
/ `Completed` / `Error`) and, once complete, its real execution time and
item count.

Toggle **Automation Insights** to see a plain-English narration of each
step as it happens. The **Power Automate Configuration** section
(collapsible) documents the exact trigger/action configuration a
real Power Automate flow uses — see [`09_Demo_Guide.md`](09_Demo_Guide.md)
for a walkthrough script.

## Email Delivery

The **Outlook Delivery** card (top of the Power Automate page) is the
single source of truth for real delivery status, polling
`GET /integration/outlook/status` every 30 seconds:

- **Delivered**: shows `✓ Outlook Connected`, `✓ Email Delivered
  Successfully`, the last delivery timestamp, recipient count, and message
  identifier.
- **Failed**: shows a clear failure alert with the timestamp, prompting a
  check of the flow's run history.
- **Pending** (no delivery ever reported): shows "Waiting for scheduled
  Outlook delivery."

This status is never hardcoded or simulated — it only changes when the
real Power Automate flow calls `POST /integration/outlook/status` after
its "Send an email (V2)" action completes or fails.
