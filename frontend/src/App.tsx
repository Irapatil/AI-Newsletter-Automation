import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AppShell } from "@/components/layout/AppShell";
import { ThemeProvider } from "@/hooks/use-theme";
import { NewsletterProvider } from "@/hooks/use-newsletter";
import { TooltipProvider } from "@/components/ui/tooltip";
import { DashboardPage } from "@/pages/DashboardPage";
import { GeneratePage } from "@/pages/GeneratePage";
import { NewsletterPage } from "@/pages/NewsletterPage";
import { HistoryPage } from "@/pages/HistoryPage";
import { HealthPage } from "@/pages/HealthPage";

export default function App() {
  return (
    <ThemeProvider>
      <TooltipProvider delayDuration={200}>
        <NewsletterProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<AppShell />}>
                <Route index element={<DashboardPage />} />
                <Route path="generate" element={<GeneratePage />} />
                <Route path="newsletter" element={<NewsletterPage />} />
                <Route path="history" element={<HistoryPage />} />
                <Route path="health" element={<HealthPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
          <Toaster position="top-right" richColors closeButton />
        </NewsletterProvider>
      </TooltipProvider>
    </ThemeProvider>
  );
}
