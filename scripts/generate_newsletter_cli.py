"""Run the AI Newsletter Automation LangGraph pipeline locally, without the API.

Usage:
    python scripts/generate_newsletter_cli.py
    python scripts/generate_newsletter_cli.py --output-dir newsletter_output
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.logging_config import configure_logging  # noqa: E402
from app.config.settings import get_settings  # noqa: E402
from app.graph.workflow import build_workflow  # noqa: E402
from app.models.state import build_initial_state  # noqa: E402


async def _run(output_dir: Path | None) -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.app_env)

    workflow = build_workflow()
    final_state = await workflow.ainvoke(build_initial_state())

    content = final_state.get("newsletter_content")
    print(f"Subject: {content.subject if content else 'N/A'}")
    print(f"Ranked stories: {len(final_state.get('ranked_news', []))}")

    errors = final_state.get("errors", [])
    if errors:
        print(f"Completed with {len(errors)} non-fatal error(s):")
        for error in errors:
            print(f"  - {error}")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "newsletter.html").write_text(
            final_state.get("newsletter_html", ""), encoding="utf-8"
        )
        (output_dir / "newsletter.md").write_text(
            final_state.get("newsletter_markdown", ""), encoding="utf-8"
        )
        print(f"Saved HTML/Markdown output to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the AI Newsletter Automation pipeline locally."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save the rendered HTML/Markdown output.",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.output_dir))


if __name__ == "__main__":
    main()
