"""Tests for TalentAgent: Greenhouse/Lever/LinkedIn aggregation into Articles.

The underlying `job_boards_service.fetch_greenhouse_jobs` /
`fetch_lever_postings` functions and `linkedin_provider.get_linkedin_provider`
are monkeypatched at the names imported into `app.agents.talent_agent`, so no
real HTTP is involved (HTTP-level behavior, including AI-keyword filtering,
is already covered by tests/test_services/test_job_boards_service.py).
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.agents.talent_agent import TalentAgent
from app.models.article import NewsCategory
from app.services.job_boards_service import JobPosting
from app.services.linkedin_provider import LinkedInJobsProvider


def _make_posting(**overrides) -> JobPosting:
    base: JobPosting = {
        "title": "Senior Machine Learning Engineer",
        "url": "https://boards.greenhouse.io/acme/jobs/1",
        "company": "acme",
        "location": "Remote",
        "published_at": datetime(2024, 1, 1, tzinfo=UTC),
        "snippet": "Join our ML team.",
    }
    base.update(overrides)
    return base


class _StubLinkedInProvider(LinkedInJobsProvider):
    """Fake LinkedIn provider returning a fixed list of JobPostings."""

    def __init__(self, postings: list[JobPosting]) -> None:
        self._postings = postings

    async def fetch_ai_jobs(self, max_results: int = 10) -> list[JobPosting]:
        return self._postings[:max_results]


@pytest.mark.asyncio
async def test_fetch_combines_greenhouse_lever_and_linkedin_into_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "acme")
    monkeypatch.setenv("LEVER_COMPANY_SLUGS", "beta")

    greenhouse_posting = _make_posting(
        title="Senior Machine Learning Engineer",
        url="https://boards.greenhouse.io/acme/jobs/1",
        company="acme",
        location="Remote",
    )
    lever_posting = _make_posting(
        title="AI Research Scientist",
        url="https://jobs.lever.co/beta/1",
        company="beta",
        location="Toronto",
    )
    linkedin_posting = _make_posting(
        title="Applied AI Engineer",
        url="https://www.linkedin.com/jobs/view/sample-1",
        company="Databricks",
        location="San Francisco, CA",
    )

    async def fake_fetch_greenhouse_jobs(board_token: str) -> list[JobPosting]:
        assert board_token == "acme"
        return [greenhouse_posting]

    async def fake_fetch_lever_postings(company_slug: str) -> list[JobPosting]:
        assert company_slug == "beta"
        return [lever_posting]

    monkeypatch.setattr("app.agents.talent_agent.fetch_greenhouse_jobs", fake_fetch_greenhouse_jobs)
    monkeypatch.setattr("app.agents.talent_agent.fetch_lever_postings", fake_fetch_lever_postings)
    monkeypatch.setattr(
        "app.agents.talent_agent.get_linkedin_provider",
        lambda: _StubLinkedInProvider([linkedin_posting]),
    )

    articles = await TalentAgent().fetch()

    assert len(articles) == 3
    for article in articles:
        assert article.category == NewsCategory.TALENT

    by_title = {article.title: article for article in articles}

    greenhouse_article = by_title["Senior Machine Learning Engineer at acme"]
    assert greenhouse_article.url == "https://boards.greenhouse.io/acme/jobs/1"
    assert greenhouse_article.source == "Greenhouse/Lever"
    assert greenhouse_article.metadata == {"company": "acme", "location": "Remote"}

    lever_article = by_title["AI Research Scientist at beta"]
    assert lever_article.url == "https://jobs.lever.co/beta/1"
    assert lever_article.source == "Greenhouse/Lever"
    assert lever_article.metadata == {"company": "beta", "location": "Toronto"}

    linkedin_article = by_title["Applied AI Engineer at Databricks"]
    assert linkedin_article.url == "https://www.linkedin.com/jobs/view/sample-1"
    assert linkedin_article.source == "LinkedIn Jobs"
    assert linkedin_article.metadata == {
        "company": "Databricks",
        "location": "San Francisco, CA",
    }


@pytest.mark.asyncio
async def test_fetch_skips_postings_with_no_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "acme")
    monkeypatch.setenv("LEVER_COMPANY_SLUGS", "")

    async def fake_fetch_greenhouse_jobs(board_token: str) -> list[JobPosting]:
        return [_make_posting(url="", title="No URL role"), _make_posting(url="https://x/1")]

    async def fake_fetch_lever_postings(company_slug: str) -> list[JobPosting]:
        return []

    monkeypatch.setattr("app.agents.talent_agent.fetch_greenhouse_jobs", fake_fetch_greenhouse_jobs)
    monkeypatch.setattr("app.agents.talent_agent.fetch_lever_postings", fake_fetch_lever_postings)
    monkeypatch.setattr(
        "app.agents.talent_agent.get_linkedin_provider",
        lambda: _StubLinkedInProvider([]),
    )

    articles = await TalentAgent().fetch()

    assert len(articles) == 1
    assert articles[0].url == "https://x/1"


@pytest.mark.asyncio
async def test_fetch_does_not_re_filter_postings_by_ai_relevance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TalentAgent trusts whatever JobPostings the service layer hands it.

    AI_TALENT_KEYWORDS filtering (see app.config.sources / job_boards_service)
    is applied inside `fetch_greenhouse_jobs`/`fetch_lever_postings` themselves
    (already covered by tests/test_services/test_job_boards_service.py).
    TalentAgent.fetch() does not re-apply any keyword check, so a
    non-AI-relevant posting that somehow reaches it (e.g. via a mocked
    dependency, or a provider bug) is passed straight through as an Article
    rather than being excluded.
    """
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "acme")
    monkeypatch.setenv("LEVER_COMPANY_SLUGS", "")

    ai_posting = _make_posting(title="Machine Learning Engineer", url="https://x/ai")
    non_ai_posting = _make_posting(title="Senior Accountant", url="https://x/accountant")

    async def fake_fetch_greenhouse_jobs(board_token: str) -> list[JobPosting]:
        return [ai_posting, non_ai_posting]

    async def fake_fetch_lever_postings(company_slug: str) -> list[JobPosting]:
        return []

    monkeypatch.setattr("app.agents.talent_agent.fetch_greenhouse_jobs", fake_fetch_greenhouse_jobs)
    monkeypatch.setattr("app.agents.talent_agent.fetch_lever_postings", fake_fetch_lever_postings)
    monkeypatch.setattr(
        "app.agents.talent_agent.get_linkedin_provider",
        lambda: _StubLinkedInProvider([]),
    )

    articles = await TalentAgent().fetch()

    titles = {article.title for article in articles}
    assert titles == {
        "Machine Learning Engineer at acme",
        "Senior Accountant at acme",
    }


@pytest.mark.asyncio
async def test_greenhouse_ai_keyword_filtering_happens_via_real_service_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end check that AI-relevance filtering does occur somewhere.

    Uses the real (unmocked) `fetch_greenhouse_jobs` with respx-mocked HTTP,
    while Lever and LinkedIn are stubbed out, to confirm the filtering
    observed in test_job_boards_service.py also takes effect when driven
    through TalentAgent.fetch().
    """
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "acme")
    monkeypatch.setenv("LEVER_COMPANY_SLUGS", "")

    payload = {
        "jobs": [
            {
                "title": "Machine Learning Engineer",
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

    async def fake_fetch_lever_postings(company_slug: str) -> list[JobPosting]:
        return []

    monkeypatch.setattr("app.agents.talent_agent.fetch_lever_postings", fake_fetch_lever_postings)
    monkeypatch.setattr(
        "app.agents.talent_agent.get_linkedin_provider",
        lambda: _StubLinkedInProvider([]),
    )

    with respx.mock:
        respx.get(url__regex=r".*boards-api\.greenhouse\.io.*").mock(
            return_value=httpx.Response(200, json=payload)
        )
        articles = await TalentAgent().fetch()

    titles = {article.title for article in articles}
    assert titles == {"Machine Learning Engineer at acme"}


@pytest.mark.asyncio
async def test_fetch_source_returning_empty_list_does_not_block_other_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A source that comes back empty (the way job_boards_service already
    handles HTTP failures internally, by catching HttpClientError and
    returning []) does not prevent the other sources' postings from
    appearing in the result.
    """
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "acme")
    monkeypatch.setenv("LEVER_COMPANY_SLUGS", "beta")

    lever_posting = _make_posting(
        title="AI Research Scientist", url="https://jobs.lever.co/beta/1", company="beta"
    )
    linkedin_posting = _make_posting(
        title="Applied AI Engineer",
        url="https://www.linkedin.com/jobs/view/sample-1",
        company="Databricks",
    )

    async def failing_fetch_greenhouse_jobs(board_token: str) -> list[JobPosting]:
        return []

    async def fake_fetch_lever_postings(company_slug: str) -> list[JobPosting]:
        return [lever_posting]

    monkeypatch.setattr(
        "app.agents.talent_agent.fetch_greenhouse_jobs", failing_fetch_greenhouse_jobs
    )
    monkeypatch.setattr("app.agents.talent_agent.fetch_lever_postings", fake_fetch_lever_postings)
    monkeypatch.setattr(
        "app.agents.talent_agent.get_linkedin_provider",
        lambda: _StubLinkedInProvider([linkedin_posting]),
    )

    articles = await TalentAgent().fetch()

    titles = {article.title for article in articles}
    assert titles == {"AI Research Scientist at beta", "Applied AI Engineer at Databricks"}


@pytest.mark.asyncio
async def test_fetch_has_no_per_source_exception_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Documents observed (not necessarily desired) behavior: unlike
    job_boards_service's internal try/except around HTTP errors,
    TalentAgent.fetch() itself wraps the three source calls in plain
    asyncio.gather() without return_exceptions=True and with no per-source
    try/except. If one dependency raises instead of degrading to [],
    the exception propagates out of fetch() and Lever/LinkedIn postings
    that were otherwise available are lost too - collect() then reports
    zero articles for the whole agent rather than a partial result.
    """
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "acme")
    monkeypatch.setenv("LEVER_COMPANY_SLUGS", "beta")

    lever_posting = _make_posting(
        title="AI Research Scientist", url="https://jobs.lever.co/beta/1", company="beta"
    )

    async def raising_fetch_greenhouse_jobs(board_token: str) -> list[JobPosting]:
        raise RuntimeError("simulated unexpected greenhouse failure")

    async def fake_fetch_lever_postings(company_slug: str) -> list[JobPosting]:
        return [lever_posting]

    monkeypatch.setattr(
        "app.agents.talent_agent.fetch_greenhouse_jobs", raising_fetch_greenhouse_jobs
    )
    monkeypatch.setattr("app.agents.talent_agent.fetch_lever_postings", fake_fetch_lever_postings)
    monkeypatch.setattr(
        "app.agents.talent_agent.get_linkedin_provider",
        lambda: _StubLinkedInProvider([]),
    )

    with pytest.raises(RuntimeError, match="simulated unexpected greenhouse failure"):
        await TalentAgent().fetch()

    # Through the public collect() contract, the whole agent's result is
    # dropped - not just the failing source's postings.
    result = await TalentAgent().collect()
    assert result.articles == []
    assert len(result.errors) == 1
    assert "simulated unexpected greenhouse failure" in result.errors[0]
