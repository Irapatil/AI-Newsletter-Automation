import { motion } from "framer-motion";
import { Lightbulb, Newspaper } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ExecutiveSummaryCardProps {
  subject: string;
  summary: string;
  oneThingToWatch: string;
}

export function ExecutiveSummaryCard({
  subject,
  summary,
  oneThingToWatch,
}: ExecutiveSummaryCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <Card className="overflow-hidden border-primary/20 bg-gradient-to-br from-primary/10 via-card/70 to-card/70 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Newspaper className="h-4 w-4 text-primary" />
            Executive Summary
          </CardTitle>
          <p className="text-sm font-medium text-muted-foreground">{subject}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-p:text-foreground/90">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary}</ReactMarkdown>
          </div>
          {oneThingToWatch && (
            <div className="flex gap-2 rounded-xl border border-warning/30 bg-warning/10 p-3">
              <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-warning-foreground/80">
                  One Thing To Watch
                </p>
                <div className="prose prose-sm dark:prose-invert mt-1 max-w-none prose-p:text-foreground/90">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{oneThingToWatch}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
