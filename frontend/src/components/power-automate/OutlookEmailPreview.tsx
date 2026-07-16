import { motion } from "framer-motion";
import { Mail } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { formatDateTime } from "@/lib/utils";

interface OutlookEmailPreviewProps {
  subject: string;
  generatedAt: string;
  html: string;
}

const FROM_ADDRESS = "newsletter@company.com";
const TO_ADDRESS = "team@company.com";

export function OutlookEmailPreview({ subject, generatedAt, html }: OutlookEmailPreviewProps) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="overflow-hidden border-border/60 bg-card/70 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-primary" /> Outlook Email Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-xl border border-border/60 bg-white">
            <div className="space-y-1.5 bg-muted/40 px-4 py-3 text-xs text-neutral-700">
              <div className="flex gap-2">
                <span className="w-14 shrink-0 font-medium text-neutral-500">From</span>
                <span>{FROM_ADDRESS}</span>
              </div>
              <div className="flex gap-2">
                <span className="w-14 shrink-0 font-medium text-neutral-500">To</span>
                <span>{TO_ADDRESS}</span>
              </div>
              <div className="flex gap-2">
                <span className="w-14 shrink-0 font-medium text-neutral-500">Subject</span>
                <span className="font-medium text-neutral-900">{subject}</span>
              </div>
              <div className="flex gap-2">
                <span className="w-14 shrink-0 font-medium text-neutral-500">Sent</span>
                <span>{formatDateTime(generatedAt)}</span>
              </div>
            </div>
            <Separator />
            <iframe title="Outlook email body preview" srcDoc={html} sandbox="" className="h-[520px] w-full" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
