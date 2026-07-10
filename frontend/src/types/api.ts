/**
 * Mirrors app/models/api_models.py and app/models/newsletter.py exactly.
 * Keep these in sync with the backend Pydantic schemas.
 */

export interface RootResponse {
  name: string;
  version: string;
  description: string;
  docs_url: string | null;
}

export type ProviderStatus =
  | "ok"
  | "configured"
  | "mock"
  | "not_configured"
  | "authenticated"
  | "public"
  | "available"
  | "operational"
  | "error";

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  providers: Record<string, ProviderStatus | string>;
}

export interface GenerateNewsletterRequest {
  requested_by?: string | null;
}

export interface NewsletterStats {
  aggregated_count: number;
  duplicates_removed: number;
  ranked_count: number;
  stories_selected: number;
}

export interface ArticleScores {
  freshness: number;
  importance: number;
  business_impact: number;
  source_credibility: number;
  research_impact: number;
  ai_relevance: number;
  total: number;
}

export interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  category: string;
  published_at: string;
  snippet: string;
  content: string;
  author: string | null;
  tags: string[];
  metadata: Record<string, unknown>;
  scores: ArticleScores;
  ai_summary: string | null;
}

export interface NewsletterSection {
  key: string;
  title: string;
  articles: Article[];
}

export interface NewsletterContentPayload {
  subject: string;
  executive_summary: string;
  sections: NewsletterSection[];
  one_thing_to_watch: string;
  generated_at: string;
}

export interface NewsletterResponse {
  subject: string;
  summary: string;
  html: string;
  markdown: string;
  json: NewsletterContentPayload;
  timestamp: string;
  errors: string[];
  stats: NewsletterStats;
}

export interface NewsletterHistoryItem {
  id: string;
  subject: string;
  timestamp: string;
}

export interface NewsletterHistoryResponse {
  items: NewsletterHistoryItem[];
  count: number;
}

export interface ErrorResponse {
  detail: string;
}

export const SECTION_TITLES: Record<string, string> = {
  global_news: "🌍 Global AI News",
  company_news: "🏢 Company Moves",
  model_releases: "🚀 New Models",
  funding: "💰 Investments",
  talent: "👩‍💻 Talent Trends",
  research: "📚 Research Highlights",
  opensource: "🔓 Open Source",
  policy: "⚖ Policy & Regulation",
};

export const LANGGRAPH_NODES = [
  { key: "global_news", label: "Global News Agent" },
  { key: "company_news", label: "Company Agent" },
  { key: "funding", label: "Funding Agent" },
  { key: "research", label: "Research Agent" },
  { key: "talent", label: "Talent Agent" },
  { key: "policy", label: "Policy Agent" },
  { key: "opensource", label: "Open Source Agent" },
  { key: "model_releases", label: "Model Release Agent" },
  { key: "aggregator", label: "Aggregator" },
  { key: "deduplication", label: "Deduplication" },
  { key: "ranking", label: "Ranking" },
  { key: "newsletter_generator", label: "Newsletter Generator" },
  { key: "html_formatter", label: "HTML Formatter" },
] as const;

export type LangGraphNodeKey = (typeof LANGGRAPH_NODES)[number]["key"];
