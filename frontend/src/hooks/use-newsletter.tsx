import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, ApiError } from "@/lib/api";
import type { NewsletterResponse } from "@/types/api";

interface NewsletterState {
  data: NewsletterResponse | null;
  executionTimeMs: number | null;
  generating: boolean;
  loadingLatest: boolean;
  error: ApiError | null;
  generate: () => Promise<void>;
  loadLatest: () => Promise<void>;
  clearError: () => void;
}

const NewsletterContext = createContext<NewsletterState | undefined>(undefined);

export function NewsletterProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<NewsletterResponse | null>(null);
  const [executionTimeMs, setExecutionTimeMs] = useState<number | null>(null);
  const [generating, setGenerating] = useState(false);
  const [loadingLatest, setLoadingLatest] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const generate = useCallback(async () => {
    setGenerating(true);
    setError(null);
    const startedAt = performance.now();
    try {
      const response = await api.generateNewsletter();
      setData(response);
      setExecutionTimeMs(performance.now() - startedAt);
    } catch (err) {
      setError(err as ApiError);
      throw err;
    } finally {
      setGenerating(false);
    }
  }, []);

  const loadLatest = useCallback(async () => {
    setLoadingLatest(true);
    setError(null);
    try {
      const response = await api.getLatestNewsletter();
      setData(response);
      setExecutionTimeMs(null);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoadingLatest(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const value = useMemo<NewsletterState>(
    () => ({ data, executionTimeMs, generating, loadingLatest, error, generate, loadLatest, clearError }),
    [data, executionTimeMs, generating, loadingLatest, error, generate, loadLatest, clearError],
  );

  return <NewsletterContext.Provider value={value}>{children}</NewsletterContext.Provider>;
}

export function useNewsletter(): NewsletterState {
  const ctx = useContext(NewsletterContext);
  if (!ctx) throw new Error("useNewsletter must be used within a NewsletterProvider");
  return ctx;
}
