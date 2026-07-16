# Demo Guide

A structured walkthrough for presenting AI Newsletter Automation to a
business stakeholder or client. Total run time: roughly 15-20 minutes.

## 1. Business Introduction (2 minutes)

Open with the problem, not the technology:

> "Staying current on AI industry news — funding, research, hiring,
> policy, model releases — means monitoring dozens of sources every day.
> This platform automates that entirely: it collects, deduplicates, ranks,
> and summarizes AI news into an executive-ready newsletter, delivered to
> Outlook every morning with zero manual effort."

Reference [`01_Project_Overview.md`](01_Project_Overview.md) for the full
business case if deeper discussion is needed.

## 2. Architecture (2 minutes)

Show the high-level flow (whiteboard or [`02_System_Architecture.md`](02_System_Architecture.md)'s
Mermaid diagram):

```
Frontend → FastAPI → LangGraph → 8 AI Agents → Semantic Search → GPT → HTML → Power Automate → Outlook
```

Key talking point: this is a **deterministic pipeline**, not an
open-ended agent loop — every run follows the same fixed, inspectable set
of steps, which is what makes the output consistent and auditable.

## 3. Live Demo — the Console (5 minutes)

1. Open the frontend (`http://localhost:5173` in development, or your
   deployed URL).
2. On the Copilot home page, click **"Generate today's newsletter."**
3. Narrate the LangGraph execution animation as it plays out — call out
   that the timings and item counts shown are the *real* per-agent
   telemetry from this exact run, not a canned animation.
4. Once complete, walk through:
   - The **Executive Summary** and **One Thing To Watch**.
   - Two or three section cards (e.g. Investments, Research Highlights).
   - The **Newsletter Preview** panel — click **View HTML Newsletter** to
     open the rendered email in a new tab.
   - The **Execution Metrics** panel — execution time, articles collected,
     duplicates removed, tokens, estimated cost.

## 4. Pipeline Deep-Dive (3 minutes, optional depending on audience)

For a technical audience, open `http://localhost:8000/docs` (Swagger) and:

1. Execute `POST /demo/generate` directly, showing the raw JSON response.
2. Point out `agent_execution` — the node-by-node execution report.
3. Open `GET /newsletter/latest/html` to show the same rendered output the
   API itself serves, independent of the frontend.

Reference [`03_AI_Pipeline.md`](03_AI_Pipeline.md) for the full technical
narrative if questions go deep on deduplication or ranking methodology.

## 5. Power Automate (3 minutes)

1. Navigate to the **Power Automate** page in the console.
2. Click **"Execute Automation"** and narrate the step-by-step console:
   Daily Schedule → FastAPI Endpoint → Content Aggregation → AI
   Summarization → HTML Generation → Receive JSON → Extract → Compose →
   Send → Outlook Delivery — each with real timing once complete.
3. Toggle **Automation Insights** to show the plain-English narration.
4. Expand **Power Automate Configuration** to show the exact
   trigger/action setup a production flow uses.

If a real Power Automate flow is connected in the environment, this is the
moment to show it live in the Power Automate portal alongside the
console — the same run, two views.

## 6. Outlook (2 minutes)

1. Show the **Outlook Delivery** card at the top of the Power Automate
   page.
2. If a real flow has run recently, it should read `✓ Outlook Connected` /
   `✓ Email Delivered Successfully` with a real timestamp — emphasize that
   this is a live callback from Power Automate
   (`POST /integration/outlook/status`), not a hardcoded status.
3. If no real flow is connected in this environment, it will honestly show
   "Waiting for scheduled Outlook delivery" — use this as a talking point
   for how the integration is designed to be honest about its own state
   rather than fake a connection.

## 7. Business Value (2 minutes)

Close by reiterating outcomes from
[`01_Project_Overview.md`](01_Project_Overview.md):

- Zero recurring labor cost per edition once deployed.
- Consistent methodology across every run — auditable via the execution
  report.
- Graceful degradation — one failed data source never blocks the day's
  newsletter.
- Low operating cost (cents per run in LLM usage).

## 8. Future Roadmap (1 minute)

Briefly preview [`10_Future_Roadmap.md`](10_Future_Roadmap.md) — Teams and
SharePoint integration, personalization, role-based delivery, an analytics
dashboard, translation, an approval workflow, and AI trend prediction —
framed as "here's where this platform can grow, on the same architecture,
without a rebuild."
