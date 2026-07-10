import { useEffect, useState } from "react";
import { Check, Loader2, X } from "lucide-react";
import { LANGGRAPH_NODES } from "@/types/api";
import { cn } from "@/lib/utils";

interface ProgressTimelineProps {
  /** True while the real POST /generate-newsletter request is in flight. */
  isRunning: boolean;
  /** True once the request has resolved successfully. */
  isComplete: boolean;
  /** True once the request has failed. */
  hasError: boolean;
}

/**
 * The backend runs the whole LangGraph pipeline synchronously and returns
 * only the final result (no SSE/WebSocket streaming of per-node progress
 * exists today). This simulates node-by-node progress while the real
 * request is in flight, then snaps to the true outcome the moment the
 * response actually arrives — it never reports "done" before the API
 * genuinely responds.
 */
export function ProgressTimeline({ isRunning, isComplete, hasError }: ProgressTimelineProps) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!isRunning) return;
    setStep(0);
    let cancelled = false;
    let current = 0;

    function scheduleNext() {
      if (cancelled || current >= LANGGRAPH_NODES.length - 1) return;
      const delay = 450 + Math.random() * 850;
      window.setTimeout(() => {
        if (cancelled) return;
        current += 1;
        setStep(current);
        scheduleNext();
      }, delay);
    }
    scheduleNext();

    return () => {
      cancelled = true;
    };
  }, [isRunning]);

  useEffect(() => {
    if (isComplete || hasError) setStep(LANGGRAPH_NODES.length);
  }, [isComplete, hasError]);

  return (
    <div className="space-y-1">
      {LANGGRAPH_NODES.map((node, index) => {
        const isDone = isComplete ? true : index < step;
        const isFailedHere = hasError && !isComplete && index === Math.min(step, LANGGRAPH_NODES.length - 1);
        const isActive = isRunning && !isComplete && !hasError && index === step;

        return (
          <div
            key={node.key}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              isActive && "bg-accent",
            )}
          >
            <div
              className={cn(
                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors",
                isDone && "border-success bg-success text-success-foreground",
                isActive && "border-primary text-primary",
                isFailedHere && "border-destructive bg-destructive/10 text-destructive",
                !isDone && !isActive && !isFailedHere && "border-border text-transparent",
              )}
            >
              {isDone && <Check className="h-3 w-3" />}
              {isActive && <Loader2 className="h-3 w-3 animate-spin" />}
              {isFailedHere && <X className="h-3 w-3" />}
            </div>
            <span
              className={cn(
                "transition-colors",
                isDone ? "text-foreground" : "text-muted-foreground",
                isActive && "font-medium text-foreground",
                isFailedHere && "font-medium text-destructive",
              )}
            >
              {node.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
