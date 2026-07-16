import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import type {
  DemoGenerateResponse,
  HealthResponse,
  NewsletterHistoryResponse,
  NewsletterResponse,
  OutlookDeliveryStatus,
  RootResponse,
} from "@/types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

export class ApiError extends Error {
  status?: number;
  detail?: string;

  constructor(message: string, status?: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
  headers: API_KEY ? { "X-API-Key": API_KEY } : undefined,
});

function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<{ detail?: string }>;
    const status = err.response?.status;
    const detail = err.response?.data?.detail;
    if (status === 401) {
      return new ApiError(
        "Unauthorized — check VITE_API_KEY matches the backend's API_AUTH_TOKEN.",
        status,
        detail,
      );
    }
    if (status === 404) {
      return new ApiError(detail ?? "Not found.", status, detail);
    }
    if (status === 502) {
      return new ApiError(
        detail ?? "The LangGraph pipeline failed to run. Check the backend logs.",
        status,
        detail,
      );
    }
    if (err.code === "ECONNABORTED") {
      return new ApiError("Request timed out — the pipeline may still be running.", status, detail);
    }
    if (!err.response) {
      return new ApiError(
        `Could not reach the API at ${BASE_URL}. Is the backend running?`,
        undefined,
        detail,
      );
    }
    return new ApiError(detail ?? err.message, status, detail);
  }
  return new ApiError(error instanceof Error ? error.message : "Unknown error occurred.");
}

/** Retries idempotent GET requests with exponential backoff on network errors or 5xx. */
async function getWithRetry<T>(
  url: string,
  config?: AxiosRequestConfig,
  maxAttempts = 3,
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await client.get<T>(url, config);
      return response.data;
    } catch (error) {
      lastError = error;
      const status = axios.isAxiosError(error) ? error.response?.status : undefined;
      const isRetryable = !status || status >= 500;
      if (!isRetryable || attempt === maxAttempts) break;
      const delayMs = 500 * 2 ** (attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  throw toApiError(lastError);
}

/**
 * Client for the six read-only/demo endpoints the Copilot UI is scoped to
 * (see AI Newsletter Automation's Swagger docs). `POST /generate-newsletter`
 * — the Power Automate production trigger — is intentionally not called
 * from this frontend; the UI only drives the Swagger-friendly demo path.
 */
export const api = {
  baseUrl: BASE_URL,
  hasApiKey: Boolean(API_KEY),

  async getRoot(): Promise<RootResponse> {
    return getWithRetry<RootResponse>("/");
  },

  async getHealth(): Promise<HealthResponse> {
    return getWithRetry<HealthResponse>("/health");
  },

  async demoGenerate(): Promise<DemoGenerateResponse> {
    try {
      const response = await client.post<DemoGenerateResponse>("/demo/generate", {});
      return response.data;
    } catch (error) {
      throw toApiError(error);
    }
  },

  async getLatestNewsletter(): Promise<NewsletterResponse> {
    return getWithRetry<NewsletterResponse>("/newsletter/latest");
  },

  async getLatestNewsletterHtml(): Promise<string> {
    try {
      const response = await client.get<string>("/newsletter/latest/html", {
        responseType: "text",
      });
      return response.data;
    } catch (error) {
      throw toApiError(error);
    }
  },

  async getHistory(limit = 20): Promise<NewsletterHistoryResponse> {
    return getWithRetry<NewsletterHistoryResponse>("/newsletter/history", { params: { limit } });
  },

  /** Real Outlook delivery status, as last reported by Power Automate - never mocked. */
  async getOutlookDeliveryStatus(): Promise<OutlookDeliveryStatus> {
    return getWithRetry<OutlookDeliveryStatus>("/integration/outlook/status");
  },
};
