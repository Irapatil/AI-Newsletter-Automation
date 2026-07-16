# Power Automate flow definition (importable reference)

`definition.json` is the flow described in
[`docs/POWER_AUTOMATE.md`](../docs/POWER_AUTOMATE.md), written in the same
Workflow Definition Language Power Automate cloud flows run on under the
hood (the same schema Azure Logic Apps uses). It is a precise, unambiguous
reference for every action's exact configuration - not prose you have to
transcribe by hand.

## What this is, honestly

This was hand-authored without access to a live Power Automate tenant, so
it has **not** been created via a real export and **cannot** be verified to
import cleanly through **Import Package (Legacy)** or as a Solution `.zip`
- those formats additionally require tenant-specific connection reference
GUIDs, environment IDs, and package manifests that only a real export from
your own environment can produce correctly. Producing a `.zip` that *looks*
like a real export but was fabricated without ever running the actual
Power Automate export pipeline would be more likely to fail import with a
confusing error than to save you time, so this repo intentionally does not
include one.

What `definition.json` **is** good for:

- **Code view**: newer Power Automate environments expose a "Code view"
  (flow menu → **Edit** → **Code view**, currently rolling out / preview in
  some tenants) that lets you paste a workflow definition directly instead
  of clicking through the designer action-by-action. If your environment
  has it, this file can be pasted there directly.
- **An exact reference while building manually**: every action's method,
  URI, header, expression, and `runAfter`/"Configure run after" wiring is
  spelled out precisely, removing any ambiguity from the step-by-step guide
  in `docs/POWER_AUTOMATE.md`. Building from the designer using this as a
  side-by-side reference takes about 10 minutes.
- **A record of intent**: if you review this with a teammate before
  building, it's a complete, precise spec of the flow to build - useful
  for a design review even if you never paste the JSON anywhere.

## Before using it

Replace these parameter default values (top of the file, under
`"parameters"`) with your real values:

| Parameter | Replace with |
|---|---|
| `ApiBaseUrl` | Your deployed backend's public HTTPS URL (see "Deployment steps" in `docs/POWER_AUTOMATE.md`) |
| `ApiAuthToken` | Your real `API_AUTH_TOKEN` - store as a secure input, never commit a real value here |
| `DistributionList` | The real recipient address/distribution list |
| `OpsMailbox` | Where failure alerts should go |

The two `OpenApiConnection` actions (`Outlook_-_Send_an_email_V2`,
`Outlook_-_Notify_ops_on_failure`) reference `shared_office365` as the
connection name - when you build this in the designer (or via Code view),
Power Automate will prompt you to authorize a real Office 365 Outlook
connection and will fill in the real connection reference itself; the
placeholder here is just the standard connector id, not a fabricated
credential.

## Validating the JSON

The file is valid JSON (`python -m json.tool power-automate/definition.json`
succeeds) and follows the real Workflow Definition Language schema, but
"valid JSON matching the schema" is not the same guarantee as "verified to
import into Power Automate" - test it in a non-production environment
first, and fall back to `docs/POWER_AUTOMATE.md`'s manual steps if Code
view isn't available in your tenant or the paste doesn't take.
