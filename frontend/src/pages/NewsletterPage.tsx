import { useRef } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Clock,
  Files,
  Copy as CopyIcon,
  Layers,
  ListChecks,
  Coins,
  DollarSign,
  Download,
  Printer,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { MetricCard } from "@/components/MetricCard";
import { NewsletterViewer } from "@/components/NewsletterViewer";
import { useLastExecutionTime, useLatestNewsletter } from "@/hooks/use-newsletter-queries";
import {
  downloadTextFile,
  copyToClipboard,
  estimateTokensAndCost,
  formatDateTime,
  formatDuration,
} from "@/lib/utils";

export function NewsletterPage() {
  const { data, isLoading, error } = useLatestNewsletter();
  const { data: executionTimeMs } = useLastExecutionTime();
  const previewFrameRef = useRef<HTMLIFrameElement>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-4 p-10 text-center">
          <p className="text-sm text-muted-foreground">
            {error?.status === 404
              ? "No newsletter has been generated yet."
              : (error?.message ?? "No newsletter loaded yet.")}
          </p>
          <Button asChild>
            <Link to="/generate">
              <Sparkles className="h-4 w-4" />
              Generate Newsletter
            </Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const { tokens, costUsd } = estimateTokensAndCost([
    data.summary,
    ...data.json.sections.flatMap((s) => s.articles.map((a) => a.ai_summary ?? "")),
  ]);

  async function handleCopy(label: string, text: string) {
    const ok = await copyToClipboard(text);
    if (ok) toast.success(`${label} copied to clipboard`);
    else toast.error(`Could not copy ${label.toLowerCase()}`);
  }

  function handleDownload(kind: "html" | "markdown") {
    if (!data) return;
    const datePart = new Date(data.timestamp).toISOString().slice(0, 10);
    const filename =
      kind === "html" ? `newsletter-${datePart}.html` : `newsletter-${datePart}.md`;
    downloadTextFile(
      filename,
      kind === "html" ? data.html : data.markdown,
      kind === "html" ? "text/html" : "text/markdown",
    );
    toast.success(`Downloaded ${filename}`);
  }

  function handlePrint() {
    const frameWindow = previewFrameRef.current?.contentWindow;
    if (!frameWindow) {
      toast.error("Preview isn't ready to print yet");
      return;
    }
    frameWindow.focus();
    frameWindow.print();
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_300px]">
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold leading-snug">{data.subject}</h2>
          <p className="text-xs text-muted-foreground">
            Generated {formatDateTime(data.timestamp)}
          </p>
          {data.errors.length > 0 && (
            <p className="mt-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning-foreground">
              {data.errors.length} non-fatal issue{data.errors.length === 1 ? "" : "s"} during this
              run: {data.errors.join("; ")}
            </p>
          )}
        </div>

        <NewsletterViewer
          ref={previewFrameRef}
          html={data.html}
          markdown={data.markdown}
          content={data.json}
        />

        <Card>
          <CardContent className="flex flex-wrap gap-2 p-4">
            <Button variant="outline" size="sm" onClick={() => handleDownload("html")}>
              <Download className="h-4 w-4" />
              Download HTML
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleDownload("markdown")}>
              <Download className="h-4 w-4" />
              Download Markdown
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleCopy("HTML", data.html)}>
              <CopyIcon className="h-4 w-4" />
              Copy HTML
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy("Markdown", data.markdown)}
            >
              <CopyIcon className="h-4 w-4" />
              Copy Markdown
            </Button>
            <Button variant="outline" size="sm" onClick={handlePrint}>
              <Printer className="h-4 w-4" />
              Print
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-muted-foreground">Execution Metrics</h3>
        {executionTimeMs != null && (
          <MetricCard label="Execution Time" value={formatDuration(executionTimeMs)} icon={Clock} />
        )}
        <MetricCard label="Articles Collected" value={data.stats.aggregated_count} icon={Files} />
        <MetricCard
          label="Duplicates Removed"
          value={data.stats.duplicates_removed}
          icon={Layers}
        />
        <MetricCard label="Stories Ranked" value={data.stats.ranked_count} icon={ListChecks} />
        <MetricCard label="Stories Selected" value={data.stats.stories_selected} icon={ListChecks} />
        <Separator />
        <MetricCard
          label="OpenAI Tokens (Estimated)"
          value={tokens.toLocaleString()}
          icon={Coins}
          accent="warning"
          hint="Heuristic (~4 chars/token) — not returned by the API"
        />
        <MetricCard
          label="Estimated Cost"
          value={`$${costUsd.toFixed(4)}`}
          icon={DollarSign}
          accent="warning"
          hint="Rough estimate, not actual billing data"
        />
      </div>
    </div>
  );
}
