# Future Roadmap

## Near-term

- **LangGraph checkpointing** - persist graph state via a `Checkpointer`
  (e.g. SQLite/Postgres) so a partially-completed run can resume instead of
  restarting from scratch after a transient failure.
- **Per-recipient personalization** - accept a recipient/segment parameter
  on `POST /generate-newsletter` and bias `RankingAgent` weights per
  audience (e.g. an engineering-focused vs. an investor-focused digest).
- **Real LinkedIn Talent API integration** - implement
  `ApiLinkedInJobsProvider` (`app/services/linkedin_provider.py`) against a
  licensed LinkedIn Talent/Partner API once credentials are available.
- **Structured Crunchbase field mapping** - validate/extend
  `CrunchbaseFundingProvider`'s field-id mapping against a live Crunchbase
  Enterprise API key (currently implemented against the documented v4
  schema, unverified against a paid account).

## Medium-term

- **Database-backed history** - replace the filesystem `history_service`
  with a Postgres/Cosmos DB-backed store for multi-instance deployments
  (the current implementation assumes a single writable volume).
- **Feedback loop** - capture click/open data from the Outlook send (via
  Power Automate) and feed it back into `RankingAgent`'s weights over time.
- **Additional policy/region coverage** - add dedicated collectors for
  China's AI governance framework, the UK's AI regulatory approach, and
  additional US state-level AI legislation.
- **Multi-language newsletters** - localize the GPT prompts in
  `NewsletterGeneratorAgent` and add a `NEWSLETTER_LANGUAGE` setting.

## Long-term

- **Self-serve section configuration** - expose an admin endpoint to
  reweight ranking dimensions, add/remove RSS sources, and toggle sections
  without a redeploy.
- **A/B subject-line testing** - generate 2-3 subject line candidates via
  `NewsletterGeneratorAgent` and let Power Automate route between them for
  open-rate experiments.
- **Alternative delivery channels** - reuse the same `NewsletterOutput`
  (HTML/Markdown/JSON) to publish to Slack, Teams, or a public web archive
  in addition to Outlook.
