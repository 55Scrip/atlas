import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Label, Link, Stack, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";

const ACCENT_LINK_STYLE = { color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" } as const;

/** Cross-Workspace Consistency Cleanup -- same uppercase small-caps
 * workspace-label treatment Portfolio's own `PAGE_TITLE_STYLE`
 * established, so every top-level workspace (Portfolio, Daily Brief,
 * Discovery, History) shares one page-title visual language. */
const PAGE_TITLE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.02em",
};

interface HoldingLite {
  ticker: string;
  caseId: string | null;
}

interface PortfolioView {
  exists: boolean;
  holdings: HoldingLite[];
}

type PortfolioStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; view: PortfolioView };

/** Visual Fidelity Pass -- "What Atlas Found" / "Watchlist Updates"
 * reuse the exact same real `/api/daily-brief` Change Intelligence
 * entries Daily Brief already renders (fetched independently, the
 * same "each page fetches the same real endpoint for itself" pattern
 * Portfolio/Daily Brief already use with `/api/alpha-portfolio*`) --
 * never a second, Discovery-specific computation of the same fact.
 * `MAX_FOUND_ENTRIES` is a display cap only, matching the approved
 * screen's own five-item list. */
interface DailyBriefEntryLite {
  caseId: string;
  ticker: string | null;
  headline: string;
  changeSummary: string;
}
interface DailyBriefViewLite {
  entries: DailyBriefEntryLite[];
}
type DailyBriefFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; brief: DailyBriefViewLite };

interface WatchlistEntryLite {
  ticker: string;
  caseId: string;
}
type WatchlistFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryLite[] };

const MAX_FOUND_ENTRIES = 5;

type ReviewCompanyStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "not-in-portfolio"; ticker: string }
  | { kind: "error"; message: string };

/**
 * Product correction: no workspace carries its own embedded Ask Atlas
 * / chat interface -- Atlas Companion will be the single, persistent,
 * cross-workspace conversational layer, built later. This page never
 * renders a chat input, transcript, send control, or suggested-prompt
 * chips. The real `POST /api/discovery/chat` endpoint
 * (`atlas/ai/api/router.py`) and its tool-calling logic are
 * deliberately left untouched on the backend -- this is a frontend
 * UI-surface removal only, preserving that capability for Atlas
 * Companion's future implementation. Discovery itself stays a real,
 * complete research page built from genuinely supported content: What
 * Atlas Found / Watchlist Updates (both reuse `/api/daily-brief`) and
 * Review a Company (bounded ticker lookup into a real Investment
 * Case) -- no placeholder stands in for the removed chat.
 */
export function DiscoveryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatus>({ kind: "loading" });
  const [dailyBrief, setDailyBrief] = useState<DailyBriefFetchStatus>({ kind: "loading" });
  const [watchlist, setWatchlist] = useState<WatchlistFetchStatus>({ kind: "loading" });
  const [reviewTicker, setReviewTicker] = useState("");
  const [reviewStatus, setReviewStatus] = useState<ReviewCompanyStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioView>;
      })
      .then((view) => setPortfolioStatus({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/daily-brief", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DailyBriefViewLite>;
      })
      .then((brief) => setDailyBrief({ kind: "loaded", brief }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDailyBrief({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-watchlist", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<WatchlistEntryLite[]>;
      })
      .then((entries) => setWatchlist({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setWatchlist({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  function openInvestmentCase(caseId: string) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "discovery" } });
  }

  function submitReviewCompany() {
    const ticker = reviewTicker.trim();
    if (ticker === "" || portfolioStatus.kind !== "loaded") return;

    const holding = portfolioStatus.view.holdings.find(
      (h) => h.ticker.toLowerCase() === ticker.toLowerCase(),
    );

    if (!holding) {
      setReviewStatus({ kind: "not-in-portfolio", ticker });
      return;
    }

    if (holding.caseId) {
      navigate(`/investment-case/${holding.caseId}`, { state: { origin: "discovery" } });
      return;
    }

    setReviewStatus({ kind: "submitting" });
    fetch("/api/cases", { method: "POST" })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<{ caseId: string }>;
      })
      .then((created) =>
        fetch(`/api/alpha-portfolio/holdings/${encodeURIComponent(holding.ticker)}/case-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidateCaseId: created.caseId }),
        }).then((linkResponse) => {
          if (!linkResponse.ok) throw new Error(`Backend responded with ${linkResponse.status}`);
          return linkResponse.json() as Promise<{ caseId: string }>;
        }),
      )
      .then((linked) => {
        navigate(`/investment-case/${linked.caseId}`, { state: { origin: "discovery" } });
      })
      .catch((error: unknown) => {
        setReviewStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  const reviewButtonLabel =
    portfolioStatus.kind === "loaded" &&
    portfolioStatus.view.holdings.some(
      (h) => h.ticker.toLowerCase() === reviewTicker.trim().toLowerCase() && h.caseId,
    )
      ? t("discovery.reviewCompany.openCase")
      : t("discovery.reviewCompany.createCase");

  // Visual Fidelity Pass -- "What Atlas Found" / "Watchlist Updates"
  // classify the same real `/api/daily-brief` entries Daily Brief
  // already renders, using the exact same Portfolio-takes-precedence
  // dedup rule Daily Brief's own module doc already establishes.
  const portfolioCaseIds = new Set(
    portfolioStatus.kind === "loaded"
      ? portfolioStatus.view.holdings.flatMap((holding) => (holding.caseId ? [holding.caseId] : []))
      : [],
  );
  const watchlistCaseIds = new Set(watchlist.kind === "loaded" ? watchlist.entries.map((entry) => entry.caseId) : []);
  const briefEntries = dailyBrief.kind === "loaded" ? dailyBrief.brief.entries : [];
  const foundEntries = briefEntries.slice(0, MAX_FOUND_ENTRIES);
  const watchlistEntries = briefEntries.filter(
    (entry) => !portfolioCaseIds.has(entry.caseId) && watchlistCaseIds.has(entry.caseId),
  );

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Heading level={3} style={PAGE_TITLE_STYLE}>
          {t("discovery.title")}
        </Heading>

        <Text color="secondary">{t("discovery.workingOnBehalf")}</Text>

        <Divider tone="hairline" />

        {/* What Atlas Found -- real Change Intelligence entries, the
            same data Daily Brief already surfaces (see derivation
            above). Never a Discovery-specific recomputation. */}
        <Stack gap="metadata">
          <Label>{t("discovery.whatFound.heading")}</Label>
          {dailyBrief.kind === "loaded" && foundEntries.length === 0 && (
            <Text color="tertiary">{t("discovery.whatFound.empty")}</Text>
          )}
          {foundEntries.map((entry) => (
            <DiscoveryFoundRow key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
          ))}
        </Stack>

        <Divider tone="hairline" />

        {/* Watchlist Updates -- same entries, Watchlist-only slice. */}
        <Stack gap="metadata">
          <Label>{t("discovery.watchlistUpdates.heading")}</Label>
          {dailyBrief.kind === "loaded" && watchlist.kind === "loaded" && watchlistEntries.length === 0 && (
            <Text color="tertiary">{t("discovery.watchlistUpdates.empty")}</Text>
          )}
          {watchlistEntries.map((entry) => (
            <DiscoveryFoundRow key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
          ))}
        </Stack>

        <Divider tone="hairline" />

        {/* Review a company -- the only bounded, non-conversational path
            to a real Investment Case from this page. No entity
            recognition: the ticker is matched by exact, case-insensitive
            string equality against the investor's own real holdings,
            never parsed out of the conversation above. */}
        <Stack gap="metadata">
          <Label>{t("discovery.reviewCompany.heading")}</Label>
          <Inline gap="row" align="center">
            <input
              value={reviewTicker}
              placeholder={t("form.ticker")}
              onChange={(event) => {
                setReviewTicker(event.target.value);
                setReviewStatus({ kind: "idle" });
              }}
            />
            <Button
              variant="tertiary"
              onClick={submitReviewCompany}
              disabled={reviewStatus.kind === "submitting" || reviewTicker.trim() === ""}
            >
              {reviewStatus.kind === "submitting" ? t("common.submitting") : reviewButtonLabel}
            </Button>
          </Inline>
          {reviewStatus.kind === "not-in-portfolio" && (
            <Inline gap="row" align="baseline">
              <Text color="tertiary">
                {t("discovery.reviewCompany.notInPortfolio", { ticker: reviewStatus.ticker })}
              </Text>
              <Link
                href="#"
                style={ACCENT_LINK_STYLE}
                onClick={(event) => {
                  event.preventDefault();
                  navigate("/portfolio");
                }}
              >
                {t("dashboard.portfolioStatus.goToPortfolio")}
              </Link>
            </Inline>
          )}
          {reviewStatus.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("discovery.reviewCompany.error", { message: reviewStatus.message })}
            </Text>
          )}
        </Stack>
      </Stack>
    </Container>
  );
}

/** Visual Fidelity Pass -- one dense row per real Change Intelligence
 * entry (ticker + first change line + arrow), shared by "What Atlas
 * Found" and "Watchlist Updates". */
function DiscoveryFoundRow({
  entry,
  onOpen,
  t,
}: {
  entry: DailyBriefEntryLite;
  onOpen: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const firstChangeLine = entry.changeSummary.split("\n")[0] ?? entry.headline;
  return (
    <Link
      href="#"
      style={{ ...ACCENT_LINK_STYLE, color: "var(--color-text-primary)", display: "block" }}
      onClick={(event) => {
        event.preventDefault();
        onOpen();
      }}
    >
      <Inline gap="row" align="baseline" style={{ justifyContent: "space-between" }}>
        <Text as="span">
          <Text as="span" color="secondary">
            {entry.ticker ?? t("dailyBrief.entry.unknownCompany")} —{" "}
          </Text>
          {firstChangeLine}
        </Text>
        <Text as="span" color="tertiary">
          →
        </Text>
      </Inline>
    </Link>
  );
}
