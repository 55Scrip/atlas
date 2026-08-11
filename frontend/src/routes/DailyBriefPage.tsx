import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { derivePortfolioActions, type AttentionCategory, type PortfolioAction } from "../portfolio/derivePortfolioActions";
import { describePortfolioAction, SEVERITY_EMOJI } from "../portfolio/describePortfolioAction";

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
  const { t } = useTranslation();
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
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("dailyBrief.title")}</Heading>

        <Divider />

        {/* Orientation -- narrative-first per this sprint's requirement,
            but the sentence itself is the same real, backend-templated
            count sentence Daily Brief v1 always used. No fabricated
            multi-sentence narrative paragraph (Migration Review §11.2
            explicitly defers that -- it needs a real synthesis step that
            does not exist yet); rendered at heading scale so it reads
            within seconds, not as one Text line among many. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            {status.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {status.kind === "error" && <Text color="secondary">{status.message}</Text>}
            {status.kind === "loaded" && <Heading level={2}>{status.brief.summary}</Heading>}
          </Stack>
        </Surface>

        <Divider />

        {/* Today's Priorities -- reuses Portfolio's real Action Center
            derivation and copy verbatim (see module doc comment). */}
        <Surface tier="primary">
          <Stack gap="intra-section">
            <Heading level={2}>{t("dailyBrief.priorities.heading")}</Heading>
            {topPriorities.length === 0 && <Text color="secondary">{t("dailyBrief.priorities.empty")}</Text>}
            {topPriorities.map((action) => {
              const { title, reason } = describePortfolioAction(action, t);
              return (
                <Stack key={action.id} gap="metadata">
                  <Text as="p">
                    {SEVERITY_EMOJI[action.severity]} {title}
                  </Text>
                  <Text color="secondary" as="p">
                    {reason}
                  </Text>
                  <div>
                    {action.caseId ? (
                      <Button variant="primary" onClick={() => openInvestmentCase(action.caseId!)}>
                        {t("dailyBrief.priorities.reviewButton")}
                      </Button>
                    ) : (
                      <Button variant="tertiary" onClick={() => navigate("/portfolio")}>
                        {t("dailyBrief.priorities.goToPortfolioButton")}
                      </Button>
                    )}
                  </div>
                  <Divider tone="hairline" />
                </Stack>
              );
            })}
          </Stack>
        </Surface>

        <Divider />

        {/* Portfolio Changes -- entries.filter narrows Daily Brief v1's
            already-real entry list to Portfolio holdings; every field
            rendered per entry is unchanged from v1. */}
        <Heading level={2}>{t("dailyBrief.portfolioChanges.heading")}</Heading>
        {status.kind === "loaded" && portfolioChangeEntries.length === 0 && (
          <Text color="secondary">{t("dailyBrief.portfolioChanges.empty")}</Text>
        )}
        {portfolioChangeEntries.map((entry) => (
          <DailyBriefEntryCard key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
        ))}

        <Divider />

        {/* Watchlist Updates -- same entry list, the complementary
            Watchlist-only slice. */}
        <Heading level={2}>{t("dailyBrief.watchlistUpdates.heading")}</Heading>
        {status.kind === "loaded" && watchlistChangeEntries.length === 0 && (
          <Text color="secondary">{t("dailyBrief.watchlistUpdates.empty")}</Text>
        )}
        {watchlistChangeEntries.map((entry) => (
          <DailyBriefEntryCard key={entry.caseId} entry={entry} onOpen={() => openInvestmentCase(entry.caseId)} t={t} />
        ))}

        <Divider />

        {/* Opportunities -- no candidate generator exists in this Alpha
            (Migration Review §11.3); an honest, calm disclosure rather
            than a fabricated list, the same pattern Discovery's own
            Opportunities section already established. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dailyBrief.opportunities.heading")}</Heading>
            <Text color="secondary">{t("dailyBrief.opportunities.notYet")}</Text>
          </Stack>
        </Surface>

        {/* Upcoming -- no earnings-calendar/macro/market-context provider
            exists in this Alpha (Migration Review §11.4); same honest
            disclosure pattern, not a fabricated events list. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dailyBrief.upcoming.heading")}</Heading>
            <Text color="secondary">{t("dailyBrief.upcoming.notYet")}</Text>
          </Stack>
        </Surface>
      </Stack>
    </Container>
  );
}

function DailyBriefEntryCard({
  entry,
  onOpen,
  t,
}: {
  entry: DailyBriefEntryView;
  onOpen: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={3}>{entry.ticker ?? t("dailyBrief.entry.unknownCompany")}</Heading>
        <Text as="p">{entry.headline}</Text>
        {entry.changeSummary.split("\n").map((line, index) => (
          <Text as="p" color="secondary" key={index}>
            {line}
          </Text>
        ))}
        <Text as="p" color="tertiary">
          {entry.whyItMatters}
        </Text>
        <div>
          <Button variant="tertiary" onClick={onOpen}>
            {t("dailyBrief.entry.openInvestmentCase")}
          </Button>
        </div>
      </Stack>
    </Surface>
  );
}
