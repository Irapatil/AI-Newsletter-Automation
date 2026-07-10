import { useQuery } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { HealthResponse } from "@/types/api";

interface UseHealthResult {
  health: HealthResponse | null;
  error: ApiError | null;
  loading: boolean;
  refetch: () => void;
}

export function useHealth(pollIntervalMs = 30_000): UseHealthResult {
  const query = useQuery<HealthResponse, ApiError>({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: pollIntervalMs > 0 ? pollIntervalMs : false,
    retry: 1,
  });

  return {
    health: query.data ?? null,
    error: query.error ?? null,
    loading: query.isLoading,
    refetch: () => {
      void query.refetch();
    },
  };
}
