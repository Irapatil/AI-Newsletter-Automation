import {
  CheckCircle2,
  Clock,
  Code2,
  FileCode2,
  FileJson,
  Layers,
  ListChecks,
  Mail,
  Send,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type StepId =
  | "trigger"
  | "http"
  | "aggregation"
  | "summarization"
  | "htmlGeneration"
  | "receive"
  | "extract"
  | "compose"
  | "send"
  | "delivered";

export type StepStatus = "pending" | "running" | "success" | "error";

export interface StepState {
  id: StepId;
  status: StepStatus;
  timeMs?: number;
  items?: number;
}

export interface StepDefinition {
  id: StepId;
  title: string;
  description: string;
  icon: LucideIcon;
  /** True for steps that never make a real outbound call in this environment. */
  simulated?: boolean;
}

export const STEP_DEFINITIONS: StepDefinition[] = [
  {
    id: "trigger",
    title: "Daily Schedule",
    description: "Recurrence trigger fires every day at 8:00 AM.",
    icon: Clock,
  },
  {
    id: "http",
    title: "FastAPI Endpoint",
    description:
      "POST to the FastAPI backend, which runs the full LangGraph pipeline server-side and returns the completed newsletter. This live console calls /demo/generate; the scheduled production flow calls /generate-newsletter — identical pipeline, identical telemetry.",
    icon: Send,
  },
  {
    id: "aggregation",
    title: "Content Aggregation",
    description:
      "The eight parallel collector agents fan in; results are aggregated, deduplicated, and ranked across six weighted dimensions.",
    icon: Layers,
  },
  {
    id: "summarization",
    title: "AI Summarization",
    description: "GPT generates per-article summaries, an executive summary, and the subject line.",
    icon: Sparkles,
  },
  {
    id: "htmlGeneration",
    title: "HTML Generation",
    description: "The newsletter is rendered to HTML, Markdown, and JSON.",
    icon: FileCode2,
  },
  {
    id: "receive",
    title: "Receive JSON Response",
    description: "Power Automate's HTTP action receives the pipeline's JSON response.",
    icon: FileJson,
  },
  {
    id: "extract",
    title: "Extract",
    description: "Parse JSON extracts subject, HTML newsletter, summary, and statistics.",
    icon: ListChecks,
  },
  {
    id: "compose",
    title: "Compose Outlook Email",
    description: "The HTML newsletter is composed into the email body.",
    icon: Code2,
  },
  {
    id: "send",
    title: "Send Outlook Email",
    description: "Outlook: Send an Email (V2) delivers the composed message to the distribution list.",
    icon: Mail,
    simulated: true,
  },
  {
    id: "delivered",
    title: "Outlook Delivery",
    description: "The daily newsletter has reached the distribution list.",
    icon: CheckCircle2,
    simulated: true,
  },
];

export function initialStepStates(): StepState[] {
  return STEP_DEFINITIONS.map((def) => ({ id: def.id, status: "pending" }));
}
