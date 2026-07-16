import { AnimatePresence, motion } from "framer-motion";
import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface WorkflowInsightsProps {
  lines: string[];
}

/** Displays the current execution status of the newsletter automation pipeline. */
export function WorkflowInsights({ lines }: WorkflowInsightsProps) {
  return (
    <Card className="border-primary/30 bg-primary/5 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-primary" /> Workflow Insights
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          View execution progress and processing events across the automation pipeline.
        </p>
      </CardHeader>
      <CardContent>
        {lines.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Execute the automation workflow to view real-time processing events for each step.
          </p>
        ) : (
          <ol className="space-y-2">
            <AnimatePresence initial={false}>
              {lines.map((line, index) => (
                <motion.li
                  key={`${index}-${line}`}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-start gap-2 text-sm text-foreground/90"
                >
                  <span className="mt-0.5 text-xs font-mono text-primary">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span>{line}</span>
                </motion.li>
              ))}
            </AnimatePresence>
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
