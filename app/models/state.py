"""Typed shared state for the LangGraph newsletter workflow.

Each collector agent writes to its own dedicated list field, so no merge
conflicts occur during parallel fan-out. `execution_logs` and `errors` are
appended to concurrently by multiple parallel branches, so they use an
`operator.add` reducer to concatenate rather than overwrite.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from app.models.article import Article
from app.models.newsletter import AgentExecutionRecord, NewsletterContent


class GraphState(TypedDict, total=False):
    # Collector outputs (populated by the parallel fan-out stage)
    global_news: list[Article]
    company_news: list[Article]
    funding: list[Article]
    talent: list[Article]
    research: list[Article]
    opensource: list[Article]
    policy: list[Article]
    model_releases: list[Article]

    # Downstream pipeline stages
    aggregated_articles: list[Article]
    deduplicated_articles: list[Article]
    ranked_news: list[Article]

    # Final outputs
    newsletter_content: NewsletterContent | None
    newsletter_html: str
    newsletter_markdown: str
    newsletter_json: dict

    # Observability
    execution_logs: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
    agent_execution: Annotated[list[AgentExecutionRecord], operator.add]


COLLECTOR_STATE_KEYS: list[str] = [
    "global_news",
    "company_news",
    "funding",
    "talent",
    "research",
    "opensource",
    "policy",
    "model_releases",
]


def build_initial_state() -> GraphState:
    """Return a fresh `GraphState` with every field initialized to an empty value."""
    state: GraphState = {key: [] for key in COLLECTOR_STATE_KEYS}  # type: ignore[assignment]
    state["aggregated_articles"] = []
    state["deduplicated_articles"] = []
    state["ranked_news"] = []
    state["newsletter_content"] = None
    state["newsletter_html"] = ""
    state["newsletter_markdown"] = ""
    state["newsletter_json"] = {}
    state["execution_logs"] = []
    state["errors"] = []
    state["agent_execution"] = []
    return state
