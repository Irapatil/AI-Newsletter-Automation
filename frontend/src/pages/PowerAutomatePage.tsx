import { motion } from "framer-motion";
import { Check, Mail, PlayCircle, RotateCcw, Sparkles } from "lucide-react";
import { AutomationConfigPanel } from "@/components/power-automate/AutomationConfigPanel";
import { ConnectionStatusPanel } from "@/components/power-automate/ConnectionStatusPanel";
import { OutlookDeliveryStatusCard } from "@/components/power-automate/OutlookDeliveryStatusCard";
import { WorkflowInsights } from "@/components/power-automate/WorkflowInsights";
import { OutlookEmailPreview } from "@/components/power-automate/OutlookEmailPreview";
import { WorkflowStepCard } from "@/components/power-automate/WorkflowStepCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useAutomationInsights } from "@/hooks/use-automation-insights";
import { useAutomationWorkflow } from "@/hooks/use-automation-workflow";
import { useOutlookDeliveryStatus } from "@/hooks/use-outlook-delivery-status";
import { STEP_DEFINITIONS } from "@/lib/power-automate-steps";
import { formatDateTime } from "@/lib/utils";

export function PowerAutomatePage() {
  const { steps, narration, result, run, retry, isRunning, isError, errorMessage, hasRun } =
    useAutomationWorkflow();
  const [insightsEnabled, setInsightsEnabled] = useAutomationInsights();
  const { data: outlookStatus } = useOutlookDeliveryStatus();
  const outlookDeliveryStatus = outlookStatus?.delivery_status;
  const outlookConnected = outlookDeliveryStatus === "delivered";
  const outlookFailed = outlookDeliveryStatus === "failed";

  const allComplete = steps.every((s) => s.status === "success");
  const extractStep = steps.find((s) => s.id === "extract");

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2 text-center"
      >
        <h1 className="text-3xl font-semibold tracking-tight">Microsoft Power Automate</h1>
        <p className="text-sm text-muted-foreground sm:text-base">
          How the daily newsletter reaches Outlook without a human in the loop.
        </p>
      </motion.div>

      <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
        <CardContent className="flex flex-col items-center gap-4 py-6 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-3">
            <label
              htmlFor="automation-insights"
              className="flex items-center gap-2 text-sm font-medium"
              title="Displays the current execution status of the newsletter automation pipeline."
            >
              <Sparkles className="h-4 w-4 text-primary" /> Automation Insights
            </label>
            <Switch
              id="automation-insights"
              checked={insightsEnabled}
              onCheckedChange={setInsightsEnabled}
            />
          </div>
          <Button onClick={run} disabled={isRunning} size="lg" className="rounded-xl">
            <PlayCircle className="h-4 w-4" />
            {isRunning ? "Running…" : hasRun ? "Execute Again" : "Execute Automation"}
          </Button>
        </CardContent>
      </Card>

      <OutlookDeliveryStatusCard />

      {insightsEnabled && <WorkflowInsights lines={narration} />}

      <div className="relative space-y-4">
        {STEP_DEFINITIONS.map((definition, index) => {
          const state = steps[index];
          return (
            <div key={definition.id}>
              <WorkflowStepCard
                index={index}
                definition={definition}
                state={state}
                outlookDeliveryStatus={outlookDeliveryStatus}
              >
                {definition.id === "extract" && extractStep?.status === "success" && result && (
                  <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-foreground/80">
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3 w-3 text-success" /> Subject
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3 w-3 text-success" /> HTML Newsletter (
                      {Math.round(result.html.length / 1024)} KB)
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3 w-3 text-success" /> Summary
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3 w-3 text-success" /> Statistics (
                      {result.demo.statistics.stories_selected} stories)
                    </li>
                  </ul>
                )}
              </WorkflowStepCard>
              {index < STEP_DEFINITIONS.length - 1 && <div className="ml-9 h-4 w-px bg-border/70" />}
            </div>
          );
        })}
      </div>

      {isError && (
        <Card className="border-destructive/40 bg-destructive/10">
          <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
            <p className="text-sm text-destructive">
              <span className="font-semibold">HTTP Error:</span>{" "}
              {errorMessage ?? "The pipeline call failed."}
            </p>
            <Button size="sm" variant="outline" onClick={retry}>
              <RotateCcw className="h-3.5 w-3.5" /> Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {result && allComplete && (
        <>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="border-success/40 bg-success/10">
              <CardContent className="space-y-1 py-6 text-center">
                <p className="flex items-center justify-center gap-2 text-lg font-semibold text-success">
                  <Check className="h-5 w-5" /> Automation Completed Successfully
                </p>
                <p className="text-sm text-foreground/90">Newsletter Generation Complete</p>
                <div className="text-sm text-muted-foreground">
                  Outlook Delivery Status{" "}
                  <Badge
                    variant={outlookConnected ? "success" : outlookFailed ? "destructive" : "outline"}
                    className="ml-1 align-middle"
                  >
                    {outlookConnected
                      ? "Connected"
                      : outlookFailed
                        ? "Delivery Failed"
                        : "Integration Ready"}
                  </Badge>
                </div>
                {result.demo.status === "partial_success" && (
                  <Badge variant="warning" className="mt-2">
                    partial_success — one or more collectors failed, remaining sources still used
                  </Badge>
                )}
              </CardContent>
            </Card>
          </motion.div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Subject", value: result.demo.subject },
              { label: "Generated", value: formatDateTime(result.demo.generated_at) },
              { label: "Execution Time", value: `${result.demo.execution_time_seconds.toFixed(1)}s` },
              {
                label: "Articles Collected",
                value: String(result.demo.statistics.aggregated_count),
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-border/50 bg-background/40 p-3"
              >
                <p className="truncate text-sm font-semibold" title={stat.value}>
                  {stat.value}
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>

          <OutlookEmailPreview
            subject={result.demo.subject}
            generatedAt={result.demo.generated_at}
            html={result.html}
          />
        </>
      )}

      <ConnectionStatusPanel />
      <AutomationConfigPanel />

      <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
        <CardContent className="flex items-start gap-3 py-5 text-sm text-muted-foreground">
          <Mail className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <div>
            Every collector agent isolates its own failures — one broken source never fails the
            whole run. A <Badge variant="warning">partial_success</Badge> status means the
            newsletter still generated from the remaining sources. A{" "}
            <span className="font-medium text-foreground">Configure run after</span> setting on
            the real Outlook action (is successful, has timed out, has failed) ensures a hard
            failure still notifies an ops mailbox instead of silently skipping a day.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
