import { useCallback, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { initialStepStates, type StepId, type StepState } from "@/lib/power-automate-steps";
import type { AgentExecutionRecord, DemoGenerateResponse, NewsletterResponse } from "@/types/api";

export interface AutomationWorkflowResult {
  demo: DemoGenerateResponse;
  full: NewsletterResponse;
  html: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Sums real per-node telemetry for a group of LangGraph nodes into one displayed stage. */
function summarizeNodes(
  records: AgentExecutionRecord[],
  nodeNames: string[],
): { timeMs: number; items: number } | null {
  const matches = records.filter((r) => nodeNames.includes(r.node));
  if (matches.length === 0) return null;
  return {
    timeMs: matches.reduce((sum, r) => sum + r.execution_time_seconds, 0) * 1000,
    items: matches[matches.length - 1].items_processed,
  };
}

const NARRATION: Partial<Record<StepId, (result?: AutomationWorkflowResult) => string>> = {
  trigger: () => "Power Automate has triggered the workflow.",
  http: () => "Calling FastAPI to generate today's newsletter.",
  aggregation: (result) => {
    const agg = result
      ? summarizeNodes(result.demo.agent_execution, [
          "AggregatorAgent",
          "DeduplicationAgent",
          "RankingAgent",
        ])
      : null;
    return agg
      ? `Content aggregated, deduplicated, and ranked — ${agg.items} stories cleared the bar.`
      : "Content aggregated, deduplicated, and ranked.";
  },
  summarization: () => "GPT summarization complete — executive summary and subject line generated.",
  htmlGeneration: () => "Newsletter rendered to HTML, Markdown, and JSON.",
  receive: (result) =>
    result
      ? `LangGraph completed in ${result.demo.execution_time_seconds.toFixed(1)}s — newsletter HTML and statistics received.`
      : "Newsletter HTML and statistics received.",
  extract: () => "Subject, HTML newsletter, summary, and statistics extracted from the response.",
  compose: () => "Preparing the Outlook email.",
  send: () => "Outlook email composed — awaiting Outlook integration for live delivery.",
  delivered: () => "Newsletter ready for Outlook delivery.",
};

/**
 * Drives the Power Automate workflow console: real-time step status and
 * narration around one real pipeline run. `http`'s duration and the
 * aggregation/summarization/HTML-generation stages all come straight from
 * the response's real per-node `agent_execution` telemetry. The remaining
 * Power-Automate-side steps' pacing is presentational (parsing/composing a
 * payload this small is genuinely sub-millisecond), never fabricated
 * response data.
 */
export function useAutomationWorkflow() {
  const [steps, setSteps] = useState<StepState[]>(initialStepStates());
  const [narration, setNarration] = useState<string[]>([]);
  const [result, setResult] = useState<AutomationWorkflowResult | null>(null);
  const cancelledRef = useRef(false);

  const setStep = useCallback(
    (id: StepId, status: StepState["status"], timeMs?: number, items?: number) => {
      setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, status, timeMs, items } : s)));
    },
    [],
  );

  const pushNarration = useCallback((id: StepId, res?: AutomationWorkflowResult) => {
    const line = NARRATION[id]?.(res);
    if (line) setNarration((prev) => [...prev, line]);
  }, []);

  const mutation = useMutation<AutomationWorkflowResult, ApiError>({
    mutationFn: async () => {
      cancelledRef.current = false;
      setSteps(initialStepStates());
      setNarration([]);
      setResult(null);

      setStep("trigger", "running");
      pushNarration("trigger");
      await sleep(500);
      setStep("trigger", "success", 500);

      setStep("http", "running");
      pushNarration("http");
      const startedAt = performance.now();
      const demo = await api.demoGenerate();
      const httpMs = performance.now() - startedAt;
      setStep("http", "success", httpMs);

      const [full, html] = await Promise.all([
        api.getLatestNewsletter(),
        api.getLatestNewsletterHtml(),
      ]);
      const data: AutomationWorkflowResult = { demo, full, html };

      setStep("aggregation", "running");
      await sleep(200);
      const agg = summarizeNodes(demo.agent_execution, [
        "AggregatorAgent",
        "DeduplicationAgent",
        "RankingAgent",
      ]);
      setStep("aggregation", "success", agg?.timeMs, agg?.items);
      pushNarration("aggregation", data);

      setStep("summarization", "running");
      await sleep(200);
      const summarization = summarizeNodes(demo.agent_execution, [
        "NewsletterGeneratorAgent",
        "NoContentFallback",
      ]);
      setStep("summarization", "success", summarization?.timeMs, summarization?.items);
      pushNarration("summarization");

      setStep("htmlGeneration", "running");
      await sleep(200);
      const htmlGen = summarizeNodes(demo.agent_execution, ["HTMLFormatterAgent"]);
      setStep("htmlGeneration", "success", htmlGen?.timeMs, htmlGen?.items);
      pushNarration("htmlGeneration");

      setStep("receive", "running");
      await sleep(250);
      setStep("receive", "success", 250);
      pushNarration("receive", data);

      setStep("extract", "running");
      await sleep(350);
      setStep("extract", "success", 350);
      pushNarration("extract");

      setStep("compose", "running");
      pushNarration("compose");
      await sleep(500);
      setStep("compose", "success", 500);

      setStep("send", "running");
      await sleep(500);
      setStep("send", "success", 500);
      pushNarration("send");

      setStep("delivered", "running");
      await sleep(300);
      setStep("delivered", "success", 300);
      pushNarration("delivered");

      setResult(data);
      return data;
    },
    onError: (error) => {
      setSteps((prev) => {
        const runningIndex = prev.findIndex((s) => s.status === "running");
        if (runningIndex === -1) return prev;
        const next = [...prev];
        next[runningIndex] = { ...next[runningIndex], status: "error" };
        return next;
      });
      void error;
    },
  });

  const run = useCallback(() => {
    mutation.mutate();
  }, [mutation]);

  return {
    steps,
    narration,
    result,
    run,
    retry: run,
    isRunning: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.error?.detail ?? mutation.error?.message ?? null,
    hasRun: mutation.isSuccess || mutation.isError,
  };
}
