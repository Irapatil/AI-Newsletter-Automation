import { ExternalLink } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { NewsletterContentPayload } from "@/types/api";

interface NewsletterViewerProps {
  html: string;
  markdown: string;
  content: NewsletterContentPayload;
}

export function NewsletterViewer({ html, markdown, content }: NewsletterViewerProps) {
  return (
    <Tabs defaultValue="preview" className="w-full">
      <TabsList>
        <TabsTrigger value="preview">Preview</TabsTrigger>
        <TabsTrigger value="sections">Sections</TabsTrigger>
        <TabsTrigger value="markdown">Markdown</TabsTrigger>
      </TabsList>

      <TabsContent value="preview">
        <div className="overflow-hidden rounded-xl border border-border bg-white shadow-sm">
          <iframe
            title="Newsletter HTML preview"
            srcDoc={html}
            sandbox=""
            className="h-[720px] w-full bg-white"
          />
        </div>
      </TabsContent>

      <TabsContent value="sections">
        <div className="space-y-4">
          <Card>
            <CardContent className="space-y-2 p-5">
              <h3 className="text-sm font-semibold text-muted-foreground">Executive Summary</h3>
              <p className="text-sm leading-relaxed">{content.executive_summary}</p>
            </CardContent>
          </Card>

          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="space-y-2 p-5">
              <h3 className="text-sm font-semibold text-primary">👀 One Thing To Watch</h3>
              <p className="text-sm leading-relaxed">{content.one_thing_to_watch}</p>
            </CardContent>
          </Card>

          {content.sections.map((section) => (
            <Card key={section.key}>
              <CardContent className="space-y-3 p-5">
                <h3 className="text-sm font-semibold">{section.title}</h3>
                <ScrollArea className="max-h-80 pr-3">
                  <div className="space-y-3">
                    {section.articles.map((article) => (
                      <a
                        key={article.id}
                        href={article.url}
                        target="_blank"
                        rel="noreferrer"
                        className="group block rounded-lg border border-border p-3 transition-colors hover:border-primary/40 hover:bg-accent/50"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-medium leading-snug group-hover:text-primary">
                            {article.title}
                          </p>
                          <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                        </div>
                        <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                          <span>{article.source}</span>
                          <span>•</span>
                          <Badge variant="outline" className="h-4 px-1.5 py-0 text-[10px]">
                            score {article.scores.total.toFixed(2)}
                          </Badge>
                        </div>
                        {article.ai_summary && (
                          <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">
                            {article.ai_summary}
                          </p>
                        )}
                      </a>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="markdown">
        <Card>
          <CardContent className="p-0">
            <ScrollArea className="max-h-[720px]">
              <pre className="whitespace-pre-wrap p-5 font-mono text-xs leading-relaxed">
                {markdown}
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
