import { motion } from "framer-motion";
import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import type { NewsletterSection } from "@/types/api";

interface SectionCardProps {
  section: NewsletterSection;
  index?: number;
}

export function SectionCard({ section, index = 0 }: SectionCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
    >
      <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span>{section.title}</span>
            <Badge variant="secondary">{section.articles.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {section.articles.length === 0 && (
            <p className="text-sm text-muted-foreground">No stories cleared the bar today.</p>
          )}
          {section.articles.slice(0, 6).map((article) => (
            <a
              key={article.id}
              href={article.url}
              target="_blank"
              rel="noreferrer"
              className="group block rounded-lg border border-transparent p-2 -m-2 transition-colors hover:border-border/60 hover:bg-accent/40"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium leading-snug text-foreground group-hover:text-primary">
                  {article.title}
                </p>
                <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              </div>
              {article.ai_summary && (
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                  {article.ai_summary}
                </p>
              )}
              <div className="mt-1.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                <span>{article.source}</span>
                <span aria-hidden>·</span>
                <span>{formatRelativeTime(article.published_at)}</span>
              </div>
            </a>
          ))}
        </CardContent>
      </Card>
    </motion.div>
  );
}
