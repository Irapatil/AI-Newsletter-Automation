import { useQuery } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { OutlookDeliveryStatus } from "@/types/api";

const POLL_INTERVAL_MS = 30_000;

/**
 * Polls the real Outlook delivery status Power Automate reports to
 * `POST /integration/outlook/status`. No hardcoded or simulated state -
 * defaults to `delivery_status: "pending"` until a real callback arrives.
 */
export function useOutlookDeliveryStatus() {
  return useQuery<OutlookDeliveryStatus, ApiError>({
    queryKey: ["integration", "outlook-status"],
    queryFn: api.getOutlookDeliveryStatus,
    refetchInterval: POLL_INTERVAL_MS,
    retry: 1,
  });
}
