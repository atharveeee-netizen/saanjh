import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { ReplayProvider } from "./data/replay";
import { ToastProvider, TooltipProvider } from "./design/primitives";
import "./index.css";

// Routing is in memory (the hosted page cannot carry paths in its URL). A plain
// #token in the address chooses the starting screen, e.g. #events, #operator, #design.
const START: Record<string, string> = {
  overview: "/", events: "/events", forecast: "/forecast", households: "/households", reports: "/reports",
  fleet: "/fleet", settings: "/settings", design: "/design", blueprint: "/design/service-blueprint",
  operator: "/operator", messages: "/household/messages", status: "/household/status",
};
const token = window.location.hash.replace(/^#/, "");
const initial = START[token] ?? "/";

// Apply a remembered theme choice before first paint.
try {
  const t = localStorage.getItem("saanjh.theme");
  if (t === "dark" || t === "light") document.documentElement.setAttribute("data-theme", t);
} catch { /* storage unavailable */ }

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity, retry: 1, refetchOnWindowFocus: false } } });

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}>
      <TooltipProvider>
        <ToastProvider>
          <MemoryRouter initialEntries={[initial]}>
            <ReplayProvider>
              <App />
            </ReplayProvider>
          </MemoryRouter>
        </ToastProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
