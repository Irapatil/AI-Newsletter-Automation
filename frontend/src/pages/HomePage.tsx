import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { History, Sparkles } from "lucide-react";
import { ArchitectureDiagram } from "@/components/copilot/ArchitectureDiagram";
import { ChatInput } from "@/components/copilot/ChatInput";
import { ChatMessage } from "@/components/copilot/ChatMessage";
import { SuggestedPrompts } from "@/components/copilot/SuggestedPrompts";
import { Badge } from "@/components/ui/badge";
import { routePromptText, useCopilotChat } from "@/hooks/use-copilot-chat";
import { useNewsletterHistory } from "@/hooks/use-newsletter";
import { formatRelativeTime } from "@/lib/utils";

export function HomePage() {
  const { turns, submitPrompt, retryTurn, hasConversation } = useCopilotChat();
  const history = useNewsletterHistory(6);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isPending = turns.some((t) => t.status === "pending");
  const lastTurnStatus = turns[turns.length - 1]?.status;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, lastTurnStatus]);

  function handleFreeText(text: string) {
    void submitPrompt(routePromptText(text), text);
  }

  if (!hasConversation) {
    return (
      <div className="flex min-h-[75vh] flex-col items-center justify-center gap-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-3"
        >
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
            <Sparkles className="h-6 w-6" />
          </span>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Enterprise AI Newsletter Copilot
          </h1>
          <p className="mx-auto max-w-xl text-sm text-muted-foreground sm:text-base">
            Multi-Agent AI Newsletter Automation powered by LangGraph
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="w-full max-w-2xl space-y-6"
        >
          <ChatInput onSubmit={handleFreeText} disabled={isPending} />
          <SuggestedPrompts
            onSelect={(key, label) => void submitPrompt(key, label)}
            disabled={isPending}
          />
        </motion.div>

        {history.data && history.data.items.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex items-center gap-2 text-xs text-muted-foreground"
          >
            <History className="h-3.5 w-3.5" />
            Last generated {formatRelativeTime(history.data.items[0].timestamp)}
          </motion.div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-40">
      <div className="space-y-8 pb-4">
        {turns.map((turn) => (
          <ChatMessage key={turn.id} turn={turn} onRetry={retryTurn} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 bg-gradient-to-t from-background via-background/95 to-transparent pb-4 pt-8">
        <div className="mx-auto max-w-3xl space-y-3 px-4 sm:px-6">
          <ChatInput onSubmit={handleFreeText} disabled={isPending} />
          <SuggestedPrompts
            onSelect={(key, label) => void submitPrompt(key, label)}
            disabled={isPending}
            className="justify-start"
          />
        </div>
      </div>

      <section className="space-y-4 pt-8">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold tracking-tight">System Architecture</h2>
          <Badge variant="outline">always on</Badge>
        </div>
        <ArchitectureDiagram />
      </section>

      {history.data && history.data.items.length > 0 && (
        <section className="space-y-3 pb-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <History className="h-4 w-4" /> Recent Editions
          </h2>
          <div className="flex flex-wrap gap-2">
            {history.data.items.map((item) => (
              <Badge key={item.id} variant="outline" className="font-normal">
                {item.subject} · {formatRelativeTime(item.timestamp)}
              </Badge>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
