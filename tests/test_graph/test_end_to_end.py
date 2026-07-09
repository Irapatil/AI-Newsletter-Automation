"""End-to-end integration test for the compiled LangGraph workflow.

Unit tests cover every agent/service in isolation, but nothing previously
exercised the *wiring* between them: parallel fan-out across the 8 collector
nodes, the `operator.add` state reducers merging concurrent writes,
aggregation, deduplication, ranking, generation, and HTML formatting all
running together through a single real `ainvoke()` call. This test stubs
only each collector agent's `fetch()` - the external I/O boundary
`BaseCollectorAgent.collect()` already wraps - so everything else (the real
graph, real nodes, real reducers, real downstream agents) runs for real.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.agents.company_news_agent import CompanyNewsAgent
from app.agents.funding_agent import FundingAgent
from app.agents.global_news_agent import GlobalNewsAgent
from app.agents.model_release_agent import ModelReleaseAgent
from app.agents.opensource_agent import OpenSourceAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.research_agent import ResearchAgent
from app.agents.talent_agent import TalentAgent
from app.graph.workflow import build_workflow
from app.models.state import build_initial_state
from tests.conftest import make_article

COLLECTOR_AGENT_CLASSES = [
    GlobalNewsAgent,
    CompanyNewsAgent,
    FundingAgent,
    TalentAgent,
    ResearchAgent,
    OpenSourceAgent,
    PolicyAgent,
    ModelReleaseAgent,
]


@pytest.fixture(autouse=True)
def _stub_collector_fetches(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(UTC)

    for agent_cls in COLLECTOR_AGENT_CLASSES:

        async def _fake_fetch(self, _agent_cls=agent_cls):
            return [
                make_article(
                    title=f"{_agent_cls.display_name} story {i}",
                    url=f"https://example.com/{_agent_cls.display_name.lower()}/{i}",
                    category=_agent_cls.category,
                    published_at=now - timedelta(hours=i),
                )
                for i in range(2)
            ]

        monkeypatch.setattr(agent_cls, "fetch", _fake_fetch)


@pytest.mark.asyncio
async def test_full_pipeline_runs_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    workflow = build_workflow()
    final_state = await workflow.ainvoke(build_initial_state())

    assert final_state["errors"] == []

    # Every one of the 8 parallel collector branches merged its own log line
    # in via the `execution_logs` reducer - proof the fan-out/fan-in and
    # `operator.add` merge actually happened, not just that the graph compiles.
    for agent_cls in COLLECTOR_AGENT_CLASSES:
        assert any(
            agent_cls.display_name in log for log in final_state["execution_logs"]
        ), f"missing execution log for {agent_cls.display_name}"

    assert len(final_state["aggregated_articles"]) == len(COLLECTOR_AGENT_CLASSES) * 2
    assert final_state["deduplicated_articles"]
    assert final_state["ranked_news"]

    content = final_state["newsletter_content"]
    assert content is not None
    assert content.subject
    assert content.executive_summary
    assert len(content.sections) >= 2
    for section in content.sections:
        for article in section.articles:
            assert article.ai_summary

    assert final_state["newsletter_html"]
    assert "<html" in final_state["newsletter_html"].lower()
    assert final_state["newsletter_markdown"]
    assert final_state["newsletter_json"]


@pytest.mark.asyncio
async def test_full_pipeline_takes_no_content_branch_when_nothing_survives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    for agent_cls in COLLECTOR_AGENT_CLASSES:

        async def _empty_fetch(self):
            return []

        monkeypatch.setattr(agent_cls, "fetch", _empty_fetch)

    workflow = build_workflow()
    final_state = await workflow.ainvoke(build_initial_state())

    content = final_state["newsletter_content"]
    assert content is not None
    assert content.sections == []
    assert final_state["newsletter_html"]
    assert "<html" in final_state["newsletter_html"].lower()
