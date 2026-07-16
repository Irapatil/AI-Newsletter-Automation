import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Settings2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ConfigRow {
  label: string;
  value: string;
  detail?: string;
}

const CONFIG_ROWS: ConfigRow[] = [
  { label: "Trigger", value: "Recurrence", detail: "Daily at 8:00 AM" },
  { label: "Action 1", value: "HTTP POST", detail: "Endpoint: /demo/generate" },
  { label: "Action 2", value: "Parse JSON", detail: "Schema generated from a sample payload" },
  { label: "Action 3", value: "Compose", detail: "HTML email body" },
  { label: "Action 4", value: "Send an Email (V2)", detail: "Outlook connector" },
];

export function AutomationConfigPanel() {
  const [open, setOpen] = useState(false);

  return (
    <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
      <CardHeader className="pb-0">
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          className="flex w-full items-center justify-between text-left"
          aria-expanded={open}
        >
          <span className="flex items-center gap-2 text-base font-semibold">
            <Settings2 className="h-4 w-4 text-primary" /> Power Automate Configuration
          </span>
          <ChevronDown
            className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")}
          />
        </button>
      </CardHeader>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <CardContent className="pt-4">
              <dl className="divide-y divide-border/60">
                {CONFIG_ROWS.map((row) => (
                  <div key={row.label} className="flex flex-wrap items-center gap-2 py-2.5">
                    <dt className="w-24 shrink-0 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      {row.label}
                    </dt>
                    <dd className="flex flex-1 flex-wrap items-center gap-2">
                      <Badge variant="secondary">{row.value}</Badge>
                      {row.detail && (
                        <span className="text-xs text-muted-foreground">{row.detail}</span>
                      )}
                    </dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
