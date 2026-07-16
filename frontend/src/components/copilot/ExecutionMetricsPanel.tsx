import { motion } from "framer-motion";
import { Clock, Coins, Copy, Files, Layers, ListFilter, Sparkle, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AgentExecutionRecord, DemoGenerateResponse } from "@/types/api";

interface ExecutionMetricsPanelProps {
  demo: DemoGenerateResponse;
}

export function ExecutionMetricsPanel({ demo }: ExecutionMetricsPanelProps) {
  const metrics: Array<{ icon: typeof Clock; label: string; value: string }> = [
    { icon: Clock, label: "Execution Time", value: `${demo.execution_time_seconds.toFixed(1)}s` },
    { icon: Files, label: "Articles Collected", value: String(demo.statistics.aggregated_count) },
    { icon: Trash2, label: "Duplicates Removed", value: String(demo.statistics.duplicates_removed) },
    { icon: ListFilter, label: "Stories Ranked", value: String(demo.statistics.ranked_count) },
    { icon: Layers, label: "Stories Selected", value: String(demo.statistics.stories_selected) },
    {
      icon: Sparkle,
      label: "OpenAI Tokens",
      value: demo.token_usage.prompt_and_completion_tokens.toLocaleString(),
    },
    { icon: Coins, label: "Estimated Cost", value: `$${demo.estimated_cost_usd.toFixed(4)}` },
  ];

  return (
    <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Execution Metrics</CardTitle>
        <div className="flex flex-wrap gap-2 pt-1">
          <Badge variant={demo.status === "success" ? "success" : "warning"}>{demo.status}</Badge>
          <Badge variant="outline">{demo.provider}</Badge>
          {demo.token_usage.is_estimated && <Badge variant="outline">estimated cost</Badge>}
        </div>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            className="rounded-xl border border-border/50 bg-background/40 p-3"
          >
            <metric.icon className="mb-1.5 h-4 w-4 text-primary" />
            <p className="text-lg font-semibold leading-none">{metric.value}</p>
            <p className="mt-1 text-[11px] text-muted-foreground">{metric.label}</p>
          </motion.div>
        ))}
      </CardContent>
      <CardContent className="pt-0">
        <AgentTimeline records={demo.agent_execution} />
      </CardContent>
    </Card>
  );
}

function AgentTimeline({ records }: { records: AgentExecutionRecord[] }) {
  if (records.length === 0) return null;
  return (
    <div>
      <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <Copy className="h-3 w-3" /> Agent Execution Timeline
      </p>
      <ul className="scrollbar-thin max-h-64 space-y-1.5 overflow-y-auto pr-1">
        {records.map((record) => (
          <li
            key={record.node}
            className="flex items-center justify-between rounded-lg bg-background/40 px-2.5 py-1.5 text-xs"
          >
            <span className="font-medium text-foreground/90">{record.node}</span>
            <span className="whitespace-nowrap text-muted-foreground">
              {record.execution_time_seconds.toFixed(2)}s · {record.items_processed} items
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
