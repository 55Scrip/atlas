import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import { ErrorBoundary } from "./ErrorBoundary";
import { Header } from "./Header";
import { LoadingBoundary } from "./LoadingBoundary";
import { Navigation } from "./Navigation";

export function AppShell() {
  return (
    <div>
      <Header />
      <Navigation />
      <main>
        <ErrorBoundary>
          <Suspense fallback={<LoadingBoundary />}>
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </main>
    </div>
  );
}
