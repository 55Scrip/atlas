import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Container, Divider, Heading, Inline, Label, Link, Stack, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { derivePortfolioActions, type AttentionCategory, type PortfolioAction } from "../portfolio/derivePortfolioActions";
import { describePortfolioAction, SEVERITY_EMOJI } from "../portfolio/describePortfolioAction";

/** Visual Fidelity Pass -- matches Portfolio/Investment Case's own
 * accent link treatment. */
const ACCENT_LINK_STYLE = { color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" } as const;

/** Cross-Workspace Consistency Cleanup -- same uppercase small-caps
 * workspace-label treatment Portfolio's own `PAGE_TITLE_STYLE`
 * established, so every top-level workspace (Portfolio, Daily Brief,
 * Discovery, History) shares one page-title visual language. Investment
 * Case is a detail page, not a workspace, and keeps its own distinct
 * company-name heading. */
const PAGE_TITLE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.02em",
};

interface ChangeFindingView {
  id: string;
  category: string;
  direction: "positive" | "negative" | "neutral";
  previousState: string;
  currentState: string;
}

interface DailyBriefEntryView {
  caseId: string;
  ticker: string | null;
  headline: string;
  changeSummary: string;
  whyItMatters: string;
  thesisImpact: string;
  changes: ChangeFindingView[];
}

interface DailyBriefView {
  generatedAt: string;
  summary: string;
  entries: DailyBriefEntryView[];
}

type DailyBriefStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; brief: DailyBriefView };

/**
 * Which Cases belong to the Portfolio vs. the Watchlist (Workspace
 * Migration Phase 4) — fetched independently from `/api/daily-brief`
 * itself, purely to classify each already-real `DailyBriefEntryView`
 * into "Portfolio Changes" / "Watchlist Updates" for the approved
 * Figma hierarchy. A failure here never blocks the entry list from
 * rendering; it only means entries can't yet be grouped (see
 * `portfolioChangeEntries`/`watchlistChangeEntries` below), the same
 * "independent fetch, section quietly degrades" pattern Portfolio's own
 * Status/Intelligence/Cockpit fetches already use.
 */
interface PortfolioHoldingLite {
  ticker: string;
  caseId: string | null;
}
interface PortfolioMembershipView {
  exists: boolean;
  holdings: PortfolioHoldingLite[];
}
type PortfolioMembershipStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; view: PortfolioMembershipView };

interface WatchlistEntryView {
  ticker: string;
  caseId: string;
  addedAt: string;
}
type WatchlistStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryView[] };

/**
 * "Today's Priorities" (Migration Review §10 item 5) reuses Portfolio's
 * own real Action Center data verbatim -- the same `reviewQueue`/
 * `attentionItems`/`missingEvidence`/`keyFindings` shapes
 * `PortfolioPage.tsx` already fetches from `/alpha-portfolio/status` and
 * `/alpha-portfolio/intelligence`, fed through the same pure
 * `derivePortfolioActions` this page never re-implements. These local
 * interfaces are the same wire-shape subset `PortfolioPage.tsx` declares
 * for itself -- only the fields `derivePortfolioActions` actually reads.
 */
interface AttentionItemView {
  ticker: string;
  category: AttentionCategory;
  caseId: string | null;
  ageDays: number | null;
}
interface ReviewQueueItemView {
  ticker: string;
  caseId: string | null;
  reasonCount: number;
  topCategory: AttentionCategory;
}
interface PortfolioStatusView {
  exists: boolean;
  summary: { unallocatedPercent: number | null } | null;
  attentionItems: AttentionItemView[];
  reviewQueue: ReviewQueueItemView[];
}
type PortfolioStatusFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: PortfolioStatusView };

type KeyFindingKind =
  | "high_concentration"
  | "elevated_concentration"
  | "large_unallocated"
  | "multiple_missing_cases"
  | "multiple_stale_cases"
  | "multiple_evidence_gaps";
interface KeyFindingView {
  kind: KeyFindingKind;
  count: number;
  tickers: string[];
}
interface MissingEvidenceItemLiteView {
  ticker: string;
  caseId: string;
}
interface PortfolioIntelligenceView {
  exists: boolean;
  keyFindings: KeyFindingView[];
  missingEvidence: MissingEvidenceItemLiteView[];
}
type PortfolioIntelligenceFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: PortfolioIntelligenceView };

/**
 * Compact, not a second Action Center -- Daily Brief's job is a pointer
 * a reader can scan in seconds, Portfolio's own workspace is where the
 * full queue lives. Capped flat at 3 (not per-severity like Portfolio's
 * own `MAX_ACTIONS_PER_SEVERITY`), most-severe-first per
 * `derivePortfolioActions`'s own existing ordering.
 */
const MAX_PRIORITIES = 3;

/**
 * Daily Brief v2 (Workspace Migration Phase 4) -- structure only, per
 * the approved Migration Review §10 item 5: ships "Portfolio Changes" /
 * "Watchlist Updates" (real Change Intelligence data, unchanged from v1)
 * and "Today's Priorities" (real Action Center data, reused from
 * Portfolio) ahead of the still-unbuilt narrative-synthesis paragraph
 * (§11.2), Opportunities (§11.3), and Upcoming Events / Market Context
 * (§11.4) -- each of the latter three stays an honest, calm "not yet
 * available" disclosure rather than fabricated content, the same
 * pattern Discovery's own Opportunities section already established.
 * No embedded Ask Atlas UI (Decision Log #2) -- this page never had one.
 */
export function DailyBriefPage() {
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const navigate = useNavigate();
  const [status, setStatus] = useState<DailyBriefStatus>({ kind: "loading" });
  const [portfolioMembership, setPortfolioMembership] = useState<PortfolioMembershipStatus>({ kind: "loading" });
  const [watchlist, setWatchlist] = useState<WatchlistStatus>({ kind: "loading" });
  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatusFetchStatus>({ kind: "loading" });
  const [portfolioIntelligence, setPortfolioIntelligence] = useState<PortfolioIntelligenceFetchStatus>({
    kind: "loading",
  });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/daily-brief", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DailyBriefView>;
      })
      .then((brief) => setStatus({ kind: "loaded", brief }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioMembershipView>;
      })
      .then((view) => setPortfolioMembership({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioMembership({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-watchlist", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<WatchlistEntryView[]>;
      })
      .then((entries) => setWatchlist({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setWatchlist({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio/status", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioStatusView>;
      })
      .then((report) => setPortfolioStatus({ kind: "loaded", report }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio/intelligence", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioIntelligenceView>;
      })
      .then((report) => setPortfolioIntelligence({ kind: "loaded", report }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioIntelligence({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  function openInvestmentCase(caseId: string) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "daily-brief" } });
  }

  const portfolioCaseIds = new Set(
    portfolioMembership.kind === "loaded"
      ? portfolioMembership.view.holdings.flatMap((holding) => (holding.caseId ? [holding.caseId] : []))
      : [],
  );
  const watchlistCaseIds = new Set(watchlist.kind === "loaded" ? watchlist.entries.map((entry) => entry.caseId) : []);

  const entries = status.kind === "loaded" ? status.brief.entries : [];
  // Portfolio takes precedence for a Case that is both held and
  // watchlisted -- mirrors `atlas.alpha.case_membership.known_cases`'s
  // own dedup precedence exactly, so a Case never appears in both lists.
  const portfolioChangeEntries = entries.filter((entry) => portfolioCaseIds.has(entry.caseId));
  const watchlistChangeEntries = entries.filter(
    (entry) => !portfolioCaseIds.has(entry.caseId) && watchlistCaseIds.has(entry.caseId),
  );

  const allActions: PortfolioAction[] = derivePortfolioActions(
    portfolioStatus.kind === "loaded" ? portfolioStatus.report.reviewQueue : [],
    portfolioIntelligence.kind === "loaded" ? portfolioIntelligence.report.missingEvidence : [],
    portfolioIntelligence.kind === "loaded" ? portfolioIntelligence.report.keyFindings : [],
    portfolioStatus.kind === "loaded" ? (portfolioStatus.report.summary?.unallocatedPercent ?? null) : null,
    portfolioStatus.kind === "loaded" ? portfolioStatus.report.attentionItems : [],
  );
  const topPriorities = allActions.slice(0, MAX_PRIORITIES);

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Heading level={3} style={PAGE_TITLE_STYLE}>
          {t("dailyBrief.title")}
        </Heading>

        <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
          <Text color="secondary">{t("dailyBrief.subtitle")}</Text>
          {status.kind === "loaded" && (
            <Text color="tertiary">
              {t("dailyBrief.lastUpdated", { time: new Date(status.brief.generatedAt).toLocaleString(locale) })}
            </Text>
          )}
        </Inline>

        <Divider tone="hairline" />

        {/* Orientation -- the same real, backend-templated summary
            sentence Daily Brief has always used (Migration Review §11.2
            defers a fabricated multi-sentence narrative -- no real
            synthesis step exists yet). Flowing paragraph, not a heading
            -- Figma's own screen reads it as prose, not a titled block. */}
        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {status.kind === "error" && <Text color="secondary">{status.message}</Text>}
        {status.kind === "loaded" && <Text as="p">{status.brief.summary}</Text>}

        <Divider tone="hairline" />

        {/* Today's Priorities -- reuses Portfolio's real Action Center
            derivation and copy verbatim (see module doc comment). */}
        <Stack gap="metadata">
          <Label>{t("dailyBrief.priorities.heading")}</Label>
          {topPriorities.length === 0 && <Text color="tertiary">{t("dailyBrief.priorities.empty")}</Text>}
          {topPriorities.map((action, index) => {
            const { title } = describePortfolioAction(action, t);
            return (
              <Inline key={action.id} gap="row" align="baseline" style={{ justifyContent: "space-between" }}>
                <Text as="span">
                  {SEVERITY_EMOJI[action.severity]} {index + 1}. {title}
                </Text>
                {action.caseId ? (
                  <Link
                    href="#"
                    style={ACCENT_LINK_STYLE}
                    onClick={(event) => {
                      event.preventDefault();
                      openInvestmentCase(action.caseId!);
                    }}
                  >
                    {t("dailyBrief.priorities.reviewButton")} →
                  </Link>
                ) : (
                  <Link
                    href="#"
                    style={ACCENT_LINK_STYLE}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate("/portfolio");
                    }}
                  >
                    {t("dailyBrief.priorities.goToPortfolioButton")} →
                  </Link>
                )}
              </Inline>
            );
          })}
        </Stack>

        <Divider tone="hairline" />

        {/* Portfolio Changes | Watchlist Updates -- the approved screen's
            own two-column pairing. `New Opportunities`/`Upcoming Events`/
            `Market Context` have no real data source in this Alpha (no
            candidate generator, no earnings-calendar/macro provider) --
            per the History precedent this program already established,
            multiple large "not yet available" blocks would make the page
            look unfinished; they are omitted entirely rather than shown
            as empty placeholders, leaving only genuinely real content. */}
        <Inline gap="inter-section" wrap align="start">
          <div style={{ flex: "1 1 380px", minWidth: 0 }}>
            <Stack gap="metadata">
              <Label>{t("dailyBrief.portfolioChanges.heading")}</Label>
              {status.kind === "loaded" && portfolioChangeEntries.length === 0 && (
                <Text color="tertiary">{t("dailyBrief.portfolioChanges.empty")}</Text>
              )}
              {portfolioChangeEntries.map((entry) => (
                <DailyBriefEntryRow key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
              ))}
            </Stack>
          </div>
          <div style={{ flex: "1 1 380px", minWidth: 0 }}>
            <Stack gap="metadata">
              <Label>{t("dailyBrief.watchlistUpdates.heading")}</Label>
              {status.kind === "loaded" && watchlistChangeEntries.length === 0 && (
                <Text color="tertiary">{t("dailyBrief.watchlistUpdates.empty")}</Text>
              )}
              {watchlistChangeEntries.map((entry) => (
                <DailyBriefEntryRow key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
              ))}
            </Stack>
          </div>
        </Inline>
      </Stack>
    </Container>
  );
}

/** Visual Fidelity Pass -- one dense row per entry (ticker + first
 * change line + a "Review" link into the Investment Case), replacing
 * the former per-entry Surface card. `changeSummary`'s remaining
 * lines and `whyItMatters` stay real, evidence-traceable content --
 * genuinely deeper detail belongs on the Investment Case page itself
 * (one click away via the same link), not duplicated here. */
function DailyBriefEntryRow({
  entry,
  onOpen,
  t,
}: {
  entry: DailyBriefEntryView;
  onOpen: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const firstChangeLine = entry.changeSummary.split("\n")[0] ?? entry.headline;
  return (
    <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
      <Text as="span">
        <Text as="span" color="secondary">
          {entry.ticker ?? t("dailyBrief.entry.unknownCompany")} —{" "}
        </Text>
        {firstChangeLine}
      </Text>
      <Link
        href="#"
        style={ACCENT_LINK_STYLE}
        onClick={(event) => {
          event.preventDefault();
          onOpen();
        }}
      >
        {t("dailyBrief.entry.openInvestmentCase")} →
      </Link>
    </Inline>
  );
}
