# Future Roadmap

The items below are business-facing platform extensions, buildable on the
current architecture without a rebuild. For the more granular engineering
backlog (checkpointing, database-backed history, etc.), see
[`ROADMAP.md`](ROADMAP.md).

## Microsoft Teams Integration

Post the daily newsletter (or a condensed digest) to a Teams channel via
the Teams connector, in addition to — or instead of — Outlook email.
Reuses the existing `newsletter_markdown` output with no pipeline changes.

## SharePoint Archive

Automatically archive each edition's HTML and Markdown to a SharePoint
document library from within the same Power Automate flow (a
`SharePoint: Create file` action alongside the existing Outlook send),
providing a durable, browsable archive independent of the API's own
history store.

## Azure Deployment

A reference deployment to Azure Container Apps (backend) and Azure Static
Web Apps (frontend), with Key Vault-backed secrets and Application
Insights telemetry — packaged as Infrastructure-as-Code (Bicep/Terraform)
for one-command provisioning.

## Personalized Newsletters

Accept a recipient or segment parameter and bias `RankingAgent`'s weights
per audience — for example, an engineering-focused edition emphasizing
research and open source, versus an investor-focused edition emphasizing
funding and business impact.

## Role-Based Delivery

Extend Power Automate to look up distribution lists (or individual
recipients) by role — executives, engineers, investors — and route a
personalized edition to each, using the personalization capability above.

## Analytics Dashboard

Capture open/click data from the Outlook send (via Power Automate's
tracking or a lightweight redirect layer) and surface engagement trends —
which sections and stories perform best — feeding back into ranking
weights over time.

## Translation

Localize the GPT prompts and rendered output for non-English audiences,
gated by a `NEWSLETTER_LANGUAGE` setting per recipient/segment.

## Approval Workflow

Insert an optional human-in-the-loop approval step between generation and
delivery for organizations that require sign-off before external-facing
content goes out — a Power Automate "Start and wait for an approval"
action ahead of the Outlook send.

## AI Trend Prediction

Apply trend analysis across historical editions (using the same embedding
representations already computed for deduplication) to surface emerging
themes before they're widely reported — e.g. a cluster of research papers
in a narrow sub-field appearing weeks before a corresponding product
announcement.
