import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LanguageProvider } from "../i18n";
import { Navigation } from "./Navigation";

function renderNav(route = "/daily-brief") {
  render(
    <MemoryRouter initialEntries={[route]}>
      <LanguageProvider>
        <Navigation />
      </LanguageProvider>
    </MemoryRouter>,
  );
}

/**
 * Final Pre-Alpha Convergence. Primary navigation is a product
 * statement, not a list of pages that exist: it names exactly the four
 * surfaces Atlas has accepted as primary, in the order an investor
 * moves through them. A route may stay reachable without being a
 * primary destination -- `/history`, `/platform-status` and the
 * decision workspace all are.
 */
describe("primary navigation", () => {
  it("exposes exactly the four accepted primary surfaces", () => {
    renderNav();
    expect(screen.getAllByRole("link")).toHaveLength(4);
  });

  it("orders them Daily Brief, Portfolio, Watchlist, Discovery", () => {
    renderNav();
    expect(screen.getAllByRole("link").map((a) => a.getAttribute("href"))).toEqual([
      "/daily-brief",
      "/portfolio",
      "/watchlist",
      "/discovery",
    ]);
  });

  /** Discovery is exploratory. It sat second, ahead of the portfolio
   * the investor actually owns. */
  it("never places Discovery ahead of Portfolio or Watchlist", () => {
    renderNav();
    const hrefs = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    expect(hrefs.indexOf("/discovery")).toBeGreaterThan(hrefs.indexOf("/portfolio"));
    expect(hrefs.indexOf("/discovery")).toBeGreaterThan(hrefs.indexOf("/watchlist"));
  });

  /** Atlas UX Freeze v1 removed History from the nav tier; the route
   * itself stays reachable. Nothing may quietly promote a fifth
   * destination back alongside the four. */
  it("promotes no fifth destination -- no History, Dashboard, Home or Profile tab", () => {
    renderNav();
    for (const gone of ["/history", "/", "/dashboard", "/profile", "/platform-status", "/discovery/candidate"]) {
      expect(screen.queryByRole("link", { name: new RegExp(`^${gone}$`) })).not.toBeInTheDocument();
    }
    const hrefs = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    expect(hrefs).not.toContain("/history");
  });

  it("names each surface with its one canonical label", () => {
    renderNav();
    expect(screen.getAllByRole("link").map((a) => a.textContent)).toEqual([
      "Dagens genomgång",
      "Portfölj",
      "Bevakningslista",
      "Discovery",
    ]);
  });

  it("marks the surface the investor is on as the active one, and only that one", () => {
    renderNav("/portfolio");
    const active = screen.getAllByRole("link").filter((a) => (a.className ?? "").includes("active"));
    expect(active).toHaveLength(1);
    expect(active[0]).toHaveAttribute("href", "/portfolio");
  });

  it("keeps every destination reachable as a real link, operable without a pointer", () => {
    renderNav();
    for (const link of screen.getAllByRole("link")) {
      expect(link.tagName).toBe("A");
      expect(link).toHaveAttribute("href");
    }
  });
});
