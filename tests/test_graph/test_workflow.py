"""Tests for the LangGraph workflow structure and conditional routing."""

from __future__ import annotations

import pytest

from app.graph.nodes import no_content_fallback_node, route_after_ranking
from app.graph.workflow import build_workflow
from app.models.state import build_initial_state
from tests.conftest import make_article


def test_build_workflow_compiles_with_expected_nodes():
    compiled = build_workflow()
    node_names = set(compiled.get_graph().nodes.keys())

    expected_collector_nodes = {
        "global_news_collector",
        "company_news_collector",
        "funding_collector",
        "talent_collector",
        "research_collector",
        "opensource_collector",
        "policy_collector",
        "model_releases_collector",
    }
    expected_pipeline_nodes = {
        "orchestrator",
        "aggregator",
        "deduplication",
        "ranking",
        "newsletter_generator",
        "no_content_fallback",
        "html_formatter",
    }
    assert expected_collector_nodes.issubset(node_names)
    assert expected_pipeline_nodes.issubset(node_names)


def test_route_after_ranking_generates_when_articles_present():
    state = build_initial_state()
    state["ranked_news"] = [make_article()]
    assert route_after_ranking(state) == "generate"


def test_route_after_ranking_falls_back_when_empty():
    state = build_initial_state()
    state["ranked_news"] = []
    assert route_after_ranking(state) == "no_content"


@pytest.mark.asyncio
async def test_no_content_fallback_node_produces_placeholder_content():
    state = build_initial_state()
    update = await no_content_fallback_node(state)

    content = update["newsletter_content"]
    assert content.sections == []
    assert "No" in content.executive_summary or "No" in content.subject
