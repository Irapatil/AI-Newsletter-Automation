import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Check, X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { StepDefinition, StepState } from "@/lib/power-automate-steps";
import type { OutlookDeliveryState } from "@/types/api";

interface WorkflowStepCardProps {
  index: number;
  definition: StepDefinition;
  state: StepState;
  /** Real status from GET /integration/outlook/status, for steps flagged `simulated`. */
  outlookDeliveryStatus?: OutlookDeliveryState;
  children?: ReactNode;
}

const STATUS_LABEL: Record<StepState["status"], string> = {
  pending: "Queued",
  running: "Running",
  success: "Completed",
  error: "Error",
};

function formatTime(ms?: number): string | null {
  if (ms === undefined) return null;
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function WorkflowStepCard({
  index,
  definition,
  state,
  outlookDeliveryStatus,
  children,
}: WorkflowStepCardProps) {
  const time = formatTime(state.timeMs);
  const detail = [time, state.items !== undefined ? `${state.items} items` : null]
    .filter(Boolean)
    .join(" · ");

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className={cn(
          "border-border/60 bg-card/70 backdrop-blur-sm transition-colors",
          state.status === "running" && "border-primary/50 shadow-[0_0_0_1px_hsl(var(--primary)/0.3)]",
          state.status === "success" && "border-success/40",
          state.status === "error" && "border-destructive/50",
        )}
      >
        <CardContent className="flex items-start gap-4 py-5">
          <span className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary">
            {state.status === "running" && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-xl bg-primary/30" />
            )}
            {state.status === "success" ? (
              <Check className="h-5 w-5 text-success" strokeWidth={3} />
            ) : state.status === "error" ? (
              <X className="h-5 w-5 text-destructive" strokeWidth={3} />
            ) : (
              <definition.icon className="h-5 w-5" />
            )}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="font-semibold">{definition.title}</h3>
              <Badge
                variant={
                  state.status === "success"
                    ? "success"
                    : state.status === "error"
                      ? "destructive"
                      : state.status === "running"
                        ? "default"
                        : "outline"
                }
              >
                {STATUS_LABEL[state.status]}
              </Badge>
              {definition.simulated && (
                <Badge
                  variant={
                    outlookDeliveryStatus === "delivered"
                      ? "success"
                      : outlookDeliveryStatus === "failed"
                        ? "destructive"
                        : "outline"
                  }
                  className={outlookDeliveryStatus === "delivered" ? undefined : "text-muted-foreground"}
                >
                  {outlookDeliveryStatus === "delivered"
                    ? "Connected"
                    : outlookDeliveryStatus === "failed"
                      ? "Delivery Failed"
                      : "Integration Ready"}
                </Badge>
              )}
              {detail && <span className="ml-auto text-xs text-muted-foreground">{detail}</span>}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{definition.description}</p>
            {children}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
