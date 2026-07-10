"""LangGraph node functions - thin adapters between agents and shared state.

Every node returns only the state keys it owns, so LangGraph can safely run
the eight collector nodes in parallel: each writes to its own dedicated
field, and `execution_logs`/`errors`/`agent_execution` are merged via the
`operator.add` reducer declared on `GraphState`.

Every node is wrapped with a stopwatch that records an `AgentExecutionRecord`
(node name, elapsed time, items processed) into `agent_execution` on
successful completion - pure observability, layered around each agent's
existing call rather than inside it. A node that raises still propagates
the exception untouched (no record is added, no behavior changes), so
graph-level retry policies and the route handler's error handling work
exactly as they did before this instrumentation existed.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from app.agents.aggregator_agent import AggregatorAgent
from app.agents.base_agent import BaseCollectorAgent
from app.agents.deduplication_agent import DeduplicationAgent
from app.agents.html_formatter_agent import HTMLFormatterAgent
from app.agents.newsletter_generator_agent import NewsletterGeneratorAgent
from app.agents.ranking_agent import RankingAgent
from app.config.logging_config import get_logger
from app.models.newsletter import AgentExecutionRecord, NewsletterContent
from app.models.state import GraphState

logger = get_logger(__name__)

NodeFn = Callable[[GraphState], Awaitable[dict]]


def _execution_record(node: str, started_at: float, items_processed: int) -> AgentExecutionRecord:
    return AgentExecutionRecord(
        node=node,
        execution_time_seconds=round(time.monotonic() - started_at, 3),
        items_processed=items_processed,
    )


def make_collector_node(agent: BaseCollectorAgent) -> NodeFn:
    async def _node(
        state: GraphState,
    ) -> dict:  # noqa: ARG001 - state unused, agent is self-contained
        started_at = time.monotonic()
        result = await agent.collect()
        return {
            agent.state_key: result.articles,
            "execution_logs": result.logs,
            "errors": result.errors,
            "agent_execution": [
                _execution_record(agent.display_name, started_at, len(result.articles))
            ],
        }

    _node.__name__ = f"{agent.state_key}_collector"
    return _node


async def orchestrator_node(state: GraphState) -> dict:  # noqa: ARG001
    started_at = time.monotonic()
    logger.info("workflow_started")
    return {
        "execution_logs": ["Orchestrator: starting parallel collection across 8 agents"],
        "agent_execution": [_execution_record("Orchestrator", started_at, 8)],
    }


async def aggregator_node(state: GraphState) -> dict:
    started_at = time.monotonic()
    aggregated = AggregatorAgent().run(state)
    return {
        "aggregated_articles": aggregated,
        "execution_logs": [f"AggregatorAgent: merged {len(aggregated)} articles from all sources"],
        "agent_execution": [_execution_record("AggregatorAgent", started_at, len(aggregated))],
    }


async def deduplication_node(state: GraphState) -> dict:
    started_at = time.monotonic()
    deduped = await DeduplicationAgent().run(state.get("aggregated_articles", []))
    removed = len(state.get("aggregated_articles", [])) - len(deduped)
    return {
        "deduplicated_articles": deduped,
        "execution_logs": [f"DeduplicationAgent: removed {removed} near-duplicate articles"],
        "agent_execution": [_execution_record("DeduplicationAgent", started_at, len(deduped))],
    }


async def ranking_node(state: GraphState) -> dict:
    started_at = time.monotonic()
    ranked = RankingAgent().run(state.get("deduplicated_articles", []))
    return {
        "ranked_news": ranked,
        "execution_logs": [f"RankingAgent: selected {len(ranked)} top-ranked articles"],
        "agent_execution": [_execution_record("RankingAgent", started_at, len(ranked))],
    }


def route_after_ranking(state: GraphState) -> str:
    """Conditional edge: skip LLM generation entirely when there is nothing to report."""
    return "generate" if state.get("ranked_news") else "no_content"


async def no_content_fallback_node(state: GraphState) -> dict:  # noqa: ARG001
    started_at = time.monotonic()
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
        "agent_execution": [_execution_record("NoContentFallback", started_at, 0)],
    }


async def newsletter_generator_node(state: GraphState) -> dict:
    started_at = time.monotonic()
    content = await NewsletterGeneratorAgent().run(state.get("ranked_news", []))
    articles_summarized = sum(len(section.articles) for section in content.sections)
    return {
        "newsletter_content": content,
        "execution_logs": [f"NewsletterGeneratorAgent: generated content ('{content.subject}')"],
        "agent_execution": [
            _execution_record("NewsletterGeneratorAgent", started_at, articles_summarized)
        ],
    }


async def html_formatter_node(state: GraphState) -> dict:
    started_at = time.monotonic()
    content = state.get("newsletter_content")
    if content is None:
        return {"errors": ["HTMLFormatterAgent: no newsletter_content available to render"]}

    output = HTMLFormatterAgent().run(content)
    articles_rendered = sum(len(section.articles) for section in content.sections)
    return {
        "newsletter_html": output.html,
        "newsletter_markdown": output.markdown,
        "newsletter_json": output.json_payload,
        "execution_logs": ["HTMLFormatterAgent: rendered HTML, Markdown, and JSON outputs"],
        "agent_execution": [_execution_record("HTMLFormatterAgent", started_at, articles_rendered)],
    }
