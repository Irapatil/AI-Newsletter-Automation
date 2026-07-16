/**
 * Mirrors app/models/api_models.py, app/models/newsletter.py, and
 * app/models/article.py exactly. Keep these in sync with the backend
 * Pydantic schemas.
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

export type NewsCategory =
  | "global_news"
  | "company_news"
  | "funding"
  | "talent"
  | "research"
  | "opensource"
  | "policy"
  | "model_releases";

export interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  category: NewsCategory;
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

export interface AgentExecutionRecord {
  node: string;
  status: "success";
  execution_time_seconds: number;
  items_processed: number;
}

export interface TokenUsage {
  prompt_and_completion_tokens: number;
  is_estimated: boolean;
}

export type RunStatus = "success" | "partial_success";

export interface NewsletterResponse {
  subject: string;
  summary: string;
  generated_at: string;
  execution_time_seconds: number;
  newsletter_html: string;
  newsletter_markdown: string;
  newsletter_json: NewsletterContentPayload;
  statistics: NewsletterStats;
  sources_used: string[];
  agent_execution: AgentExecutionRecord[];
  provider: string;
  status: RunStatus;
  token_usage: TokenUsage;
  estimated_cost_usd: number;
  errors: string[];
}

export interface DemoGenerateResponse {
  subject: string;
  generated_at: string;
  execution_time_seconds: number;
  provider: string;
  status: RunStatus;
  statistics: NewsletterStats;
  sources_used: string[];
  agent_execution: AgentExecutionRecord[];
  token_usage: TokenUsage;
  estimated_cost_usd: number;
  newsletter_markdown: string;
  html_preview_url: string;
  errors: string[];
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

export type OutlookDeliveryState = "pending" | "delivered" | "failed";

export interface OutlookDeliveryStatus {
  delivery_status: OutlookDeliveryState;
  last_delivery_time: string | null;
  message_id: string | null;
  recipient_count: number | null;
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

export const SECTION_ORDER: string[] = [
  "global_news",
  "company_news",
  "model_releases",
  "funding",
  "talent",
  "research",
  "opensource",
  "policy",
];

/** Expected LangGraph node execution order for the happy path (see app/graph/workflow.py). */
export const LANGGRAPH_NODES = [
  { key: "Orchestrator", label: "Orchestrator" },
  { key: "GlobalNewsAgent", label: "Global News Agent" },
  { key: "CompanyNewsAgent", label: "Company News Agent" },
  { key: "ResearchAgent", label: "Research Agent" },
  { key: "FundingAgent", label: "Funding Agent" },
  { key: "TalentAgent", label: "Talent Agent" },
  { key: "PolicyAgent", label: "Policy Agent" },
  { key: "OpenSourceAgent", label: "Open Source Agent" },
  { key: "ModelReleaseAgent", label: "Model Release Agent" },
  { key: "AggregatorAgent", label: "Aggregator" },
  { key: "DeduplicationAgent", label: "Deduplication" },
  { key: "RankingAgent", label: "Ranking" },
  { key: "NewsletterGeneratorAgent", label: "Newsletter Generator" },
  { key: "HTMLFormatterAgent", label: "HTML Formatter" },
] as const;

export type LangGraphNodeKey = (typeof LANGGRAPH_NODES)[number]["key"];
