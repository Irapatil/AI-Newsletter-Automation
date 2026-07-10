import { useMemo, useState } from "react";
import { History as HistoryIcon, Info, Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useNewsletterHistory } from "@/hooks/use-newsletter-queries";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";

export function HistoryPage() {
  const { data, isLoading, error } = useNewsletterHistory(20);
  const [search, setSearch] = useState("");

  const filteredItems = useMemo(() => {
    const items = data?.items ?? [];
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((item) => item.subject.toLowerCase().includes(query));
  }, [data, search]);

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-lg border border-border bg-muted/40 px-4 py-3 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <p>
          This list comes from{" "}
          <code className="rounded bg-muted px-1 py-0.5">GET /newsletter/history</code>. The API
          only returns full HTML/Markdown/JSON for the single most recent edition (via{" "}
          <code className="rounded bg-muted px-1 py-0.5">GET /newsletter/latest</code>) — there is
          no per-edition retrieval endpoint yet, so historical entries below show metadata only.
        </p>
      </div>

      {!isLoading && !error && data && data.items.length > 0 && (
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search newsletters by subject…"
            className="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm shadow-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {!isLoading && error && (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">{error.message}</CardContent>
        </Card>
      )}

      {!isLoading && !error && data && data.items.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground">
            <HistoryIcon className="h-6 w-6" />
            No newsletters generated yet.
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && data && data.items.length > 0 && filteredItems.length === 0 && (
        <Card>
          <CardContent className="p-6 text-center text-sm text-muted-foreground">
            No newsletters match &quot;{search}&quot;.
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && filteredItems.length > 0 && (
        <div className="relative space-y-4 pl-6">
          <div className="absolute bottom-2 left-[7px] top-2 w-px bg-border" aria-hidden="true" />
          {filteredItems.map((item) => (
            <div key={item.id} className="relative animate-fade-in">
              <div className="absolute -left-6 top-5 h-3 w-3 rounded-full border-2 border-primary bg-background" />
              <Card>
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{item.subject}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(item.timestamp)}
                    </p>
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
