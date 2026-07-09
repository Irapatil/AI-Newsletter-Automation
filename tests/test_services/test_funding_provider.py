"""Tests for the funding provider abstraction (Crunchbase + Google News fallback)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.funding_provider import (
    CrunchbaseFundingProvider,
    GoogleNewsFundingProvider,
    _extract_amount_usd,
    get_funding_provider,
)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Startup raises $50 million in Series B", 50_000_000.0),
        ("Company secures $1.2 billion valuation", 1_200_000_000.0),
        ("No amount mentioned here", None),
    ],
)
def test_extract_amount_usd(title: str, expected: float | None) -> None:
    assert _extract_amount_usd(title) == expected


def test_get_funding_provider_uses_crunchbase_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CRUNCHBASE_API_KEY", "cb-test-key")
    assert isinstance(get_funding_provider(), CrunchbaseFundingProvider)


def test_get_funding_provider_falls_back_to_google_news(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRUNCHBASE_API_KEY", "")
    assert isinstance(get_funding_provider(), GoogleNewsFundingProvider)


@pytest.mark.asyncio
async def test_google_news_funding_provider_parses_entries() -> None:
    rss_body = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>Acme AI raises $10 million in seed round</title>
        <link>https://example.com/funding/1</link>
        <description>Acme AI secures new investment.</description>
        <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
      </item>
    </channel></rss>"""
    with respx.mock:
        respx.get(url__regex=r".*news\.google\.com.*").mock(
            return_value=httpx.Response(200, text=rss_body)
        )
        rounds = await GoogleNewsFundingProvider().fetch_recent_funding_rounds(max_results=5)

    assert len(rounds) == 1
    assert rounds[0]["amount_usd"] == 10_000_000.0
    assert rounds[0]["company"] == "Acme AI"
