"""LangGraph StateGraph definition for the AI newsletter pipeline.

    START -> orchestrator -> [8 collector agents in parallel] -> aggregator
          -> deduplication -> ranking -> (conditional) -> newsletter_generator
          -> html_formatter -> END
                             \\-> no_content_fallback -----------^

Parallel fan-out: the orchestrator has an edge to each of the eight
collector nodes, and every collector node has an edge into `aggregator`.
LangGraph only executes `aggregator` once all eight predecessors for the
current superstep have completed, giving deterministic fan-out/fan-in with
no manual synchronization code.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy

from app.agents.company_news_agent import CompanyNewsAgent
from app.agents.funding_agent import FundingAgent
from app.agents.global_news_agent import GlobalNewsAgent
from app.agents.model_release_agent import ModelReleaseAgent
from app.agents.opensource_agent import OpenSourceAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.research_agent import ResearchAgent
from app.agents.talent_agent import TalentAgent
from app.graph.nodes import (
    aggregator_node,
    deduplication_node,
    html_formatter_node,
    make_collector_node,
    newsletter_generator_node,
    no_content_fallback_node,
    orchestrator_node,
    ranking_node,
    route_after_ranking,
)
from app.models.state import GraphState

_COLLECTOR_AGENTS = [
    GlobalNewsAgent(),
    CompanyNewsAgent(),
    FundingAgent(),
    TalentAgent(),
    ResearchAgent(),
    OpenSourceAgent(),
    PolicyAgent(),
    ModelReleaseAgent(),
]

_NETWORK_RETRY = RetryPolicy(max_attempts=3, initial_interval=1.0, backoff_factor=2.0)


def build_workflow() -> CompiledStateGraph:
    """Construct and compile the LangGraph newsletter workflow."""
    graph = StateGraph(GraphState)

    graph.add_node("orchestrator", orchestrator_node)

    for agent in _COLLECTOR_AGENTS:
        node_name = f"{agent.state_key}_collector"
        graph.add_node(node_name, make_collector_node(agent), retry=_NETWORK_RETRY)
        graph.add_edge("orchestrator", node_name)
        graph.add_edge(node_name, "aggregator")

    graph.add_node("aggregator", aggregator_node)
    graph.add_node("deduplication", deduplication_node, retry=_NETWORK_RETRY)
    graph.add_node("ranking", ranking_node)
    graph.add_node("newsletter_generator", newsletter_generator_node, retry=_NETWORK_RETRY)
    graph.add_node("no_content_fallback", no_content_fallback_node)
    graph.add_node("html_formatter", html_formatter_node)

    graph.add_edge(START, "orchestrator")
    graph.add_edge("aggregator", "deduplication")
    graph.add_edge("deduplication", "ranking")
    graph.add_conditional_edges(
        "ranking",
        route_after_ranking,
        {"generate": "newsletter_generator", "no_content": "no_content_fallback"},
    )
    graph.add_edge("newsletter_generator", "html_formatter")
    graph.add_edge("no_content_fallback", "html_formatter")
    graph.add_edge("html_formatter", END)

    return graph.compile()


@lru_cache
def get_compiled_workflow() -> CompiledStateGraph:
    """Process-wide cached compiled graph (compilation is not free)."""
    return build_workflow()
