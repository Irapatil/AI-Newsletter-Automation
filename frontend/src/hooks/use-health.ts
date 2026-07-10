import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { HealthResponse } from "@/types/api";

interface UseHealthResult {
  health: HealthResponse | null;
  error: ApiError | null;
  loading: boolean;
  refetch: () => void;
}

export function useHealth(pollIntervalMs = 30_000): UseHealthResult {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const data = await api.getHealth();
        if (!cancelled) {
          setHealth(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err as ApiError);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const interval = pollIntervalMs > 0 ? setInterval(load, pollIntervalMs) : undefined;

    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [pollIntervalMs, tick]);

  return { health, error, loading, refetch: () => setTick((t) => t + 1) };
}
