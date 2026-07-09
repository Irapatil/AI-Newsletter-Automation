"""Tests for filesystem-backed newsletter history persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services import history_service


def make_output(
    *,
    subject: str = "Test Subject",
    summary: str = "Test summary",
    timestamp: datetime | None = None,
) -> history_service.NewsletterOutput:
    return history_service.NewsletterOutput(
        subject=subject,
        summary=summary,
        html="<p>hello</p>",
        markdown="hello",
        json_payload={"subject": subject},
        timestamp=timestamp or datetime.now(UTC),
    )


@pytest.fixture(autouse=True)
def _use_tmp_history_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("NEWSLETTER_HISTORY_DIR", str(tmp_path))
    return tmp_path


def test_save_newsletter_writes_json_file_round_trip(tmp_path: Path) -> None:
    output = make_output(subject="Round Trip Subject", timestamp=datetime(2026, 1, 1, tzinfo=UTC))

    path = history_service.save_newsletter(output, "abc123")

    assert path.parent == tmp_path
    assert path.exists()
    assert path.name.endswith("_abc123.json")

    loaded = history_service.get_latest()
    assert loaded is not None
    assert loaded.subject == "Round Trip Subject"
    assert loaded.html == "<p>hello</p>"
    assert loaded.markdown == "hello"
    assert loaded.json_payload == {"subject": "Round Trip Subject"}
    assert loaded.timestamp == datetime(2026, 1, 1, tzinfo=UTC)


def test_get_latest_returns_most_recent_by_embedded_timestamp() -> None:
    older = make_output(subject="Older", timestamp=datetime(2026, 1, 1, tzinfo=UTC))
    newer = make_output(subject="Newer", timestamp=datetime(2026, 6, 1, tzinfo=UTC))

    # Save the newer newsletter first, then the older one, so mtime/write
    # order is the *opposite* of timestamp order. If `get_latest` picked the
    # most recently written file, it would (incorrectly) return "Older".
    history_service.save_newsletter(newer, "newer-id")
    history_service.save_newsletter(older, "older-id")

    latest = history_service.get_latest()
    assert latest is not None
    assert latest.subject == "Newer"


def test_get_latest_returns_none_when_history_dir_is_empty() -> None:
    assert history_service.get_latest() is None


def test_get_latest_returns_none_when_history_dir_does_not_exist_yet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nested = tmp_path / "does" / "not" / "exist"
    assert not nested.exists()
    monkeypatch.setenv("NEWSLETTER_HISTORY_DIR", str(nested))

    result = history_service.get_latest()

    assert result is None
    # The lookup should have lazily created the directory without raising.
    assert nested.exists()


def test_get_latest_skips_unreadable_file_without_raising(tmp_path: Path) -> None:
    (tmp_path / "20260101T000000Z_broken.json").write_text("{not valid json", encoding="utf-8")

    assert history_service.get_latest() is None


def test_list_history_returns_empty_list_when_no_newsletters_saved() -> None:
    assert history_service.list_history() == []


def test_list_history_orders_newest_first() -> None:
    first = make_output(subject="First", timestamp=datetime(2026, 1, 1, tzinfo=UTC))
    second = make_output(subject="Second", timestamp=datetime(2026, 3, 1, tzinfo=UTC))
    third = make_output(subject="Third", timestamp=datetime(2026, 2, 1, tzinfo=UTC))

    history_service.save_newsletter(first, "id-first")
    history_service.save_newsletter(second, "id-second")
    history_service.save_newsletter(third, "id-third")

    items = history_service.list_history()

    assert [item.subject for item in items] == ["Second", "Third", "First"]
    assert [item.id for item in items] == ["id-second", "id-third", "id-first"]


def test_list_history_respects_limit() -> None:
    for month in range(1, 6):
        history_service.save_newsletter(
            make_output(
                subject=f"Newsletter {month}", timestamp=datetime(2026, month, 1, tzinfo=UTC)
            ),
            f"id-{month}",
        )

    items = history_service.list_history(limit=2)

    assert len(items) == 2
    assert [item.subject for item in items] == ["Newsletter 5", "Newsletter 4"]


def test_list_history_skips_unreadable_files_without_raising(tmp_path: Path) -> None:
    history_service.save_newsletter(
        make_output(subject="Good", timestamp=datetime(2026, 1, 1, tzinfo=UTC)), "good-id"
    )
    # Invalid JSON syntax triggers the JSONDecodeError branch.
    (tmp_path / "20260601T000000Z_bad-json.json").write_text("not json at all", encoding="utf-8")
    # Valid JSON but missing required keys triggers the KeyError branch.
    (tmp_path / "20260701T000000Z_missing-keys.json").write_text("{}", encoding="utf-8")

    items = history_service.list_history()

    assert len(items) == 1
    assert items[0].subject == "Good"
