import { useState } from "react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Link } from "react-router-dom";
import { LanguageProvider } from "../i18n";
import { CompanionPanel } from "./CompanionPanel";
import * as companionApi from "./companionApi";
import { __resetAlphaWatchlistCacheForTests } from "../discovery/watchlistActions";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

// `LanguageContext.tsx`'s own `DEFAULT_LANGUAGE` is `"sv"` -- every
// assertion below uses the real Swedish copy, matching every other test
// in this repository that renders through `LanguageProvider`
// (`DecisionWorkspacePage.test.tsx`, `CaseConditionsSection.test.tsx`).

vi.mock("./companionApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./companionApi")>();
  return { ...actual, sendCompanionChat: vi.fn() };
});

const PORTFOLIO_RESPONSE = {
  holdings: [{ ticker: "AAPL", caseId: "case-aapl" }],
};
const WATCHLIST_RESPONSE = [{ ticker: "TSLA", caseId: "case-tsla" }];

function mockFetchOnce() {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(PORTFOLIO_RESPONSE) } as Response);
      }
      if (url.includes("/api/alpha-watchlist")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(WATCHLIST_RESPONSE) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

/** Mirrors how `AppShell` mounts Companion: once, as a sibling of the
 * routed content, so it never remounts on navigation. `links` renders one
 * real `<Link>` per route under test so tests can navigate without
 * touching browser APIs. */
function TestShell({ initialRoute, links }: { initialRoute: string; links: { to: string; label: string }[] }) {
  const [expanded, setExpanded] = useState(true);
  return (
    <MemoryRouter initialEntries={[initialRoute]}>
      <LanguageProvider>
        <nav>
          {links.map((link) => (
            <Link key={link.to} to={link.to}>
              {link.label}
            </Link>
          ))}
        </nav>
        <CompanionPanel expanded={expanded} onExpandedChange={setExpanded} />
      </LanguageProvider>
    </MemoryRouter>
  );
}

async function sendMessage(text: string) {
  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText("Meddela Atlas…"), text);
  await user.click(screen.getByRole("button", { name: "Skicka" }));
}

describe("CompanionPanel -- Sprint 3 coverage completion", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    mockFetchOnce();
    vi.mocked(companionApi.sendCompanionChat).mockResolvedValue({ message: "ok", mode: "generated", toolResult: null });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
    __resetAlphaWatchlistCacheForTests();
  });

  it("renders nothing on an unsupported route (Platform Status)", () => {
    render(<TestShell initialRoute="/platform-status" links={[]} />);
    expect(screen.queryByRole("button", { name: /Atlas/ })).not.toBeInTheDocument();
  });

  it("renders the toggle and, once expanded, the Portfolio-wide context strip on the bare Portfolio route", async () => {
    render(<TestShell initialRoute="/portfolio" links={[]} />);
    await waitFor(() => expect(screen.getByText("Portföljövergripande")).toBeInTheDocument());
  });

  it("shows the ticker in the context strip immediately on a Portfolio Holding route, without waiting for the holdings fetch", () => {
    render(<TestShell initialRoute="/portfolio/holding/AAPL" links={[]} />);
    expect(screen.getByText("Diskuterar: AAPL")).toBeInTheDocument();
  });

  it("shows the ticker in the context strip immediately on a Company route", () => {
    render(<TestShell initialRoute="/company/AAPL" links={[]} />);
    expect(screen.getByText("Diskuterar: AAPL")).toBeInTheDocument();
  });

  it("shows Portfolio-wide on a bare Watchlist route with nothing selected", async () => {
    render(<TestShell initialRoute="/watchlist" links={[]} />);
    await waitFor(() => expect(screen.getByText("Portföljövergripande")).toBeInTheDocument());
  });

  it("does not announce the very first context, even after navigating before any message is sent", async () => {
    render(<TestShell initialRoute="/portfolio" links={[{ to: "/company/AAPL", label: "go-company" }]} />);
    await waitFor(() => expect(screen.getByText("Portföljövergripande")).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByText("go-company"));

    await waitFor(() => expect(screen.getByText("Diskuterar: AAPL")).toBeInTheDocument());
    expect(screen.queryByText(/Kontext ändrad/)).not.toBeInTheDocument();
  });

  it("announces exactly one context change (ticker resolved to its Case) when navigating from a bare workspace into a Company page after a message has been sent", async () => {
    render(<TestShell initialRoute="/portfolio" links={[{ to: "/company/AAPL", label: "go-company" }]} />);
    await waitFor(() => expect(screen.getByText("Portföljövergripande")).toBeInTheDocument());

    await sendMessage("Hello");
    await waitFor(() =>
      expect(companionApi.sendCompanionChat).toHaveBeenCalledWith([{ role: "user", content: "Hello" }], "sv", null),
    );

    const user = userEvent.setup();
    await user.click(screen.getByText("go-company"));

    await waitFor(() =>
      expect(screen.getByText("Kontext ändrad: Portföljövergripande → AAPL")).toBeInTheDocument(),
    );
    expect(screen.getAllByText(/Kontext ändrad/)).toHaveLength(1);
  });

  it("does not announce again when navigating from a Company page to the Investment Case for the same underlying Case", async () => {
    render(
      <TestShell initialRoute="/company/AAPL" links={[{ to: "/investment-case/case-aapl", label: "go-investment-case" }]} />,
    );
    await waitFor(() => expect(screen.getByText("Diskuterar: AAPL")).toBeInTheDocument());

    await sendMessage("Hello");
    await waitFor(() =>
      expect(companionApi.sendCompanionChat).toHaveBeenCalledWith([{ role: "user", content: "Hello" }], "sv", "case-aapl"),
    );

    const user = userEvent.setup();
    await user.click(screen.getByText("go-investment-case"));

    await waitFor(() => expect(screen.getByText("Diskuterar: AAPL")).toBeInTheDocument());
    expect(screen.queryByText(/Kontext ändrad/)).not.toBeInTheDocument();
  });

  it("resolves a Company route's caseId from the Watchlist when the ticker is not held", async () => {
    render(<TestShell initialRoute="/company/TSLA" links={[]} />);
    await sendMessage("Hello");
    await waitFor(() =>
      expect(companionApi.sendCompanionChat).toHaveBeenCalledWith([{ role: "user", content: "Hello" }], "sv", "case-tsla"),
    );
  });

  it("persists the transcript across navigation between supported routes without duplicating messages", async () => {
    render(
      <TestShell
        initialRoute="/portfolio"
        links={[
          { to: "/watchlist", label: "go-watchlist" },
          { to: "/daily-brief", label: "go-daily-brief" },
        ]}
      />,
    );
    await sendMessage("First message");
    await waitFor(() => expect(screen.getByText("First message")).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByText("go-watchlist"));
    expect(screen.getByText("First message")).toBeInTheDocument();

    await user.click(screen.getByText("go-daily-brief"));
    expect(screen.getByText("First message")).toBeInTheDocument();
    expect(screen.getAllByText("First message")).toHaveLength(1);
  });

  it("restores a persisted transcript from sessionStorage on a fresh mount (simulating a page refresh)", async () => {
    const { unmount } = render(<TestShell initialRoute="/portfolio" links={[]} />);
    await sendMessage("Survives a refresh");
    await waitFor(() => expect(screen.getByText("Survives a refresh")).toBeInTheDocument());
    unmount();

    render(<TestShell initialRoute="/portfolio" links={[]} />);
    expect(screen.getByText("Survives a refresh")).toBeInTheDocument();
  });

  it("collapses on toggle click and re-expands, consistently across a ticker-bearing route", async () => {
    render(<TestShell initialRoute="/portfolio/holding/AAPL" links={[]} />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Stäng Atlas" }));
    expect(screen.queryByText("Diskuterar: AAPL")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Öppna Atlas" }));
    expect(screen.getByText("Diskuterar: AAPL")).toBeInTheDocument();
  });
});
