import { AlertTriangle, Activity, CheckCircle2, CircleDashed, Workflow } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHealth } from "@/hooks/use-health";
import { useOutlookDeliveryStatus } from "@/hooks/use-outlook-delivery-status";
import { cn } from "@/lib/utils";

type IndicatorState = "ok" | "warning" | "neutral";

interface StatusItem {
  key: string;
  label: string;
  state: IndicatorState;
  statusLabel: string;
  note: string;
}

const INDICATOR_ICON: Record<IndicatorState, typeof CheckCircle2> = {
  ok: CheckCircle2,
  warning: AlertTriangle,
  neutral: CircleDashed,
};

const INDICATOR_COLOR: Record<IndicatorState, string> = {
  ok: "text-success",
  warning: "text-destructive",
  neutral: "text-muted-foreground",
};

export function ConnectionStatusPanel() {
  const { health, loading } = useHealth();
  const { data: outlookStatus } = useOutlookDeliveryStatus();
  const fastApiHealthy = !loading && health?.status === "ok";
  const langGraphOperational = !loading && health?.providers.langgraph === "operational";

  let outlookState: IndicatorState = "neutral";
  let outlookLabel = "Integration Ready";
  let outlookNote = "Detected from GET /integration/outlook/status — no delivery reported yet";
  if (outlookStatus?.delivery_status === "delivered") {
    outlookState = "ok";
    outlookLabel = "Connected";
    outlookNote = "Real delivery confirmed by Power Automate";
  } else if (outlookStatus?.delivery_status === "failed") {
    outlookState = "warning";
    outlookLabel = "Delivery Failed";
    outlookNote = "Power Automate reported a failed send — check the flow's run history";
  }

  const items: StatusItem[] = [
    {
      key: "fastapi",
      label: "FastAPI",
      state: fastApiHealthy ? "ok" : "warning",
      statusLabel: fastApiHealthy ? "Healthy" : "Unavailable",
      note: "Live health check",
    },
    {
      key: "langgraph",
      label: "LangGraph",
      state: langGraphOperational ? "ok" : "warning",
      statusLabel: langGraphOperational ? "Operational" : "Unavailable",
      note: "Compiled workflow status",
    },
    {
      key: "power-automate",
      label: "Power Automate",
      state: "neutral",
      statusLabel: "Not Configured",
      note: "Reference only — no live workflow connection configured in this environment",
    },
    {
      key: "outlook",
      label: "Outlook",
      state: outlookState,
      statusLabel: outlookLabel,
      note: outlookNote,
    },
  ];

  return (
    <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Workflow className="h-4 w-4 text-primary" /> Workflow Status
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {items.map((item) => {
          const Icon = INDICATOR_ICON[item.state];
          return (
            <div
              key={item.key}
              className="flex flex-col items-start gap-1.5 rounded-xl border border-border/50 bg-background/40 p-3"
            >
              <span className="flex items-center gap-1.5 text-sm font-medium">
                <Icon className={cn("h-3.5 w-3.5", INDICATOR_COLOR[item.state])} />
                {item.label}
              </span>
              <span className={cn("text-[11px] leading-snug", INDICATOR_COLOR[item.state])}>
                {item.statusLabel}
              </span>
              <span className="text-[11px] leading-snug text-muted-foreground/80">{item.note}</span>
            </div>
          );
        })}
      </CardContent>
      <CardContent className="flex items-center gap-1.5 pt-0 text-[11px] text-muted-foreground">
        <Activity className="h-3 w-3" /> Refreshes automatically every 30s.
      </CardContent>
    </Card>
  );
}
