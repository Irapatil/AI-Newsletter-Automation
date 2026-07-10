import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Tone = "success" | "warning" | "destructive" | "neutral";

const STATUS_MAP: Record<string, { tone: Tone; label: string }> = {
  ok: { tone: "success", label: "OK" },
  configured: { tone: "success", label: "Configured" },
  authenticated: { tone: "success", label: "Authenticated" },
  available: { tone: "success", label: "Available" },
  operational: { tone: "success", label: "Operational" },
  mock: { tone: "warning", label: "Mock Mode" },
  public: { tone: "warning", label: "Public (unauthenticated)" },
  not_configured: { tone: "neutral", label: "Not Configured" },
  error: { tone: "destructive", label: "Error" },
};

const TONE_ICON: Record<Tone, typeof CheckCircle2> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  destructive: XCircle,
  neutral: HelpCircle,
};

const TONE_CLASS: Record<Tone, string> = {
  success: "border-transparent bg-success/15 text-success dark:bg-success/20",
  warning: "border-transparent bg-warning/15 text-warning-foreground dark:bg-warning/20",
  destructive: "border-transparent bg-destructive/15 text-destructive dark:bg-destructive/20",
  neutral: "border-transparent bg-muted text-muted-foreground",
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const entry = STATUS_MAP[status] ?? { tone: "neutral" as Tone, label: status };
  const Icon = TONE_ICON[entry.tone];

  return (
    <Badge className={cn(TONE_CLASS[entry.tone], className)}>
      <Icon className="h-3 w-3" />
      {entry.label}
    </Badge>
  );
}
