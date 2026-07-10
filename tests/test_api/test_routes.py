"""Tests for the FastAPI routes, with the LangGraph workflow mocked out."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.api.routes as routes_module
from app.main import app
from app.models.newsletter import NewsletterContent, NewsletterSection
from tests.conftest import make_article


class _FakeCompiledGraph:
    def __init__(self, final_state: dict) -> None:
        self._final_state = final_state

    async def ainvoke(self, _initial_state: dict) -> dict:
        return self._final_state


def _canned_final_state(*, errors: list[str] | None = None) -> dict:
    article = make_article(
        title="Test Article", url="https://example.com/1", source="TechCrunch AI"
    )
    other_article = make_article(title="Other Article", url="https://example.com/2", source="arXiv")
    content = NewsletterContent(
        subject="Test Subject",
        executive_summary="Test summary.",
        sections=[NewsletterSection(key="global_news", title="Global", articles=[article])],
        one_thing_to_watch="Watch this.",
        generated_at=datetime.now(UTC),
    )
    return {
        "newsletter_content": content,
        "newsletter_html": "<html>test</html>",
        "newsletter_markdown": "# Test",
        "newsletter_json": {"subject": "Test Subject"},
        "errors": errors or [],
        "aggregated_articles": [article, article, other_article],
        "deduplicated_articles": [article, other_article],
        "ranked_news": [article],
        "agent_execution": [
            {
                "node": "Orchestrator",
                "status": "success",
                "execution_time_seconds": 0.01,
                "items_processed": 8,
            },
            {
                "node": "RankingAgent",
                "status": "success",
                "execution_time_seconds": 0.02,
                "items_processed": 1,
            },
        ],
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("NEWSLETTER_HISTORY_DIR", str(tmp_path))
    monkeypatch.setattr(
        routes_module, "get_compiled_workflow", lambda: _FakeCompiledGraph(_canned_final_state())
    )
    with TestClient(app) as test_client:
        yield test_client


def test_root_returns_metadata(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "AI Newsletter Automation"


def test_cors_allows_configured_frontend_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_preflight_allows_x_api_key_header(client: TestClient) -> None:
    response = client.options(
        "/generate-newsletter",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unconfigured_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://evil.example.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body["providers"].keys()) == {
        "api",
        "openai",
        "newsapi",
        "github",
        "rss",
        "langgraph",
    }
    assert body["providers"]["api"] == "ok"
    assert body["providers"]["langgraph"] == "operational"


def test_health_reports_openai_mock_when_no_key_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    response = client.get("/health")
    assert response.json()["providers"]["openai"] == "mock"


def test_generate_newsletter_returns_expected_payload(client: TestClient) -> None:
    response = client.post("/generate-newsletter", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "Test Subject"
    assert body["summary"] == "Test summary."
    assert body["newsletter_html"] == "<html>test</html>"
    assert body["newsletter_json"] == {"subject": "Test Subject"}
    assert body["statistics"] == {
        "aggregated_count": 3,
        "duplicates_removed": 1,
        "ranked_count": 1,
        "stories_selected": 1,
    }
    assert body["sources_used"] == ["TechCrunch AI", "arXiv"]
    assert body["status"] == "success"
    assert body["provider"] == "mock"
    assert body["execution_time_seconds"] >= 0
    assert body["token_usage"]["is_estimated"] is True
    assert body["estimated_cost_usd"] >= 0
    assert [rec["node"] for rec in body["agent_execution"]] == ["Orchestrator", "RankingAgent"]
    assert body["errors"] == []


def test_generate_newsletter_reports_partial_success_with_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEWSLETTER_HISTORY_DIR", str(tmp_path))
    monkeypatch.setattr(
        routes_module,
        "get_compiled_workflow",
        lambda: _FakeCompiledGraph(
            _canned_final_state(errors=["FundingAgent: failed after 12.0s"])
        ),
    )
    with TestClient(app) as test_client:
        response = test_client.post("/generate-newsletter", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial_success"
    assert body["errors"] == ["FundingAgent: failed after 12.0s"]


def test_generate_newsletter_persists_to_history(client: TestClient) -> None:
    client.post("/generate-newsletter", json={})
    history = client.get("/newsletter/history")
    assert history.status_code == 200
    assert history.json()["count"] == 1

    latest = client.get("/newsletter/latest")
    assert latest.status_code == 200
    assert latest.json()["subject"] == "Test Subject"


def test_newsletter_latest_404_when_none_generated(client: TestClient) -> None:
    response = client.get("/newsletter/latest")
    assert response.status_code == 404


def test_newsletter_latest_html_returns_raw_html(client: TestClient) -> None:
    client.post("/generate-newsletter", json={})
    response = client.get("/newsletter/latest/html")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == "<html>test</html>"


def test_newsletter_latest_html_404_when_none_generated(client: TestClient) -> None:
    response = client.get("/newsletter/latest/html")
    assert response.status_code == 404


def test_demo_generate_returns_compact_payload(client: TestClient) -> None:
    response = client.post("/demo/generate")
    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "Test Subject"
    assert body["html_preview_url"] == "/newsletter/latest/html"
    assert "newsletter_html" not in body
    assert body["newsletter_markdown"] == "# Test"
    assert body["statistics"]["aggregated_count"] == 3
    assert [rec["node"] for rec in body["agent_execution"]] == ["Orchestrator", "RankingAgent"]

    # The demo endpoint persists to history exactly like generate-newsletter.
    html_response = client.get("/newsletter/latest/html")
    assert html_response.status_code == 200
    assert html_response.text == "<html>test</html>"


def test_generate_newsletter_requires_api_key_when_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEWSLETTER_HISTORY_DIR", str(tmp_path))
    monkeypatch.setenv("API_AUTH_TOKEN", "super-secret")
    monkeypatch.setattr(
        routes_module, "get_compiled_workflow", lambda: _FakeCompiledGraph(_canned_final_state())
    )

    with TestClient(app) as test_client:
        unauthorized = test_client.post("/generate-newsletter", json={})
        assert unauthorized.status_code == 401

        authorized = test_client.post(
            "/generate-newsletter", json={}, headers={"X-API-Key": "super-secret"}
        )
        assert authorized.status_code == 200
