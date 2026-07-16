import { motion } from "framer-motion";
import { Bot, RotateCcw, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ExecutionMetricsPanel } from "@/components/copilot/ExecutionMetricsPanel";
import { LangGraphExecutionAnimation } from "@/components/copilot/LangGraphExecutionAnimation";
import { ExecutiveSummaryCard } from "@/components/copilot/ExecutiveSummaryCard";
import { NewsletterPreviewPanel } from "@/components/copilot/NewsletterPreviewPanel";
import { SectionCard } from "@/components/copilot/SectionCard";
import { getAssistantIntro, getSectionsForPrompt } from "@/lib/copilot-filters";
import type { ChatTurn } from "@/hooks/use-copilot-chat";

interface ChatMessageProps {
  turn: ChatTurn;
  onRetry: (turnId: string) => void;
}

export function ChatMessage({ turn, onRetry }: ChatMessageProps) {
  const sections = turn.data ? getSectionsForPrompt(turn.data.full, turn.promptKey) : [];
  const showSummary = turn.promptKey === "generate" || turn.promptKey === "summary";
  const showPreview = turn.promptKey === "generate";

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-end"
      >
        <div className="flex max-w-[85%] items-start gap-2.5">
          <p className="rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
            {turn.promptText}
          </p>
          <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary">
            <User className="h-3.5 w-3.5" />
          </span>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="flex justify-start"
      >
        <div className="flex w-full max-w-3xl items-start gap-2.5">
          <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
            <Bot className="h-3.5 w-3.5" />
          </span>
          <div className="min-w-0 flex-1 space-y-4">
            {turn.status === "pending" && <LangGraphExecutionAnimation phase="running" />}

            {turn.status === "error" && (
              <div className="space-y-3">
                <LangGraphExecutionAnimation phase="error" errorMessage={turn.errorMessage} />
                <Button size="sm" variant="outline" onClick={() => onRetry(turn.id)}>
                  <RotateCcw className="h-3.5 w-3.5" /> Retry
                </Button>
              </div>
            )}

            {turn.status === "success" && turn.data && (
              <>
                <LangGraphExecutionAnimation
                  phase="done"
                  agentExecution={turn.data.demo.agent_execution}
                />
                <p className="text-sm text-foreground/90">
                  {getAssistantIntro(turn.promptKey, sections)}
                </p>
                {showSummary && (
                  <ExecutiveSummaryCard
                    subject={turn.data.full.subject}
                    summary={turn.data.full.summary}
                    oneThingToWatch={turn.data.full.newsletter_json.one_thing_to_watch}
                  />
                )}
                {sections.length > 0 && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {sections.map((section, index) => (
                      <SectionCard key={section.key} section={section} index={index} />
                    ))}
                  </div>
                )}
                {showPreview && (
                  <NewsletterPreviewPanel
                    html={turn.data.html}
                    markdown={turn.data.full.newsletter_markdown}
                    subject={turn.data.full.subject}
                  />
                )}
                <ExecutionMetricsPanel demo={turn.data.demo} />
              </>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
