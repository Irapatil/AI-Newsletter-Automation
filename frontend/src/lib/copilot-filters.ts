import type { PromptKey } from "@/hooks/use-copilot-chat";
import { SECTION_TITLES } from "@/types/api";
import type { NewsletterResponse, NewsletterSection } from "@/types/api";

const PROMPT_SECTION_KEY: Partial<Record<PromptKey, string>> = {
  funding: "funding",
  research: "research",
  hiring: "talent",
  policy: "policy",
};

/** Selects the slice of the one real newsletter result each suggested prompt is about. */
export function getSectionsForPrompt(
  full: NewsletterResponse | undefined,
  promptKey: PromptKey,
): NewsletterSection[] {
  const sections = full?.newsletter_json.sections ?? [];
  if (promptKey === "generate") return sections;
  if (promptKey === "summary") return [];

  if (promptKey === "openai") {
    const matches = sections
      .flatMap((section) => section.articles)
      .filter((article) =>
        `${article.title} ${article.snippet} ${article.source}`.toLowerCase().includes("openai"),
      );
    return matches.length > 0
      ? [{ key: "openai", title: "🤖 OpenAI News", articles: matches }]
      : [];
  }

  const sectionKey = PROMPT_SECTION_KEY[promptKey];
  const match = sections.find((section) => section.key === sectionKey);
  return match ? [match] : [];
}

export function getAssistantIntro(promptKey: PromptKey, sections: NewsletterSection[]): string {
  switch (promptKey) {
    case "generate":
      return "Here's today's full AI newsletter, assembled by the LangGraph pipeline below.";
    case "summary":
      return "Here's the executive summary from today's run.";
    case "openai":
      return sections.length > 0
        ? "Here's everything about OpenAI from today's run."
        : "No OpenAI-specific stories cleared the ranking bar in today's run — here's the executive summary instead.";
    default: {
      const title = SECTION_TITLES[PROMPT_SECTION_KEY[promptKey] ?? ""] ?? "that topic";
      return sections.length > 0
        ? `Here's the ${title} section from today's run.`
        : `No stories landed in ${title} today — here's the executive summary instead.`;
    }
  }
}
