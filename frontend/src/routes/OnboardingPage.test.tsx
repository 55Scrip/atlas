import { afterEach } from "vitest";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { OnboardingPage } from "./OnboardingPage";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

function emptyPortfolioView() {
  return { exists: false };
}

function existingPortfolioView() {
  return { exists: true, holdings: [{ ticker: "AMD", weightPercent: 100 }] };
}

function mockFetch(handlers: Record<string, () => unknown>) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      for (const [pattern, handler] of Object.entries(handlers)) {
        if (url.includes(pattern)) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(handler()) } as Response);
        }
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("OnboardingPage (Zero-Effort Portfolio Onboarding)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  it("shows all five entry options", async () => {
    mockFetch({ "/api/alpha-portfolio": emptyPortfolioView });
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });
    expect(await screen.findByText("Importera från Avanza")).toBeInTheDocument();
    expect(screen.getByText("Importera från Nordnet")).toBeInTheDocument();
    expect(screen.getByText("Klistra in portfölj")).toBeInTheDocument();
    expect(screen.getByText("Ladda upp fil")).toBeInTheDocument();
    expect(screen.getByText("Ange innehav manuellt")).toBeInTheDocument();
  });

  it("a fully-resolved paste skips review and lands on the progress screen", async () => {
    mockFetch({
      "/api/alpha-portfolio/import/preview": () => ({
        rows: [
          {
            lineNumber: 1,
            raw: "AMD;100",
            originalName: "AMD",
            ticker: "AMD",
            quantity: null,
            price: null,
            valueAbsolute: null,
            weightPercent: 100,
            currency: null,
            status: "RESOLVED",
            message: null,
            candidates: [],
            alreadyHeld: false,
          },
        ],
        headerDetected: false,
        holdingsFound: 1,
        resolvedCount: 1,
        needsReview: false,
        currencyConflict: false,
      }),
      "/api/alpha-portfolio/import": () => ({ exists: true, batchId: "batch-1" }),
      "/api/enrichment-progress/batch-1": () => ({
        exists: true,
        total: 1,
        doneCount: 1,
        currentlyAnalyzing: null,
        complete: true,
      }),
      "/api/alpha-portfolio": emptyPortfolioView,
    });
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "AMD;100" } });
    fireEvent.click(screen.getByText("Fortsätt"));

    expect(await screen.findByText("Atlas bygger din investeringsarbetsyta.")).toBeInTheDocument();
    expect(screen.getByText("Du kan börja använda Atlas nu.")).toBeInTheDocument();
  });

  it("a genuinely ambiguous row blocks import until resolved", async () => {
    mockFetch({
      "/api/alpha-portfolio/import/preview": () => ({
        rows: [
          {
            lineNumber: 1,
            raw: "Berkshire Hathaway;100",
            originalName: "Berkshire Hathaway",
            ticker: null,
            quantity: null,
            price: null,
            valueAbsolute: null,
            weightPercent: 100,
            currency: null,
            status: "AMBIGUOUS",
            message: "Atlas found more than one match.",
            candidates: [
              { ticker: "BRK.A", displayName: "Berkshire Hathaway Class A" },
              { ticker: "BRK.B", displayName: "Berkshire Hathaway Class B" },
            ],
            alreadyHeld: false,
          },
        ],
        headerDetected: false,
        holdingsFound: 1,
        resolvedCount: 0,
        needsReview: true,
        currencyConflict: false,
      }),
      "/api/alpha-portfolio/import": () => ({ exists: true, batchId: "batch-2" }),
      "/api/enrichment-progress/batch-2": () => ({
        exists: true,
        total: 1,
        doneCount: 1,
        currentlyAnalyzing: null,
        complete: true,
      }),
      "/api/alpha-portfolio": emptyPortfolioView,
    });
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Berkshire Hathaway;100" },
    });
    fireEvent.click(screen.getByText("Fortsätt"));

    expect(await screen.findByText("Vilket bolag menade du?")).toBeInTheDocument();
    const importButton = screen.getByText("Importera portfölj");
    expect(importButton).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/Berkshire Hathaway Class B/));
    await waitFor(() => expect(importButton).not.toBeDisabled());

    fireEvent.click(importButton);
    expect(await screen.findByText("Atlas bygger din investeringsarbetsyta.")).toBeInTheDocument();
  });

  it("a known-unsupported holding (e.g. a private company) never blocks the rest of the import", async () => {
    mockFetch({
      "/api/alpha-portfolio/import/preview": () => ({
        rows: [
          {
            lineNumber: 1,
            raw: "AMD;60000 kr",
            originalName: "AMD",
            ticker: "AMD",
            quantity: null,
            price: null,
            valueAbsolute: 60000,
            weightPercent: null,
            currency: "SEK",
            status: "RESOLVED",
            message: null,
            instrumentType: null,
            candidates: [],
            alreadyHeld: false,
          },
          {
            lineNumber: 2,
            raw: "SpaceX;16000 kr",
            originalName: "SpaceX",
            ticker: null,
            quantity: null,
            price: null,
            valueAbsolute: 16000,
            weightPercent: null,
            currency: "SEK",
            status: "UNSUPPORTED",
            message: "'SpaceX' is a recognized private, not a supported equity holding.",
            instrumentType: "private",
            candidates: [],
            alreadyHeld: false,
          },
        ],
        headerDetected: false,
        holdingsFound: 2,
        resolvedCount: 1,
        needsReview: true,
        currencyConflict: false,
      }),
      "/api/alpha-portfolio/import": () => ({ exists: true, batchId: "batch-3" }),
      "/api/enrichment-progress/batch-3": () => ({
        exists: true,
        total: 1,
        doneCount: 1,
        currentlyAnalyzing: null,
        complete: true,
      }),
      "/api/alpha-portfolio": emptyPortfolioView,
    });
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "AMD;60000 kr\nSpaceX;16000 kr" } });
    fireEvent.click(screen.getByText("Fortsätt"));

    // The reason is shown, in Atlas's own words -- never a raw ticker
    // input for something that can never become tradeable.
    expect(await screen.findByText(/SpaceX.*private/)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Ticker")).not.toBeInTheDocument();

    // Import proceeds -- one unusual holding never holds the rest hostage.
    const importButton = screen.getByText("Importera portfölj");
    expect(importButton).not.toBeDisabled();
    fireEvent.click(importButton);
    expect(await screen.findByText("Atlas bygger din investeringsarbetsyta.")).toBeInTheDocument();
  });

  it("import proceeds with an unresolved row left behind, and says so", async () => {
    mockFetch({
      "/api/alpha-portfolio/import/preview": () => ({
        rows: [
          {
            lineNumber: 1,
            raw: "AMD;60000 kr",
            originalName: "AMD",
            ticker: "AMD",
            quantity: null,
            price: null,
            valueAbsolute: 60000,
            weightPercent: null,
            currency: "SEK",
            status: "RESOLVED",
            message: null,
            instrumentType: null,
            candidates: [],
            alreadyHeld: false,
          },
          {
            lineNumber: 2,
            raw: "Unknown Co;16000 kr",
            originalName: "Unknown Co",
            ticker: null,
            quantity: null,
            price: null,
            valueAbsolute: 16000,
            weightPercent: null,
            currency: "SEK",
            status: "UNRESOLVED",
            message: "Atlas couldn't identify 'Unknown Co'.",
            instrumentType: null,
            candidates: [],
            alreadyHeld: false,
          },
        ],
        headerDetected: false,
        holdingsFound: 2,
        resolvedCount: 1,
        needsReview: true,
        currencyConflict: false,
      }),
      "/api/alpha-portfolio/import": () => ({ exists: true, batchId: "batch-4" }),
      "/api/enrichment-progress/batch-4": () => ({
        exists: true,
        total: 1,
        doneCount: 1,
        currentlyAnalyzing: null,
        complete: true,
      }),
      "/api/alpha-portfolio": emptyPortfolioView,
    });
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "AMD;60000 kr\nUnknown Co;16000 kr" } });
    fireEvent.click(screen.getByText("Fortsätt"));

    const importButton = await screen.findByText("Importera portfölj");
    expect(importButton).not.toBeDisabled();
    expect(screen.getByText(/1 innehav du inte löst/)).toBeInTheDocument();

    fireEvent.click(importButton);
    expect(await screen.findByText("Atlas bygger din investeringsarbetsyta.")).toBeInTheDocument();
  });

  it("a failed confirm never shows raw backend text, only a translated message", async () => {
    const rawBackendDetail =
      "Holding 'AMD' has neither a weight percentage nor enough data to determine its size.";
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/alpha-portfolio/import/preview")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                rows: [
                  {
                    lineNumber: 1,
                    raw: "AMD;100",
                    originalName: "AMD",
                    ticker: "AMD",
                    quantity: null,
                    price: null,
                    valueAbsolute: null,
                    weightPercent: 100,
                    currency: null,
                    status: "RESOLVED",
                    message: null,
                    instrumentType: null,
                    candidates: [],
                    alreadyHeld: false,
                  },
                ],
                headerDetected: false,
                holdingsFound: 1,
                resolvedCount: 1,
                needsReview: false,
                currencyConflict: false,
              }),
          } as Response);
        }
        if (url.includes("/api/alpha-portfolio/import")) {
          return Promise.resolve({
            ok: false,
            status: 400,
            json: () => Promise.resolve({ detail: rawBackendDetail }),
          } as Response);
        }
        if (url.includes("/api/alpha-portfolio")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(emptyPortfolioView()) } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "AMD;100" } });
    fireEvent.click(screen.getByText("Fortsätt"));

    expect(
      await screen.findByText("Atlas kunde inte slutföra importen just nu. Försök igen."),
    ).toBeInTheDocument();
    expect(screen.queryByText(rawBackendDetail, { exact: false })).not.toBeInTheDocument();
    expect(consoleErrorSpy).toHaveBeenCalledWith("Atlas backend error:", rawBackendDetail);
    consoleErrorSpy.mockRestore();
  });

  it("manual entry builds a synthetic Company,Quantity,Price submission", async () => {
    let capturedPreviewBody: string | null = null;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/alpha-portfolio/import/preview")) {
          capturedPreviewBody = init?.body as string;
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                rows: [],
                headerDetected: true,
                holdingsFound: 0,
                resolvedCount: 0,
                needsReview: false,
                currencyConflict: false,
              }),
          } as Response);
        }
        if (url.includes("/api/alpha-portfolio")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(emptyPortfolioView()) } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Ange innehav manuellt"));
    fireEvent.change(screen.getByLabelText("Bolag"), { target: { value: "Microsoft" } });
    fireEvent.change(screen.getByLabelText("Antal"), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Pris"), { target: { value: "400" } });
    fireEvent.click(screen.getByText("Fortsätt", { selector: "button" }));

    await waitFor(() => expect(capturedPreviewBody).not.toBeNull());
    const parsed = JSON.parse(capturedPreviewBody as unknown as string) as { rawText: string };
    expect(parsed.rawText).toBe("Company,Quantity,Price\nMicrosoft,10,400");
  });

  it("'I don't have a portfolio yet' skips straight to objective/horizon", async () => {
    let fromScratchCalled = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/alpha-portfolio/from-scratch")) {
          fromScratchCalled = true;
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true }) } as Response);
        }
        if (url.includes("/api/alpha-portfolio")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(emptyPortfolioView()) } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Ange innehav manuellt"));
    fireEvent.click(screen.getByText("Jag har ingen portfölj än"));
    expect(await screen.findByText("Börja från grunden")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Investeringsmål"), { target: { value: "Growth" } });
    fireEvent.change(screen.getByLabelText("Investeringshorisont"), { target: { value: "Long" } });
    fireEvent.click(screen.getByText("Fortsätt till portföljen"));

    await waitFor(() => expect(fromScratchCalled).toBe(true));
  });

  it("a SUGGESTED row is accepted by default, imports directly, and is remembered", async () => {
    let capturedResolutionsBody: string | null = null;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/alpha-portfolio/import/preview")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                rows: [
                  {
                    lineNumber: 1,
                    raw: "Taiwan Semicond Manufacturing;100",
                    originalName: "Taiwan Semicond Manufacturing",
                    ticker: "TSM",
                    quantity: null,
                    price: null,
                    valueAbsolute: null,
                    weightPercent: 100,
                    currency: null,
                    status: "SUGGESTED",
                    message: "Atlas believes this is Taiwan Semiconductor Manufacturing (TSM).",
                    instrumentType: null,
                    candidates: [{ ticker: "TSM", displayName: "Taiwan Semiconductor Manufacturing" }],
                    alreadyHeld: false,
                  },
                ],
                headerDetected: false,
                holdingsFound: 1,
                resolvedCount: 0,
                needsReview: true,
                currencyConflict: false,
              }),
          } as Response);
        }
        if (url.includes("/api/alpha-portfolio/import/resolutions")) {
          capturedResolutionsBody = init?.body as string;
          return Promise.resolve({ ok: true, json: () => Promise.resolve(null) } as Response);
        }
        if (url.includes("/api/enrichment-progress/batch-5")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({ exists: true, total: 1, doneCount: 1, currentlyAnalyzing: null, complete: true }),
          } as Response);
        }
        if (url.includes("/api/alpha-portfolio/import")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ exists: true, batchId: "batch-5" }),
          } as Response);
        }
        if (url.includes("/api/alpha-portfolio")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(emptyPortfolioView()) } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Taiwan Semicond Manufacturing;100" },
    });
    fireEvent.click(screen.getByText("Fortsätt"));

    expect(
      await screen.findByText("Atlas tror att det här är Taiwan Semiconductor Manufacturing (TSM). Stämmer det?"),
    ).toBeInTheDocument();
    const importButton = screen.getByText("Importera portfölj");
    expect(importButton).not.toBeDisabled();

    fireEvent.click(importButton);
    expect(await screen.findByText("Atlas bygger din investeringsarbetsyta.")).toBeInTheDocument();

    await waitFor(() => expect(capturedResolutionsBody).not.toBeNull());
    const parsed = JSON.parse(capturedResolutionsBody as unknown as string) as {
      resolutions: { originalName: string; ticker: string }[];
    };
    expect(parsed.resolutions).toEqual([{ originalName: "Taiwan Semicond Manufacturing", ticker: "TSM" }]);
  });

  it("rejecting a SUGGESTED row requires a manual ticker before it counts as resolved", async () => {
    mockFetch({
      "/api/alpha-portfolio/import/preview": () => ({
        rows: [
          {
            lineNumber: 1,
            raw: "Taiwan Semicond Manufacturing;100",
            originalName: "Taiwan Semicond Manufacturing",
            ticker: "TSM",
            quantity: null,
            price: null,
            valueAbsolute: null,
            weightPercent: 100,
            currency: null,
            status: "SUGGESTED",
            message: "Atlas believes this is Taiwan Semiconductor Manufacturing (TSM).",
            instrumentType: null,
            candidates: [{ ticker: "TSM", displayName: "Taiwan Semiconductor Manufacturing" }],
            alreadyHeld: false,
          },
        ],
        headerDetected: false,
        holdingsFound: 1,
        resolvedCount: 0,
        needsReview: true,
        currencyConflict: false,
      }),
      "/api/alpha-portfolio": emptyPortfolioView,
    });
    renderWithProviders(<OnboardingPage />, { route: "/welcome" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Taiwan Semicond Manufacturing;100" },
    });
    fireEvent.click(screen.getByText("Fortsätt"));

    await screen.findByText("Atlas tror att det här är Taiwan Semiconductor Manufacturing (TSM). Stämmer det?");
    const importButton = screen.getByText("Importera portfölj");
    expect(importButton).not.toBeDisabled();

    fireEvent.click(screen.getByLabelText("Nej, jag anger det själv"));
    expect(importButton).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText("Ticker"), { target: { value: "TSMX" } });
    await waitFor(() => expect(importButton).not.toBeDisabled());
  });

  it("shows a replace warning when a portfolio already exists", async () => {
    mockFetch({
      "/api/alpha-portfolio/import/preview": () => ({
        rows: [
          {
            lineNumber: 1,
            raw: "Unknown Co;100",
            originalName: "Unknown Co",
            ticker: null,
            quantity: null,
            price: null,
            valueAbsolute: null,
            weightPercent: 100,
            currency: null,
            status: "UNRESOLVED",
            message: "Atlas couldn't identify it.",
            candidates: [],
            alreadyHeld: false,
          },
        ],
        headerDetected: false,
        holdingsFound: 1,
        resolvedCount: 0,
        needsReview: true,
        currencyConflict: false,
      }),
      "/api/alpha-portfolio": existingPortfolioView,
    });
    renderWithProviders(<OnboardingPage />, { route: "/portfolio/import" });

    fireEvent.click(await screen.findByText("Klistra in portfölj"));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Unknown Co;100" },
    });
    fireEvent.click(screen.getByText("Fortsätt"));

    expect(await screen.findByText("Det här ersätter de innehav som just nu visas i Atlas.")).toBeInTheDocument();
  });
});
