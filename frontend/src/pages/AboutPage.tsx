import { motion } from "framer-motion";
import {
  Brain,
  Github,
  Mail,
  Sparkles,
  Target,
  Workflow,
} from "lucide-react";
import { ArchitectureDiagram } from "@/components/copilot/ArchitectureDiagram";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TECH_STACK = [
  { icon: Workflow, name: "LangGraph", role: "Deterministic multi-agent orchestration (StateGraph)" },
  { icon: Sparkles, name: "FastAPI", role: "Async Python backend, OpenAPI/Swagger-first" },
  { icon: Brain, name: "OpenAI", role: "GPT summarization + embedding-based deduplication" },
  { icon: Sparkles, name: "Microsoft Copilot-style UX", role: "This chat-first presentation layer" },
  { icon: Workflow, name: "Power Automate", role: "Daily trigger + Outlook delivery, no server ops" },
  { icon: Github, name: "GitHub / arXiv / NewsAPI", role: "Live multi-source data collection" },
];

export function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2 text-center"
      >
        <h1 className="text-3xl font-semibold tracking-tight">About This Project</h1>
        <p className="text-sm text-muted-foreground sm:text-base">
          Enterprise multi-agent AI newsletter automation, end to end.
        </p>
      </motion.div>

      <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4 text-primary" /> Business Problem
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>
            Staying current on AI news, funding, research, hiring, and policy means monitoring
            dozens of scattered sources every day — a task too time-consuming to do well
            manually, and too nuanced (dedup, ranking, relevance) for a simple RSS digest.
          </p>
          <p>
            This system automates that entirely: eight specialized agents collect from live
            sources in parallel, a LangGraph pipeline deduplicates and ranks the results, and GPT
            produces an executive-ready newsletter — delivered to Outlook every morning with zero
            manual effort.
          </p>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">Architecture</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          A single compiled LangGraph <code className="rounded bg-muted px-1">StateGraph</code> fans
          out to eight collector agents in parallel, then flows through aggregation,
          deduplication, ranking, GPT generation, and HTML formatting before Power Automate
          delivers the result to Outlook.
        </p>
        <ArchitectureDiagram />
      </div>

      <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-base">Technology Stack</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          {TECH_STACK.map((tech) => (
            <div
              key={tech.name}
              className="flex items-start gap-3 rounded-xl border border-border/50 bg-background/40 p-3"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                <tech.icon className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-medium">{tech.name}</p>
                <p className="text-xs text-muted-foreground">{tech.role}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
        <CardContent className="flex items-center gap-3 py-5 text-sm text-muted-foreground">
          <Mail className="h-4 w-4 shrink-0 text-primary" />
          Every fact shown in this Copilot comes directly from the live FastAPI backend — this UI
          is a presentation layer only, with no business logic of its own.
        </CardContent>
      </Card>
    </div>
  );
}
