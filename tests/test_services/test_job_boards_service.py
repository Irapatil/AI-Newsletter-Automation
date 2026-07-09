"""Tests for the Greenhouse/Lever public job-board clients."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.services.job_boards_service import fetch_greenhouse_jobs, fetch_lever_postings


@pytest.mark.asyncio
async def test_fetch_greenhouse_jobs_filters_to_ai_roles() -> None:
    payload = {
        "jobs": [
            {
                "title": "Senior Machine Learning Engineer",
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
                "updated_at": "2024-01-01T12:00:00Z",
                "location": {"name": "Remote"},
                "content": "<p>Join our ML team.</p>",
            },
            {
                "title": "Senior Accountant",
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/2",
                "updated_at": "2024-01-01T12:00:00Z",
                "location": {"name": "New York"},
                "content": "<p>Join our finance team.</p>",
            },
        ]
    }
    with respx.mock:
        respx.get(url__regex=r".*boards-api\.greenhouse\.io.*").mock(
            return_value=httpx.Response(200, json=payload)
        )
        postings = await fetch_greenhouse_jobs("acme")

    assert len(postings) == 1
    assert postings[0]["title"] == "Senior Machine Learning Engineer"
    assert postings[0]["company"] == "acme"


@pytest.mark.asyncio
async def test_fetch_lever_postings_filters_to_ai_roles() -> None:
    payload = [
        {
            "text": "AI Research Scientist",
            "hostedUrl": "https://jobs.lever.co/acme/1",
            "createdAt": 1704110400000,
            "categories": {"location": "Toronto"},
            "descriptionHtml": "<p>Research role.</p>",
        },
        {
            "text": "Office Manager",
            "hostedUrl": "https://jobs.lever.co/acme/2",
            "createdAt": 1704110400000,
            "categories": {"location": "Toronto"},
            "descriptionHtml": "<p>Admin role.</p>",
        },
    ]
    with respx.mock:
        respx.get(url__regex=r".*api\.lever\.co.*").mock(
            return_value=httpx.Response(200, json=payload)
        )
        postings = await fetch_lever_postings("acme")

    assert len(postings) == 1
    assert postings[0]["title"] == "AI Research Scientist"


@pytest.mark.asyncio
async def test_fetch_greenhouse_jobs_returns_empty_on_404() -> None:
    with respx.mock:
        respx.get(url__regex=r".*boards-api\.greenhouse\.io.*").mock(
            return_value=httpx.Response(404)
        )
        postings = await fetch_greenhouse_jobs("unknown-board")

    assert postings == []
