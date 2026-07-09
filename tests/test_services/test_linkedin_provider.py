"""Tests for the LinkedIn Jobs provider abstraction."""

from __future__ import annotations

import pytest

from app.services.linkedin_provider import (
    ApiLinkedInJobsProvider,
    MockLinkedInJobsProvider,
    get_linkedin_provider,
)

REQUIRED_FIELDS = ("title", "url", "company", "location", "published_at", "snippet")


@pytest.mark.asyncio
async def test_mock_provider_returns_populated_job_postings() -> None:
    postings = await MockLinkedInJobsProvider().fetch_ai_jobs()

    assert len(postings) > 0
    for posting in postings:
        for field in REQUIRED_FIELDS:
            assert posting[field]


@pytest.mark.asyncio
async def test_mock_provider_respects_max_results() -> None:
    postings = await MockLinkedInJobsProvider().fetch_ai_jobs(max_results=2)

    assert len(postings) == 2


@pytest.mark.asyncio
async def test_api_provider_returns_empty_list_without_raising() -> None:
    postings = await ApiLinkedInJobsProvider().fetch_ai_jobs()

    assert postings == []


def test_get_linkedin_provider_defaults_to_mock() -> None:
    assert isinstance(get_linkedin_provider(), MockLinkedInJobsProvider)


def test_get_linkedin_provider_returns_api_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LINKEDIN_JOBS_PROVIDER", "api")
    monkeypatch.setenv("LINKEDIN_API_KEY", "linkedin-test-key")

    assert isinstance(get_linkedin_provider(), ApiLinkedInJobsProvider)


def test_get_linkedin_provider_falls_back_to_mock_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LINKEDIN_JOBS_PROVIDER", "api")
    monkeypatch.setenv("LINKEDIN_API_KEY", "")

    assert isinstance(get_linkedin_provider(), MockLinkedInJobsProvider)
