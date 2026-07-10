import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  Bot,
  Brain,
  Calendar,
  Clock,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/StatusBadge";
import { useHealth } from "@/hooks/use-health";
import { api, type ApiError } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import type { NewsletterHistoryItem } from "@/types/api";

export function DashboardPage() {
  const { health, loading: healthLoading } = useHealth();
  const [lastRun, setLastRun] = useState<NewsletterHistoryItem | null>(null);
  const [historyError, setHistoryError] = useState<ApiError | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .getHistory(1)
      .then((res) => {
        if (!cancelled) setLastRun(res.items[0] ?? null);
      })
      .catch((err) => {
        if (!cancelled) setHistoryError(err as ApiError);
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-border bg-gradient-to-br from-primary/10 via-background to-background p-6 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-semibold">Enterprise AI Newsletter Automation</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            A LangGraph multi-agent pipeline collects, deduplicates, ranks, and summarizes AI
            industry news into an executive-ready newsletter — delivered daily via Microsoft
            Power Automate and Outlook.
          </p>
        </div>
        <Button asChild size="lg" className="shrink-0">
          <Link to="/generate">
            <Sparkles className="h-4 w-4" />
            Generate Newsletter
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground">System Status</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                API Status
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <Skeleton className="h-6 w-24" />
              ) : (
                <StatusBadge status={health?.providers?.api ?? "error"} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                LangGraph Status
              </CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <Skeleton className="h-6 w-24" />
              ) : (
                <StatusBadge status={health?.providers?.langgraph ?? "error"} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                OpenAI Status
              </CardTitle>
              <Brain className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <Skeleton className="h-6 w-24" />
              ) : (
                <StatusBadge status={health?.providers?.openai ?? "error"} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium text-muted-foreground">Last Run</CardTitle>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <Skeleton className="h-6 w-40" />
            ) : historyError ? (
              <p className="text-sm text-muted-foreground">Unable to load history.</p>
            ) : lastRun ? (
              <div>
                <p className="truncate text-sm font-medium">{lastRun.subject}</p>
                <p className="text-xs text-muted-foreground">
                  {formatRelativeTime(lastRun.timestamp)}
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No newsletter generated yet — try Generate Newsletter.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Next Scheduled Run
            </CardTitle>
            <CardDescription className="sr-only">
              Scheduling is handled outside this API by Power Automate
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium">Daily via Microsoft Power Automate</p>
            <p className="text-xs text-muted-foreground">
              Scheduling lives in Power Automate&apos;s recurrence trigger, not in this API — see
              docs/POWER_AUTOMATE.md for the flow configuration.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
