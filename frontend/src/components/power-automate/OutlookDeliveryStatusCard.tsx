import { motion } from "framer-motion";
import { CheckCircle2, Clock, MailWarning } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useOutlookDeliveryStatus } from "@/hooks/use-outlook-delivery-status";
import { formatDateTime } from "@/lib/utils";

/**
 * The single source of truth for Outlook delivery state, polled every 30s
 * from `GET /integration/outlook/status`. Power Automate's flow calls
 * `POST /integration/outlook/status` right after its real "Send an email
 * (V2)" action completes - nothing here is hardcoded or simulated.
 */
export function OutlookDeliveryStatusCard() {
  const { data, isLoading, isError } = useOutlookDeliveryStatus();

  return (
    <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <MailWarning className="h-4 w-4 text-primary" /> Outlook Delivery
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && <Skeleton className="h-16 w-full rounded-xl" />}

        {!isLoading && isError && (
          <p className="text-sm text-muted-foreground">
            Couldn't reach the integration status endpoint - it will retry automatically.
          </p>
        )}

        {!isLoading && !isError && data?.delivery_status === "delivered" && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2 rounded-xl border border-success/30 bg-success/10 p-4"
          >
            <p className="flex items-center gap-2 text-sm font-semibold text-success">
              <CheckCircle2 className="h-4 w-4" /> Outlook Connected
            </p>
            <p className="flex items-center gap-2 text-sm font-semibold text-success">
              <CheckCircle2 className="h-4 w-4" /> Email Delivered Successfully
            </p>
            <div className="pt-1 text-xs text-muted-foreground">
              <p>
                <span className="font-medium text-foreground/80">Last Delivery:</span>{" "}
                {data.last_delivery_time ? formatDateTime(data.last_delivery_time) : "—"}
              </p>
              {data.recipient_count !== null && <p>Recipients: {data.recipient_count}</p>}
              {data.message_id && <p className="truncate">Message ID: {data.message_id}</p>}
            </div>
          </motion.div>
        )}

        {!isLoading && !isError && data?.delivery_status === "failed" && (
          <div className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <MailWarning className="h-4 w-4 shrink-0" />
            Outlook reported a failed delivery
            {data.last_delivery_time ? ` at ${formatDateTime(data.last_delivery_time)}` : ""}.
          </div>
        )}

        {!isLoading && !isError && data?.delivery_status === "pending" && (
          <div className="flex items-center gap-2 rounded-xl border border-border/50 bg-background/40 p-4 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 shrink-0" />
            Waiting for scheduled Outlook delivery.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
