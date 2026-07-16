import { Outlet } from "react-router-dom";
import { Header } from "@/components/layout/Header";

export function AppShell() {
  return (
    <div className="relative min-h-screen bg-background">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,hsl(var(--primary)/0.18),transparent)]"
      />
      <Header />
      <main className="mx-auto max-w-7xl px-4 pb-16 pt-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
