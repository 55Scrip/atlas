import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import { CompanionPanel } from "../companion/CompanionPanel";
import { ErrorBoundary } from "./ErrorBoundary";
import { Header } from "./Header";
import { LoadingBoundary } from "./LoadingBoundary";
import { Navigation } from "./Navigation";

export function AppShell() {
  return (
    <div style={{ minHeight: "100vh" }}>
      <Header />
      <Navigation />
      <main style={{ padding: "var(--space-inter-section) 0" }}>
        <ErrorBoundary>
          <Suspense fallback={<LoadingBoundary />}>
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </main>
      {/* Mounted here, outside the per-route <Outlet/>, so Atlas
          Companion persists across every workspace navigation instead of
          remounting -- see frontend/src/companion/CompanionPanel.tsx. */}
      <CompanionPanel />
    </div>
  );
}
