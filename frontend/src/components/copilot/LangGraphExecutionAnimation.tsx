import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { LANGGRAPH_NODES } from "@/types/api";
import type { AgentExecutionRecord } from "@/types/api";

export type ExecutionPhase = "running" | "done" | "error";

interface LangGraphExecutionAnimationProps {
  phase: ExecutionPhase;
  agentExecution?: AgentExecutionRecord[];
  errorMessage?: string;
  className?: string;
}

const PULSE_INTERVAL_MS = 850;
const REVEAL_STEP_MS = 130;

/** node.node values from app/graph/nodes.py that don't appear on the happy-path diagram. */
const FALLBACK_NODE_LABELS: Record<string, string> = {
  NoContentFallback: "No-Content Fallback",
};

export function LangGraphExecutionAnimation({
  phase,
  agentExecution = [],
  errorMessage,
  className,
}: LangGraphExecutionAnimationProps) {
  const [pulseIndex, setPulseIndex] = useState(0);
  const [revealedCount, setRevealedCount] = useState(phase === "done" ? agentExecution.length : 0);

  useEffect(() => {
    if (phase !== "running") return;
    const interval = setInterval(() => {
      setPulseIndex((prev) => (prev + 1) % LANGGRAPH_NODES.length);
    }, PULSE_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [phase]);

  useEffect(() => {
    if (phase !== "done") {
      setRevealedCount(0);
      return;
    }
    setRevealedCount(0);
    let count = 0;
    const interval = setInterval(() => {
      count += 1;
      setRevealedCount(count);
      if (count >= agentExecution.length) clearInterval(interval);
    }, REVEAL_STEP_MS);
    return () => clearInterval(interval);
  }, [phase, agentExecution]);

  const executedNodeNames = agentExecution.map((record) => record.node);
  const displayNodes: Array<{ key: string; label: string }> = LANGGRAPH_NODES.map((node) => ({
    key: node.key,
    label: node.label,
  }));

  // If the fallback path ran instead of NewsletterGeneratorAgent, swap that slot's label.
  if (executedNodeNames.includes("NoContentFallback")) {
    const genIndex = displayNodes.findIndex((n) => n.key === "NewsletterGeneratorAgent");
    if (genIndex >= 0) {
      displayNodes[genIndex] = {
        key: "NoContentFallback",
        label: FALLBACK_NODE_LABELS.NoContentFallback,
      };
    }
  }

  return (
    <div
      className={cn(
        "rounded-2xl border border-border/60 bg-card/60 p-5 backdrop-blur-sm",
        className,
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold tracking-wide text-muted-foreground">
          LANGGRAPH EXECUTION
        </h3>
        {phase === "running" && (
          <span className="flex items-center gap-1.5 text-xs text-primary">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> running
          </span>
        )}
        {phase === "done" && (
          <span className="flex items-center gap-1.5 text-xs text-success">
            <Check className="h-3.5 w-3.5" /> complete
          </span>
        )}
        {phase === "error" && (
          <span className="flex items-center gap-1.5 text-xs text-destructive">
            <XCircle className="h-3.5 w-3.5" /> failed
          </span>
        )}
      </div>

      <div className="flex flex-col items-stretch gap-0.5">
        <FlowNode label="START" state="ghost" />
        <Connector />
        {displayNodes.map((node, index) => {
          const record = agentExecution.find((r) => r.node === node.key);
          const isRevealed = phase === "done" && index < revealedCount;
          const isCurrentPulse = phase === "running" && index === pulseIndex;
          const isFanOut = index >= 1 && index <= 8;

          return (
            <div key={node.key}>
              <FlowNode
                label={node.label}
                state={
                  phase === "error" && !isRevealed
                    ? "idle"
                    : isRevealed
                      ? "done"
                      : isCurrentPulse
                        ? "active"
                        : "idle"
                }
                badge={
                  isRevealed && record
                    ? `${record.execution_time_seconds.toFixed(2)}s · ${record.items_processed} items`
                    : undefined
                }
                indent={isFanOut}
              />
              {index < displayNodes.length - 1 && <Connector />}
            </div>
          );
        })}
        <Connector />
        <FlowNode label="END" state={phase === "done" ? "done" : "ghost"} />
      </div>

      {phase === "error" && errorMessage && (
        <p className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {errorMessage}
        </p>
      )}
    </div>
  );
}

function Connector() {
  return <div className="ml-4 h-3 w-px bg-border/70" />;
}

interface FlowNodeProps {
  label: string;
  state: "idle" | "active" | "done" | "ghost";
  badge?: string;
  indent?: boolean;
}

function FlowNode({ label, state, badge, indent }: FlowNodeProps) {
  return (
    <motion.div
      layout
      className={cn("flex items-center gap-3 py-1", indent && "pl-6")}
      initial={false}
    >
      <span
        className={cn(
          "relative flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-300",
          state === "ghost" && "border-border/50 bg-transparent",
          state === "idle" && "border-border bg-muted",
          state === "active" && "border-primary bg-primary/20",
          state === "done" && "border-success bg-success",
        )}
      >
        {state === "active" && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/50" />
        )}
        {state === "done" && <Check className="h-3 w-3 text-success-foreground" strokeWidth={3} />}
      </span>
      <span
        className={cn(
          "text-sm transition-colors duration-300",
          state === "ghost" && "font-mono text-xs uppercase tracking-widest text-muted-foreground/70",
          state === "idle" && "text-muted-foreground",
          state === "active" && "font-medium text-foreground",
          state === "done" && "font-medium text-foreground",
        )}
      >
        {label}
      </span>
      <AnimatePresence>
        {badge && (
          <motion.span
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            className="ml-auto whitespace-nowrap rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
          >
            {badge}
          </motion.span>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
