import { useCallback, useRef, useState } from "react";
import { api, type ApiError } from "@/lib/api";
import type { DemoGenerateResponse, NewsletterResponse } from "@/types/api";

export type PromptKey =
  | "generate"
  | "funding"
  | "openai"
  | "research"
  | "hiring"
  | "policy"
  | "summary";

export interface SuggestedPrompt {
  key: PromptKey;
  label: string;
}

export const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  { key: "generate", label: "Generate today's newsletter" },
  { key: "funding", label: "Show funding updates" },
  { key: "openai", label: "Show OpenAI news" },
  { key: "research", label: "Show research highlights" },
  { key: "hiring", label: "Show hiring trends" },
  { key: "policy", label: "Show policy updates" },
  { key: "summary", label: "Show today's AI summary" },
];

const KEYWORD_ROUTES: Array<{ key: PromptKey; test: RegExp }> = [
  { key: "funding", test: /fund|invest|raise|series|valuation/i },
  { key: "openai", test: /openai|gpt|chatgpt|sam altman/i },
  { key: "research", test: /research|paper|arxiv|benchmark|study/i },
  { key: "hiring", test: /hir|talent|job|recruit|headcount/i },
  { key: "policy", test: /polic|regulat|eu ai act|legislat|government/i },
  { key: "summary", test: /summary|today|overview|brief|recap/i },
];

/** Lightweight keyword router for free-text input — not an LLM, just maps to the nearest supported view. */
export function routePromptText(text: string): PromptKey {
  for (const route of KEYWORD_ROUTES) {
    if (route.test.test(text)) return route.key;
  }
  return "generate";
}

export interface CopilotTurnData {
  demo: DemoGenerateResponse;
  full: NewsletterResponse;
  html: string;
}

export interface ChatTurn {
  id: string;
  promptKey: PromptKey;
  promptText: string;
  status: "pending" | "success" | "error";
  data?: CopilotTurnData;
  errorMessage?: string;
  startedAt: number;
}

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `turn-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/**
 * Drives the whole conversation. Every prompt — whichever suggested chip or
 * free-text query triggered it — runs the exact same real pipeline call
 * (`POST /demo/generate`) followed by the two read endpoints that hydrate
 * the rich views (`GET /newsletter/latest`, `GET /newsletter/latest/html`).
 * `promptKey` only controls which slice of that one real result is
 * rendered — there is no per-topic backend query to call instead.
 */
export function useCopilotChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const cacheRef = useRef<CopilotTurnData | null>(null);

  const submitPrompt = useCallback(async (promptKey: PromptKey, promptText: string) => {
    const id = newId();
    setTurns((prev) => [
      ...prev,
      { id, promptKey, promptText, status: "pending", startedAt: Date.now() },
    ]);

    try {
      const demo = await api.demoGenerate();
      const [full, html] = await Promise.all([
        api.getLatestNewsletter(),
        api.getLatestNewsletterHtml(),
      ]);
      const data: CopilotTurnData = { demo, full, html };
      cacheRef.current = data;
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: "success", data } : t)));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Something went wrong.";
      setTurns((prev) =>
        prev.map((t) =>
          t.id === id ? { ...t, status: "error", errorMessage: (error as ApiError).detail ?? message } : t,
        ),
      );
    }
  }, []);

  const retryTurn = useCallback(
    (turnId: string) => {
      const turn = turns.find((t) => t.id === turnId);
      if (!turn) return;
      setTurns((prev) => prev.filter((t) => t.id !== turnId));
      void submitPrompt(turn.promptKey, turn.promptText);
    },
    [turns, submitPrompt],
  );

  return { turns, submitPrompt, retryTurn, hasConversation: turns.length > 0 };
}
