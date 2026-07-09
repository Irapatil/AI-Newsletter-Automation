"""LinkedIn Jobs provider abstraction.

LinkedIn does not expose a public jobs-search API; a live integration
requires a LinkedIn Talent/Partner API agreement and OAuth credentials. This
module defines the provider interface so a real implementation can be
dropped in later, while a `mock` implementation (the default) supplies
realistic sample data so the TalentAgent and the rest of the pipeline are
always exercisable end-to-end.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.services.job_boards_service import JobPosting

logger = get_logger(__name__)

_SAMPLE_TITLES: list[tuple[str, str, str]] = [
    ("Senior Machine Learning Engineer", "Stripe", "Remote - US"),
    ("AI Research Scientist, LLM Alignment", "Cohere", "Toronto, Canada"),
    ("Applied AI Engineer", "Databricks", "San Francisco, CA"),
    ("Machine Learning Infrastructure Engineer", "Snowflake", "Remote - US"),
    ("Generative AI Solutions Architect", "Salesforce", "New York, NY"),
]


class LinkedInJobsProvider(ABC):
    """Abstract provider for LinkedIn-sourced AI talent signal."""

    @abstractmethod
    async def fetch_ai_jobs(self, max_results: int = 10) -> list[JobPosting]:
        raise NotImplementedError


class MockLinkedInJobsProvider(LinkedInJobsProvider):
    """Deterministic sample data used when no LinkedIn partner API is configured."""

    async def fetch_ai_jobs(self, max_results: int = 10) -> list[JobPosting]:
        now = datetime.now(UTC)
        postings = [
            JobPosting(
                title=title,
                url="https://www.linkedin.com/jobs/",
                company=company,
                location=location,
                published_at=now - timedelta(hours=index * 6),
                snippet=(
                    f"{title} role at {company} ({location}). Sample data - configure "
                    "LINKEDIN_JOBS_PROVIDER=api with partner credentials for live postings."
                ),
            )
            for index, (title, company, location) in enumerate(_SAMPLE_TITLES)
        ]
        return postings[:max_results]


class ApiLinkedInJobsProvider(LinkedInJobsProvider):
    """Placeholder for a real LinkedIn Talent/Partner API integration.

    Requires an authorized partner agreement; without one, this degrades
    gracefully to an empty result rather than failing the pipeline.
    """

    async def fetch_ai_jobs(self, max_results: int = 10) -> list[JobPosting]:
        logger.warning(
            "linkedin_api_provider_not_configured",
            hint="Set a partner-authorized client and implement fetch_ai_jobs, "
            "or leave LINKEDIN_JOBS_PROVIDER=mock.",
        )
        return []


def get_linkedin_provider() -> LinkedInJobsProvider:
    settings = get_settings()
    if settings.linkedin_jobs_provider == "api" and settings.linkedin_api_key:
        return ApiLinkedInJobsProvider()
    return MockLinkedInJobsProvider()
