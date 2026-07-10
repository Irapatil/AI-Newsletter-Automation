import { useLocation } from "react-router-dom";
import { Wifi, WifiOff } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useHealth } from "@/hooks/use-health";
import { cn } from "@/lib/utils";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Dashboard",
    subtitle: "Enterprise AI Newsletter Automation — system overview",
  },
  "/generate": {
    title: "Generate Newsletter",
    subtitle: "Trigger the LangGraph pipeline on demand",
  },
  "/newsletter": {
    title: "Newsletter",
    subtitle: "Latest generated edition",
  },
  "/history": {
    title: "History",
    subtitle: "Previously generated newsletters",
  },
  "/health": {
    title: "System Health",
    subtitle: "API and integration status",
  },
};

export function Header() {
  const location = useLocation();
  const page = PAGE_TITLES[location.pathname] ?? { title: "AI Newsletter Automation", subtitle: "" };
  const { health, error } = useHealth();
  const connected = Boolean(health) && !error;

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-md">
      <div>
        <h1 className="text-base font-semibold leading-none">{page.title}</h1>
        {page.subtitle && (
          <p className="mt-1 text-xs text-muted-foreground">{page.subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
            connected
              ? "border-success/30 bg-success/10 text-success"
              : "border-destructive/30 bg-destructive/10 text-destructive",
          )}
          title={connected ? "API reachable" : error?.message ?? "API unreachable"}
        >
          {connected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
          {connected ? "API Connected" : "API Offline"}
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
