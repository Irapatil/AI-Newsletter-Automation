"""Renders the structured newsletter content into HTML, Markdown, and JSON."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config.settings import get_settings
from app.models.newsletter import NewsletterContent, NewsletterOutput

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_environment = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)


class HTMLFormatterAgent:
    display_name = "HTMLFormatterAgent"

    def run(self, content: NewsletterContent) -> NewsletterOutput:
        sender_name = get_settings().newsletter_sender_name
        return NewsletterOutput(
            subject=content.subject,
            summary=content.executive_summary,
            html=self._render_html(content, sender_name),
            markdown=self._render_markdown(content),
            json_payload=content.model_dump(mode="json"),
            timestamp=content.generated_at,
        )

    @staticmethod
    def _render_html(content: NewsletterContent, sender_name: str) -> str:
        template = _environment.get_template("newsletter.html.j2")
        return template.render(content=content, sender_name=sender_name)

    @staticmethod
    def _render_markdown(content: NewsletterContent) -> str:
        lines: list[str] = [
            f"# {content.subject}",
            "",
            "## Executive Summary",
            "",
            content.executive_summary,
            "",
            f"> 👀 **One Thing To Watch:** {content.one_thing_to_watch}",
            "",
        ]
        for section in content.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            for article in section.articles:
                lines.append(f"### [{article.title}]({article.url})")
                lines.append(
                    f"*{article.source} · {article.published_at.strftime('%b %d, %H:%M UTC')}*"
                )
                lines.append("")
                lines.append(article.ai_summary or article.snippet)
                lines.append("")
        lines.append("---")
        lines.append(
            f"_Generated automatically at {content.generated_at.strftime('%Y-%m-%d %H:%M UTC')}._"
        )
        return "\n".join(lines)
