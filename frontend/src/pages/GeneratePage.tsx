import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Sparkles, ArrowRight, RotateCcw, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ProgressTimeline } from "@/components/ProgressTimeline";
import { useNewsletter } from "@/hooks/use-newsletter";
import { formatDuration } from "@/lib/utils";

export function GeneratePage() {
  const { generate, generating, data, executionTimeMs, error, clearError } = useNewsletter();
  const [hasStarted, setHasStarted] = useState(false);
  const navigate = useNavigate();

  async function handleGenerate() {
    setHasStarted(true);
    clearError();
    try {
      await generate();
      toast.success("Newsletter generated successfully");
    } catch {
      toast.error("Newsletter generation failed");
    }
  }

  const succeeded = hasStarted && !generating && !error && Boolean(data);
  const failed = hasStarted && !generating && Boolean(error);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card className="overflow-hidden">
        <CardHeader className="items-center text-center">
          <div className="mb-2 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Sparkles className="h-7 w-7" />
          </div>
          <CardTitle className="text-xl">Generate Today&apos;s Newsletter</CardTitle>
          <CardDescription>
            Runs the full LangGraph pipeline: 8 parallel collectors → aggregation → semantic
            deduplication → ranking → GPT summarization → HTML/Markdown/JSON rendering.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-4 pb-8">
          {!hasStarted && (
            <Button size="lg" className="h-12 px-8 text-base" onClick={handleGenerate}>
              <Sparkles className="h-5 w-5" />
              Generate Today&apos;s Newsletter
            </Button>
          )}

          {hasStarted && (
            <>
              <div className="w-full">
                <ProgressTimeline
                  isRunning={generating}
                  isComplete={succeeded}
                  hasError={failed}
                />
              </div>

              {generating && (
                <p className="text-xs text-muted-foreground">
                  This typically takes 15–40 seconds depending on source latency and LLM response
                  time…
                </p>
              )}

              {succeeded && (
                <div className="flex w-full flex-col items-center gap-3 rounded-lg border border-success/30 bg-success/5 p-4">
                  <p className="text-sm font-medium text-success">
                    Newsletter generated in {formatDuration(executionTimeMs ?? 0)}
                  </p>
                  <Button onClick={() => navigate("/newsletter")}>
                    View Newsletter
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {failed && (
                <div className="flex w-full flex-col items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    {error?.message ?? "Generation failed"}
                  </div>
                  <Button variant="outline" onClick={handleGenerate}>
                    <RotateCcw className="h-4 w-4" />
                    Retry
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
