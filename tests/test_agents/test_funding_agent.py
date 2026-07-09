"""Tests for FundingAgent: provider-to-Article mapping and datetime coercion."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agents.funding_agent import FundingAgent, _coerce_datetime
from app.models.article import NewsCategory
from app.services.funding_provider import FundingProvider, FundingRound


class _StubFundingProvider(FundingProvider):
    """Fake provider returning a fixed list of FundingRound dicts."""

    display_name = "Stub"

    def __init__(self, rounds: list[FundingRound]) -> None:
        self._rounds = rounds

    async def fetch_recent_funding_rounds(self, max_results: int = 15) -> list[FundingRound]:
        return self._rounds[:max_results]


def _make_round(**overrides) -> FundingRound:
    base: FundingRound = {
        "title": "Acme AI raises $50 million in Series B",
        "url": "https://example.com/funding/acme",
        "company": "Acme AI",
        "amount_usd": 50_000_000.0,
        "published_at": "2024-01-15T10:30:00Z",
        "snippet": "Acme AI secures new funding.",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_fetch_maps_funding_rounds_to_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_dt = datetime(2024, 2, 1, tzinfo=UTC)
    rounds = [
        _make_round(),
        _make_round(
            title="Beta Corp raises $1 billion",
            url="https://example.com/funding/beta",
            company="Beta Corp",
            amount_usd=1_000_000_000.0,
            published_at=fixed_dt,
            snippet="Beta Corp secures massive round.",
        ),
    ]
    stub_provider = _StubFundingProvider(rounds)
    monkeypatch.setattr("app.agents.funding_agent.get_funding_provider", lambda: stub_provider)

    articles = await FundingAgent().fetch()

    assert len(articles) == 2

    first, second = articles
    assert first.title == "Acme AI raises $50 million in Series B"
    assert first.url == "https://example.com/funding/acme"
    assert first.category == NewsCategory.FUNDING
    assert first.source == "Stub"
    assert first.metadata == {"company": "Acme AI", "amount_usd": 50_000_000.0}
    assert isinstance(first.published_at, datetime)
    assert first.published_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

    assert second.title == "Beta Corp raises $1 billion"
    assert second.category == NewsCategory.FUNDING
    assert second.metadata == {"company": "Beta Corp", "amount_usd": 1_000_000_000.0}
    assert second.published_at == fixed_dt


@pytest.mark.asyncio
async def test_fetch_skips_rounds_with_no_url(monkeypatch: pytest.MonkeyPatch) -> None:
    rounds = [_make_round(url="")]
    monkeypatch.setattr(
        "app.agents.funding_agent.get_funding_provider",
        lambda: _StubFundingProvider(rounds),
    )

    articles = await FundingAgent().fetch()

    assert articles == []


def test_coerce_datetime_parses_iso_string() -> None:
    result = _coerce_datetime("2024-01-15T10:30:00Z")

    assert isinstance(result, datetime)
    assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)


def test_coerce_datetime_falls_back_to_now_on_unparseable_string() -> None:
    before = datetime.now(UTC)
    result = _coerce_datetime("not a real date at all !!!")
    after = datetime.now(UTC)

    assert isinstance(result, datetime)
    assert before <= result <= after


def test_coerce_datetime_passes_through_existing_datetime() -> None:
    value = datetime(2023, 6, 1, 12, 0, 0, tzinfo=UTC)

    result = _coerce_datetime(value)

    assert result is value
