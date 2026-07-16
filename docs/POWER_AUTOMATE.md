# Microsoft Power Automate Integration Guide

This guide wires the `/generate-newsletter` API into a Power Automate cloud
flow that runs daily, sends the result through Outlook, and reports real
delivery status back to the API so the frontend's Power Automate console
reflects actual Outlook delivery instead of a placeholder.

> **Prefer pasting JSON over clicking through the designer?**
> [`power-automate/definition.json`](../power-automate/definition.json) is
> the same flow below, written out precisely in Power Automate's underlying
> Workflow Definition Language - see
> [`power-automate/README.md`](../power-automate/README.md) for how to use
> it and its honest limitations (it hasn't been verified against a real
> tenant).

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
        ├─── on success ──▶ HTTP (POST /integration/outlook/status, status="delivered")
        │
        └─── on failure ──▶ HTTP (POST /integration/outlook/status, status="failed")
                             + Outlook: Send an email (V2) to an ops mailbox
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
settings so it does not appear in run history logs. Retry policy: open the
HTTP action's **Settings** and set **Retry Policy** to `Exponential`, **Count**
`4`, **Interval** `PT10S` - the pipeline itself is a single request, so a
transient network/5xx failure calling the API is the only thing worth
retrying here (the LangGraph pipeline's own per-collector retries already
happen server-side, see `app/utils/retry.py`).

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

## Step 5 - Outlook connector: Send an email (V2)

1. Add action **Outlook: Send an email (V2)** (the standard Office 365
   Outlook connector - no custom connector or app registration required for
   a user-delegated flow; a shared mailbox needs the sender to have **Send
   As**/**Send on Behalf** permission on it).
2. **To**: your distribution list (e.g. `ai-newsletter@yourcompany.com`).
3. **Subject**: `body('Parse_JSON')?['subject']`.
4. **Body**: `outputs('Compose')` (or `body('Parse_JSON')?['newsletter_html']` directly).
5. **Is HTML**: `Yes`.

Optionally, add a condition checking
`body('Parse_JSON')?['status']` equals `partial_success` to CC an ops
mailbox or append a note when one or more collectors failed but a
newsletter still went out.

**Important connector detail**: "Send an email (V2)" does not return a
message id in its outputs (unlike a "Get emails"-style trigger), so there is
nothing to forward as a real Outlook message identifier. The callback step
below uses the flow run's own identifier instead - accurate and unique
per run, without inventing data the connector doesn't provide.

> `docs/images/power-automate-outlook-send.png` — *(screenshot placeholder: Outlook Send an email action)*

## Step 6 - Callback: report delivery status

This is what replaces the frontend's "Integration Ready" placeholder with a
real `Connected` / `Email Delivered Successfully` state - see
[`API.md`](API.md#post-integrationoutlookstatus) for the endpoint's full
schema.

1. Add action **HTTP**, configured to run **only after Send an email (V2)
   succeeds**: on the action's **⋯ menu → Configure run after**, check only
   **is successful**.
2. **Method**: `POST`
3. **URI**: `https://<your-deployed-host>/integration/outlook/status`
4. **Headers**: same `Content-Type: application/json` and `X-API-Key` as Step 2.
5. **Body**:
   ```json
   {
     "status": "delivered",
     "timestamp": "@{utcNow()}",
     "message_id": "@{workflow().run.name}",
     "recipient_count": "@{length(split(body('Parse_JSON')?['statistics']?['stories_selected'], ''))}"
   }
   ```
   In practice `recipient_count` is optional and only meaningful if your
   `To` field is a dynamically-computed distribution list - for a static
   list, omit it or hardcode the count; it isn't derived from
   `stories_selected` in a real flow (that example line is illustrative of
   the expression syntax, not a real recipient count formula).

Add a **second** HTTP action, configured to run **only after Send an email
(V2) has failed, has timed out, or is skipped** (**Configure run after** →
check those three), POSTing the same endpoint with:
```json
{ "status": "failed", "timestamp": "@{utcNow()}" }
```
Pair this with an **Outlook: Send an email (V2)** action (also configured to
run on that same failure branch) addressed to an ops mailbox, so a failed
send is never silent - this is the flow's failure notification.

> `docs/images/power-automate-callback.png` — *(screenshot placeholder: HTTP callback action + Configure run after)*

## Step 7 (optional) - Archive to SharePoint

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

## The callback endpoint

`POST /integration/outlook/status` and `GET /integration/outlook/status` are
a small, real feedback loop - not a mock:

- `POST` (called by the flow, requires `X-API-Key` in production) persists
  `{status, timestamp, message_id?, recipient_count?}` to
  `OUTLOOK_STATUS_FILE` (default `data/outlook_status.json`).
- `GET` (public, polled by the frontend every 30 seconds) returns the same
  record as `{delivery_status, last_delivery_time, message_id,
  recipient_count}`, defaulting to `delivery_status: "pending"` with
  everything else `null` until the first real callback arrives.
- There is no simulated or hardcoded "connected" state anywhere in this
  path - if the flow has never successfully called back, the frontend
  always shows the pending/"Integration Ready" state, honestly.

## Deployment steps

For Power Automate (a cloud service) to reach this API, the backend needs a
publicly resolvable HTTPS URL - `localhost` only works if you're testing
from the same machine via a tunnel.

1. **Deploy the backend** somewhere with a public HTTPS endpoint - the
   included `Dockerfile`/`docker-compose.yml` work on any container host
   (Azure Container Apps, AWS ECS/App Runner, Fly.io, a VM behind a
   reverse proxy, etc.). Set `APP_ENV=production` and a real
   `API_AUTH_TOKEN` (`openssl rand -hex 32`) - production refuses to boot
   without one (see `app/config/settings.py`).
2. **Local testing without a full deployment**: run `uvicorn` locally and
   expose it with a tunnel (e.g. `ngrok http 8000`), then point the flow's
   HTTP actions at the tunnel's HTTPS URL. Tunnels are for testing the flow
   end-to-end only - don't leave one running as your production endpoint.
3. **Set `ALLOWED_HOSTS`** to the exact host Power Automate will call (the
   tunnel/deployed domain) - `TrustedHostMiddleware` rejects anything else.
4. **`CORS_ALLOWED_ORIGINS`** doesn't need to include Power Automate at all
   - CORS only applies to browser-based callers (the frontend); Power
   Automate's HTTP action isn't a browser and isn't subject to CORS.
5. Import/recreate the flow described above in your own Power Automate
   environment (there's no exportable flow package in this repo - build it
   from the steps above, which take about 10 minutes).
6. Run **Test → Manually** once to confirm both the newsletter email and
   the callback fire, then check `GET /integration/outlook/status` reflects
   `"delivered"` and the frontend's Power Automate page shows **Outlook
   Connected**.

## Error handling

Add a **Configure run after** setting on the Outlook action (or a parallel
branch) to run **"is successful, has timed out, is skipped, has failed"** so
a failed HTTP call still notifies someone - e.g. an additional Outlook
action sending an alert to an ops mailbox when the HTTP action's status is
`Failed`. Because every collector agent in the pipeline isolates its own
failures (see `app/agents/base_agent.py`), the API call itself only fails
on a hard error (e.g. the whole workflow throwing), which should be rare
and worth alerting on. Step 6 above wires the same failure branch to the
callback endpoint, so a failed send is reflected in `GET
/integration/outlook/status` too, not just in an email alert.

## Testing the flow

1. Save the flow, then use **Test > Manually** to trigger it once
   immediately rather than waiting for the next 8 AM run.
2. Check the run history for each action's inputs/outputs - the HTTP
   action's output body should match the shape documented in
   [`API.md`](API.md).
3. Confirm the callback fired: `curl https://<your-host>/integration/outlook/status`
   should show `"delivery_status": "delivered"` and a recent
   `last_delivery_time`.
