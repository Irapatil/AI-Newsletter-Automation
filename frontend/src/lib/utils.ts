import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diffMs = Date.now() - then;
  const diffSec = Math.round(diffMs / 1000);
  const diffMin = Math.round(diffSec / 60);
  const diffHour = Math.round(diffMin / 60);
  const diffDay = Math.round(diffHour / 24);

  if (Math.abs(diffSec) < 60) return "just now";
  if (Math.abs(diffMin) < 60) return `${diffMin} min${Math.abs(diffMin) === 1 ? "" : "s"} ago`;
  if (Math.abs(diffHour) < 24) return `${diffHour} hour${Math.abs(diffHour) === 1 ? "" : "s"} ago`;
  return `${diffDay} day${Math.abs(diffDay) === 1 ? "" : "s"} ago`;
}

export function formatDuration(ms: number): string {
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const remSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remSeconds}s`;
}

/**
 * Rough client-side token/cost estimate for display only. There is no
 * server-provided token count (the API does not track OpenAI usage), so
 * this is a heuristic (~4 chars/token) clearly labeled "Estimated" in the UI.
 */
export function estimateTokensAndCost(texts: string[]): { tokens: number; costUsd: number } {
  const totalChars = texts.reduce((sum, t) => sum + t.length, 0);
  const tokens = Math.round(totalChars / 4);
  // Blended rough rate for a small gpt-4o-class summarization + embedding workload.
  const costUsd = (tokens / 1_000_000) * 2.5;
  return { tokens, costUsd };
}

export function downloadTextFile(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
