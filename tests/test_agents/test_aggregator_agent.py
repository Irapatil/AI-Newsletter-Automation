"""Tests for the aggregator agent that merges collector outputs."""

from __future__ import annotations

from app.agents.aggregator_agent import AggregatorAgent
from app.models.state import build_initial_state
from tests.conftest import make_article


def test_aggregator_merges_all_collector_state_keys():
    state = build_initial_state()
    state["global_news"] = [make_article(title="Global 1")]
    state["research"] = [make_article(title="Research 1"), make_article(title="Research 2")]

    merged = AggregatorAgent().run(state)

    assert len(merged) == 3
    assert {a.title for a in merged} == {"Global 1", "Research 1", "Research 2"}


def test_aggregator_handles_empty_state():
    state = build_initial_state()
    assert AggregatorAgent().run(state) == []
