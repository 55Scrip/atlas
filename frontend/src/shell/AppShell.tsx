import { Suspense, useState } from "react";
import { Outlet } from "react-router-dom";
import { CompanionPanel, readPersistedExpanded } from "../companion/CompanionPanel";
import { ErrorBoundary } from "./ErrorBoundary";
import { Header } from "./Header";
import { LoadingBoundary } from "./LoadingBoundary";
import { Navigation } from "./Navigation";

export function AppShell() {
  // Lifted here (rather than left as CompanionPanel's own local state) so
  // <main> can reserve horizontal space while the panel is expanded --
  // the smallest fix for the panel covering workspace content (tall
  // Holdings/Atlas View/Decision Reviews tables) without touching any of
  // the five workspace layouts individually.
  const [companionExpanded, setCompanionExpanded] = useState<boolean>(readPersistedExpanded);

  return (
    <div style={{ minHeight: "100vh" }}>
      <Header />
      <Navigation />
      <main
        style={{
          paddingTop: "var(--space-inter-section)",
          paddingBottom: "var(--space-inter-section)",
          // A genuine `width` constraint, not padding: several workspace
          // tables (Holdings, Atlas View, Decision Reviews) size to their
          // own content and refuse to shrink to fit a padded content box
          // -- they simply paint through padding as if it weren't there.
          // An explicit width gives <main> a real boundary, so overflow-x
          // below actually clips/scrolls that content within the
          // reserved area instead of letting it spill under the panel.
          width: companionExpanded ? "calc(100% - var(--global-companion-reserved-width))" : "100%",
          overflowX: "auto",
          transition: "width var(--motion-duration-brief) var(--motion-easing-out)",
        }}
      >
        <ErrorBoundary>
          <Suspense fallback={<LoadingBoundary />}>
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </main>
      {/* Mounted here, outside the per-route <Outlet/>, so Atlas
          Companion persists across every workspace navigation instead of
          remounting -- see frontend/src/companion/CompanionPanel.tsx. */}
      <CompanionPanel expanded={companionExpanded} onExpandedChange={setCompanionExpanded} />
    </div>
  );
}
