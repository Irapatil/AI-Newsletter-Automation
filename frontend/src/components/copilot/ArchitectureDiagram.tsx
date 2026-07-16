import { motion } from "framer-motion";
import {
  ArrowRight,
  GitBranch,
  Layers,
  ListOrdered,
  Mail,
  Server,
  Sparkles,
  Workflow,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STAGES = [
  { icon: Server, label: "FastAPI" },
  { icon: Workflow, label: "LangGraph" },
  { icon: GitBranch, label: "Parallel Agents" },
  { icon: Layers, label: "Aggregator" },
  { icon: ListOrdered, label: "Ranking" },
  { icon: Sparkles, label: "GPT" },
  { icon: Server, label: "HTML" },
  { icon: Workflow, label: "Power Automate" },
  { icon: Mail, label: "Outlook" },
];

export function ArchitectureDiagram() {
  return (
    <Card className="border-border/60 bg-card/70 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Architecture</CardTitle>
        <p className="text-sm text-muted-foreground">
          One FastAPI call runs the whole path below, end to end, on every request.
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center justify-center gap-x-1 gap-y-4">
          {STAGES.map((stage, index) => (
            <div key={stage.label} className="flex items-center">
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.06 }}
                className="flex flex-col items-center gap-2 rounded-xl border border-border/50 bg-background/40 px-3 py-3"
              >
                <stage.icon className="h-5 w-5 text-primary" />
                <span className="whitespace-nowrap text-xs font-medium text-foreground/90">
                  {stage.label}
                </span>
              </motion.div>
              {index < STAGES.length - 1 && (
                <motion.div
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.8, repeat: Infinity, delay: index * 0.15 }}
                >
                  <ArrowRight className="mx-1 h-4 w-4 text-muted-foreground" />
                </motion.div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
