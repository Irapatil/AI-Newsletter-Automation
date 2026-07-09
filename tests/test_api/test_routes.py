"""Tests for the FastAPI routes, with the LangGraph workflow mocked out."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.api.routes as routes_module
from app.main import app
from app.models.newsletter import NewsletterContent


class _FakeCompiledGraph:
    def __init__(self, final_state: dict) -> None:
        self._final_state = final_state

    async def ainvoke(self, _initial_state: dict) -> dict:
        return self._final_state


def _canned_final_state() -> dict:
    content = NewsletterContent(
        subject="Test Subject",
        executive_summary="Test summary.",
        sections=[],
        one_thing_to_watch="Watch this.",
        generated_at=datetime.now(UTC),
    )
    return {
        "newsletter_content": content,
        "newsletter_html": "<html>test</html>",
        "newsletter_markdown": "# Test",
        "newsletter_json": {"subject": "Test Subject"},
        "errors": [],
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


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_newsletter_returns_expected_payload(client: TestClient) -> None:
    response = client.post("/generate-newsletter", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "Test Subject"
    assert body["summary"] == "Test summary."
    assert body["html"] == "<html>test</html>"
    assert body["json"] == {"subject": "Test Subject"}


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
