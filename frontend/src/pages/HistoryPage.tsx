import { useEffect, useState } from "react";
import { History as HistoryIcon, Info } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { api, type ApiError } from "@/lib/api";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";
import type { NewsletterHistoryItem } from "@/types/api";

export function HistoryPage() {
  const [items, setItems] = useState<NewsletterHistoryItem[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .getHistory(20)
      .then((res) => {
        if (!cancelled) setItems(res.items);
      })
      .catch((err) => {
        if (!cancelled) setError(err as ApiError);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-lg border border-border bg-muted/40 px-4 py-3 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <p>
          This list comes from <code className="rounded bg-muted px-1 py-0.5">GET /newsletter/history</code>.
          The API only returns full HTML/Markdown/JSON for the single most recent edition (via{" "}
          <code className="rounded bg-muted px-1 py-0.5">GET /newsletter/latest</code>) — there is
          no per-edition retrieval endpoint yet, so historical entries below show metadata only.
        </p>
      </div>

      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {!loading && error && (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">{error.message}</CardContent>
        </Card>
      )}

      {!loading && !error && items && items.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground">
            <HistoryIcon className="h-6 w-6" />
            No newsletters generated yet.
          </CardContent>
        </Card>
      )}

      {!loading && !error && items && items.length > 0 && (
        <div className="space-y-2">
          {items.map((item) => (
            <Card key={item.id} className="animate-fade-in">
              <CardContent className="flex items-center justify-between gap-4 p-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{item.subject}</p>
                  <p className="text-xs text-muted-foreground">{formatDateTime(item.timestamp)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {item.id}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {formatRelativeTime(item.timestamp)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
