# Microsoft Power Automate Integration Guide

This guide wires the `/generate-newsletter` API into a Power Automate cloud
flow that runs daily and sends the result through Outlook.

## Flow overview

```
Daily Trigger (Recurrence, 8:00 AM)
        │
        ▼
HTTP (POST /generate-newsletter)
        │
        ▼
Parse JSON (the HTTP response body)
        │
        ▼
Compose (HTML body)
        │
        ▼
Outlook: Send an email (V2)
        │
        ▼
(optional) Create file in SharePoint - archive the HTML/Markdown
```

## Step 1 - Recurrence trigger

1. Create a new **Automated cloud flow** (or **Scheduled cloud flow**).
2. Add trigger **Recurrence**.
3. Set **Interval**: `1`, **Frequency**: `Day`, **At these hours**: `8`, **At these minutes**: `0`.

> `docs/images/power-automate-trigger.png` — *(screenshot placeholder: Recurrence trigger configuration panel)*

## Step 2 - HTTP action

1. Add action **HTTP**.
2. **Method**: `POST`
3. **URI**: `https://<your-deployed-host>/generate-newsletter`
4. **Headers**:
   | Key | Value |
   |---|---|
   | `Content-Type` | `application/json` |
   | `X-API-Key` | `@{parameters('ApiAuthToken')}` (store as an environment variable / secure input, not hardcoded) |
5. **Body**: `{}`  (or `{"requested_by": "power-automate-daily-trigger"}`)

Mark the `X-API-Key` header value as **Secure Input/Output** in the action's
settings so it does not appear in run history logs.

> `docs/images/power-automate-http-action.png` — *(screenshot placeholder: HTTP action configuration)*

## Step 3 - Parse JSON

1. Add action **Parse JSON**.
2. **Content**: `Body` (output of the HTTP action).
3. **Schema** — generate from a sample payload (run the HTTP action once and
   use *"Use sample payload to generate schema"* — Swagger's example for
   `POST /generate-newsletter` at `/docs` works directly as a sample), or
   paste directly:

```json
{
  "type": "object",
  "properties": {
    "subject": { "type": "string" },
    "summary": { "type": "string" },
    "generated_at": { "type": "string" },
    "execution_time_seconds": { "type": "number" },
    "newsletter_html": { "type": "string" },
    "newsletter_markdown": { "type": "string" },
    "newsletter_json": { "type": "object" },
    "statistics": {
      "type": "object",
      "properties": {
        "aggregated_count": { "type": "integer" },
        "duplicates_removed": { "type": "integer" },
        "ranked_count": { "type": "integer" },
        "stories_selected": { "type": "integer" }
      }
    },
    "sources_used": { "type": "array", "items": { "type": "string" } },
    "agent_execution": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "node": { "type": "string" },
          "status": { "type": "string" },
          "execution_time_seconds": { "type": "number" },
          "items_processed": { "type": "integer" }
        }
      }
    },
    "provider": { "type": "string" },
    "status": { "type": "string" },
    "token_usage": {
      "type": "object",
      "properties": {
        "prompt_and_completion_tokens": { "type": "integer" },
        "is_estimated": { "type": "boolean" }
      }
    },
    "estimated_cost_usd": { "type": "number" },
    "errors": { "type": "array", "items": { "type": "string" } }
  }
}
```

> `docs/images/power-automate-parse-json.png` — *(screenshot placeholder: Parse JSON schema editor)*

## Step 4 - Compose (HTML body)

Add action **Compose**, **Inputs**: `body('Parse_JSON')?['newsletter_html']`.

This step is optional (you can reference the Parse JSON output directly in
the Outlook action), but keeping it separate makes the flow easier to debug
- you can inspect the exact HTML string in the run history.

## Step 5 - Outlook: Send an email (V2)

1. Add action **Outlook: Send an email (V2)**.
2. **To**: your distribution list (e.g. `ai-newsletter@yourcompany.com`).
3. **Subject**: `body('Parse_JSON')?['subject']`.
4. **Body**: `outputs('Compose')` (or `body('Parse_JSON')?['newsletter_html']` directly).
5. **Is HTML**: `Yes`.

Optionally, add a condition checking
`body('Parse_JSON')?['status']` equals `partial_success` to CC an ops
mailbox or append a note when one or more collectors failed but a
newsletter still went out.

> `docs/images/power-automate-outlook-send.png` — *(screenshot placeholder: Outlook Send an email action)*

## Step 6 (optional) - Archive to SharePoint

To keep a durable, browsable archive independent of the API's own history
store:

1. Add action **SharePoint: Create file**.
2. **Site Address**: your SharePoint site.
3. **Folder Path**: e.g. `/Shared Documents/AI Newsletters`.
4. **File Name**: `@{formatDateTime(utcNow(), 'yyyy-MM-dd')}-ai-newsletter.html`
5. **File Content**: `body('Parse_JSON')?['newsletter_html']`.

You can add a second **Create file** action for
`body('Parse_JSON')?['newsletter_markdown']` if you also want a Markdown
archive (useful for pasting into Teams/Confluence/Notion).

> `docs/images/power-automate-sharepoint-archive.png` — *(screenshot placeholder: SharePoint Create file action)*

## Error handling

Add a **Configure run after** setting on the Outlook action (or a parallel
branch) to run **"is successful, has timed out, is skipped, has failed"** so
a failed HTTP call still notifies someone - e.g. an additional Outlook
action sending an alert to an ops mailbox when the HTTP action's status is
`Failed`. Because every collector agent in the pipeline isolates its own
failures (see `app/agents/base_agent.py`), the API call itself only fails
on a hard error (e.g. the whole workflow throwing), which should be rare
and worth alerting on.

## Testing the flow

1. Save the flow, then use **Test > Manually** to trigger it once
   immediately rather than waiting for the next 8 AM run.
2. Check the run history for each action's inputs/outputs - the HTTP
   action's output body should match the shape documented in
   [`API.md`](API.md).
