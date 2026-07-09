"""LangGraph node functions - thin adapters between agents and shared state.

Every node returns only the state keys it owns, so LangGraph can safely run
the eight collector nodes in parallel: each writes to its own dedicated
field, and `execution_logs`/`errors` are merged via the `operator.add`
reducer declared on `GraphState`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from app.agents.aggregator_agent import AggregatorAgent
from app.agents.base_agent import BaseCollectorAgent
from app.agents.deduplication_agent import DeduplicationAgent
from app.agents.html_formatter_agent import HTMLFormatterAgent
from app.agents.newsletter_generator_agent import NewsletterGeneratorAgent
from app.agents.ranking_agent import RankingAgent
from app.config.logging_config import get_logger
from app.models.newsletter import NewsletterContent
from app.models.state import GraphState

logger = get_logger(__name__)

NodeFn = Callable[[GraphState], Awaitable[dict]]


def make_collector_node(agent: BaseCollectorAgent) -> NodeFn:
    async def _node(
        state: GraphState,
    ) -> dict:  # noqa: ARG001 - state unused, agent is self-contained
        result = await agent.collect()
        return {
            agent.state_key: result.articles,
            "execution_logs": result.logs,
            "errors": result.errors,
        }

    _node.__name__ = f"{agent.state_key}_collector"
    return _node


async def orchestrator_node(state: GraphState) -> dict:  # noqa: ARG001
    logger.info("workflow_started")
    return {"execution_logs": ["Orchestrator: starting parallel collection across 8 agents"]}


async def aggregator_node(state: GraphState) -> dict:
    aggregated = AggregatorAgent().run(state)
    return {
        "aggregated_articles": aggregated,
        "execution_logs": [f"AggregatorAgent: merged {len(aggregated)} articles from all sources"],
    }


async def deduplication_node(state: GraphState) -> dict:
    deduped = await DeduplicationAgent().run(state.get("aggregated_articles", []))
    removed = len(state.get("aggregated_articles", [])) - len(deduped)
    return {
        "deduplicated_articles": deduped,
        "execution_logs": [f"DeduplicationAgent: removed {removed} near-duplicate articles"],
    }


async def ranking_node(state: GraphState) -> dict:
    ranked = RankingAgent().run(state.get("deduplicated_articles", []))
    return {
        "ranked_news": ranked,
        "execution_logs": [f"RankingAgent: selected {len(ranked)} top-ranked articles"],
    }


def route_after_ranking(state: GraphState) -> str:
    """Conditional edge: skip LLM generation entirely when there is nothing to report."""
    return "generate" if state.get("ranked_news") else "no_content"


async def no_content_fallback_node(state: GraphState) -> dict:  # noqa: ARG001
    today = datetime.now(UTC).strftime("%B %d, %Y")
    content = NewsletterContent(
        subject=f"AI Newsletter - {today} (No Major Updates)",
        executive_summary=(
            "No significant AI developments cleared the relevance threshold in this "
            "collection window. All sources were checked; the pipeline will report "
            "fresh coverage in the next scheduled run."
        ),
        sections=[],
        one_thing_to_watch="No standout story to highlight today.",
        generated_at=datetime.now(UTC),
    )
    return {
        "newsletter_content": content,
        "execution_logs": [
            "NoContentFallback: no ranked articles, generated placeholder newsletter"
        ],
    }


async def newsletter_generator_node(state: GraphState) -> dict:
    content = await NewsletterGeneratorAgent().run(state.get("ranked_news", []))
    return {
        "newsletter_content": content,
        "execution_logs": [f"NewsletterGeneratorAgent: generated content ('{content.subject}')"],
    }


async def html_formatter_node(state: GraphState) -> dict:
    content = state.get("newsletter_content")
    if content is None:
        return {"errors": ["HTMLFormatterAgent: no newsletter_content available to render"]}

    output = HTMLFormatterAgent().run(content)
    return {
        "newsletter_html": output.html,
        "newsletter_markdown": output.markdown,
        "newsletter_json": output.json_payload,
        "execution_logs": ["HTMLFormatterAgent: rendered HTML, Markdown, and JSON outputs"],
    }
