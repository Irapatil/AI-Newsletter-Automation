import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Sparkles,
  Newspaper,
  History,
  HeartPulse,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/generate", label: "Generate Newsletter", icon: Sparkles },
  { to: "/newsletter", label: "Newsletter", icon: Newspaper },
  { to: "/history", label: "History", icon: History },
  { to: "/health", label: "Health", icon: HeartPulse },
] as const;

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground md:flex">
      <div className="flex h-16 items-center gap-2.5 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Bot className="h-[18px] w-[18px]" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">AI Newsletter</span>
          <span className="text-[11px] text-sidebar-foreground/60">Automation Console</span>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-white"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-white",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-sidebar-border px-4 py-4 text-[11px] text-sidebar-foreground/50">
        <p>LangGraph + FastAPI</p>
        <p>Enterprise Demo Build</p>
      </div>
    </aside>
  );
}
