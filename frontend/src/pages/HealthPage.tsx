import { Bot, Github, Globe, Key, Newspaper, RefreshCw, Rss } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/StatusBadge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useHealth } from "@/hooks/use-health";
import { formatDateTime } from "@/lib/utils";

const PROVIDER_META: Record<
  string,
  { label: string; icon: typeof Globe; description: string }
> = {
  api: {
    label: "FastAPI",
    icon: Globe,
    description: "The FastAPI backend responded to this request.",
  },
  openai: {
    label: "OpenAI",
    icon: Bot,
    description: "Whether a real OpenAI/Azure OpenAI key is configured, or the pipeline is falling back to a deterministic mock LLM.",
  },
  newsapi: {
    label: "NewsAPI",
    icon: Newspaper,
    description: "Optional supplemental source used by GlobalNewsAgent and PolicyAgent.",
  },
  github: {
    label: "GitHub",
    icon: Github,
    description: "GitHub Search API works unauthenticated (60 req/hr); a token raises that to 5000 req/hr.",
  },
  rss: { label: "RSS / Atom", icon: Rss, description: "RSS/Atom feed collection needs no credentials." },
  langgraph: {
    label: "LangGraph",
    icon: Key,
    description: "Whether the compiled StateGraph built without raising an exception.",
  },
};

export function HealthPage() {
  const { health, error, loading, refetch } = useHealth();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">Overall Status</CardTitle>
            {health && (
              <p className="mt-1 text-xs text-muted-foreground">
                Last checked {formatDateTime(health.timestamp)} · API v{health.version}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {loading ? <Skeleton className="h-6 w-16" /> : <StatusBadge status={health?.status ?? "error"} />}
            <Button variant="outline" size="icon" onClick={refetch} aria-label="Refresh health">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
      </Card>

      {error && (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">{error.message}</CardContent>
        </Card>
      )}

      <div>
        <h3 className="mb-3 text-sm font-semibold text-muted-foreground">Integrations</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loading && !health
            ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)
            : Object.entries(PROVIDER_META).map(([key, meta]) => {
                const Icon = meta.icon;
                const status = health?.providers?.[key] ?? "error";
                return (
                  <Card key={key}>
                    <CardContent className="flex items-start justify-between gap-3 p-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">{meta.label}</span>
                        </div>
                        <div className="mt-2">
                          <StatusBadge status={status} />
                        </div>
                      </div>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            type="button"
                            className="text-xs text-muted-foreground underline decoration-dotted underline-offset-2"
                          >
                            what&apos;s this?
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">{meta.description}</TooltipContent>
                      </Tooltip>
                    </CardContent>
                  </Card>
                );
              })}
        </div>
      </div>
    </div>
  );
}
