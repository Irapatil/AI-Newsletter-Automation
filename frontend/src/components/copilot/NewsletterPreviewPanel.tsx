import { useState } from "react";
import { Check, Copy, Download, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { copyToClipboard, downloadTextFile } from "@/lib/utils";

interface NewsletterPreviewPanelProps {
  html: string;
  markdown: string;
  subject: string;
}

export function NewsletterPreviewPanel({ html, markdown, subject }: NewsletterPreviewPanelProps) {
  const [copiedHtml, setCopiedHtml] = useState(false);
  const [copiedMarkdown, setCopiedMarkdown] = useState(false);

  async function handleCopy(kind: "html" | "markdown") {
    const ok = await copyToClipboard(kind === "html" ? html : markdown);
    if (!ok) {
      toast.error("Couldn't copy to clipboard — your browser may be blocking it.");
      return;
    }
    toast.success(`${kind === "html" ? "HTML" : "Markdown"} copied to clipboard.`);
    if (kind === "html") {
      setCopiedHtml(true);
      setTimeout(() => setCopiedHtml(false), 1800);
    } else {
      setCopiedMarkdown(true);
      setTimeout(() => setCopiedMarkdown(false), 1800);
    }
  }

  const fileSlug = subject.replace(/[^a-z0-9]+/gi, "-").toLowerCase().slice(0, 60) || "newsletter";

  return (
    <Card className="overflow-hidden border-border/60 bg-card/70 backdrop-blur-sm">
      <CardHeader className="flex flex-col gap-3 pb-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle className="text-base">Newsletter Preview</CardTitle>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => window.open(`${api.baseUrl}/newsletter/latest/html`, "_blank", "noopener")}
          >
            <ExternalLink className="h-3.5 w-3.5" /> View HTML Newsletter
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => downloadTextFile(`${fileSlug}.html`, html, "text/html")}
          >
            <Download className="h-3.5 w-3.5" /> Download HTML
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => downloadTextFile(`${fileSlug}.md`, markdown, "text/markdown")}
          >
            <Download className="h-3.5 w-3.5" /> Download Markdown
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleCopy("html")}>
            {copiedHtml ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />} Copy
            HTML
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleCopy("markdown")}>
            {copiedMarkdown ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}{" "}
            Copy Markdown
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-xl border border-border/60 bg-white">
          <iframe
            title="Newsletter preview"
            srcDoc={html}
            sandbox=""
            className="h-[560px] w-full"
          />
        </div>
      </CardContent>
    </Card>
  );
}
