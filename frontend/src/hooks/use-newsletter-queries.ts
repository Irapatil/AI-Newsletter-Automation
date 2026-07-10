import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { NewsletterHistoryResponse, NewsletterResponse } from "@/types/api";

export const NEWSLETTER_LATEST_KEY = ["newsletter", "latest"] as const;
const EXECUTION_TIME_KEY = ["newsletter", "lastExecutionMs"] as const;

export function useLatestNewsletter() {
  return useQuery<NewsletterResponse, ApiError>({
    queryKey: NEWSLETTER_LATEST_KEY,
    queryFn: api.getLatestNewsletter,
    retry: false,
  });
}

export function useLastExecutionTime() {
  return useQuery<number | null>({
    queryKey: EXECUTION_TIME_KEY,
    queryFn: () => null,
    enabled: false,
    initialData: null,
  });
}

interface GenerateResult {
  data: NewsletterResponse;
  executionTimeMs: number;
}

export function useGenerateNewsletter() {
  const queryClient = useQueryClient();

  return useMutation<GenerateResult, ApiError>({
    mutationFn: async () => {
      const startedAt = performance.now();
      const data = await api.generateNewsletter();
      return { data, executionTimeMs: performance.now() - startedAt };
    },
    onSuccess: ({ data, executionTimeMs }) => {
      queryClient.setQueryData(NEWSLETTER_LATEST_KEY, data);
      queryClient.setQueryData(EXECUTION_TIME_KEY, executionTimeMs);
    },
  });
}

export function useNewsletterHistory(limit = 20) {
  return useQuery<NewsletterHistoryResponse, ApiError>({
    queryKey: ["newsletter", "history", limit],
    queryFn: () => api.getHistory(limit),
  });
}
