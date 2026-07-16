import { useQuery } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { NewsletterHistoryResponse } from "@/types/api";

export function useNewsletterHistory(limit = 8) {
  return useQuery<NewsletterHistoryResponse, ApiError>({
    queryKey: ["newsletter", "history", limit],
    queryFn: () => api.getHistory(limit),
  });
}
