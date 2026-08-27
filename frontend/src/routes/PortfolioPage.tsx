import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, StatusBadge, Surface, Text, VisuallyHidden } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  type AnalysisCoverageLevel,
  type ConvictionLevel,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type ReviewPriority,
} from "../status/statusTone";
import type { StatusTone } from "../foundation";
import type { AnalysisRiskStatus } from "../changeIntelligence/describeChange";
import { FitBadge } from "../portfolioFit/FitBadge";
import { fetchPortfolioFitForHoldings, type PortfolioFitAssessmentView, type FitRating } from "../portfolioFit/portfolioFitApi";
import { fetchStanceForHoldings, type TickerStanceView, type StanceView } from "../stance/stanceApi";
import { StanceBadge } from "../stance/StanceBadge";
import { primaryStanceReason, stanceReasonSentence } from "../stance/describeStance";
import type { StanceLevel } from "../status/statusTone";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { realHeadlineText } from "../dailyBriefAgenda/bookkeepingFilter";
import { MonitoringFreshnessNote } from "../monitoring/MonitoringFreshnessNote";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { invalidateAlphaPortfolio, setAlphaPortfolioData, useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { fetchMonitoringStatus, type MonitoringOperationalStatusView } from "../monitoring/monitoringApi";
import { sortHoldings, type HoldingSortKey } from "../portfolio/sortHoldings";
import { deriveInvestmentRating } from "../investmentCase/atlasRatingModel";
import { CompactRatingBadge } from "../investmentCase/CompactRatingBadge";

/** Alpha Integration Fix (One Product Pass): Portfolio no longer treats
 * the shared `/api/daily-brief-agenda` fetch (filtered to
 * `group === "portfolio"`) as its own attention/priority source -- the
 * Alpha Product Integration Review found that doing so put Portfolio in
 * direct competition with Daily Brief's own "what changed" job across
 * five separate surfaces on this page (Hero, Pulse's attention count,
 * "Today's Story," "Attention Required," and the Holdings Table's
 * Reason column). All five are now gone or reworked to use Portfolio's
 * own signals (ownership facts, Portfolio Fit, Stance) instead. This
 * fetch's one remaining, in-scope consumer is
 * `TodaysBiggestRiskOpportunity`'s own "what changed" line. */
type DailyBriefAgendaFetchStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; items: AgendaItemView[] };

/** Deliverable 7 (Portfolio Fit Engine) -- `assessments` arrives already
 * sorted best-first from `PortfolioFitService.assess_all_holdings`. */
type PortfolioFitFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; assessments: PortfolioFitAssessmentView[] };

/** Atlas Intelligence Sprint 2 (Recommendation Quality &
 * Actionability, Deliverable 6). */
type StanceHoldingsFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: TickerStanceView[] };

/**
 * `concentrationLevel` is an internal enum value (`ConcentrationLevel.LOW`
 * etc., `atlas/domains/portfolio/models.py`, serialized as its raw
 * `.value` — "Low", "Moderate", "Elevated", "High") — the value itself
 * stays English on the wire, per the localization architecture. This
 * maps it to a translated word only where it's displayed.
 */
const CONCENTRATION_LEVEL_KEY: Record<string, TranslationKey> = {
  Low: "portfolio.concentrationLevel.low",
  Moderate: "portfolio.concentrationLevel.moderate",
  Elevated: "portfolio.concentrationLevel.elevated",
  High: "portfolio.concentrationLevel.high",
};

interface HoldingView {
  ticker: string;
  weightPercent: number;
  valueAbsolute: number | null;
  caseId: string | null;
  reconciliationStatus: "NONE" | "UPDATED" | "AWAITING_RECONCILIATION";
}

interface PortfolioView {
  exists: boolean;
  entryMode: string | null;
  hasAbsoluteValues: boolean;
  holdings: HoldingView[];
  cashWeightPercent: number | null;
  cashValueAbsolute: number | null;
  totalValue: number | null;
  numberOfHoldings: number;
  concentrationLevel: string | null;
  objective: string | null;
  horizon: string | null;
  awaitingReconciliation: boolean;
}

/**
 * Product Sprint 8 (Portfolio Excellence, Deliverable 4): the
 * `/alpha-portfolio/status` and `/alpha-portfolio/intelligence` fetches
 * that used to live here, and the ~20 types that described their wire
 * shape, are gone. Both endpoints had exactly one live consumer on this
 * page -- `derivePortfolioActions` (deleted, see the module docstring
 * above) -- everything else they carried (`PortfolioIntelligencePanels`,
 * the Key Findings/Risk Signals two-column block) was already dead code,
 * confirmed via a fresh-from-disk audit: implemented in full but never
 * called anywhere in this file's render tree. Every real fact either
 * endpoint contributed that this page actually shows -- holdings count,
 * cash, concentration level, largest position -- is already on the base
 * `/alpha-portfolio` `PortfolioView` this page fetches regardless, or is
 * a real signal in the shared Daily Brief Agenda this page already
 * reads. Two fewer network calls, ~180 fewer lines of now-unreachable
 * type declarations -- simplification, not a feature loss.
 */

/**
 * ATLAS-028 Portfolio Cockpit -- one canonical, portfolio-scoped per-
 * holding analysis, projected from `CanonicalAnalysis`
 * (`atlas/alpha/portfolio_cockpit/`). Every value below comes straight
 * from `GET /alpha-portfolio/cockpit`; this page computes nothing of
 * its own beyond translating enum values -- the same "no domain logic
 * in the UI" discipline this whole page follows.
 * Portfolio Cockpit is the overview; a holding's own
 * Investment Case (one click away via `caseId`) is the depth.
 */
/** `ConvictionLevel`/`AnalysisCoverageLevel`/`ReviewPriority` now live
 * in `../status/statusTone` (Workspace Migration, Foundation
 * extraction) -- these local aliases keep every existing `Cockpit*`
 * usage site in this file unchanged. `CockpitRiskStatus` joins them in
 * Phase 2 (Portfolio migration): the Holdings table now renders a real
 * Risk column, reusing `AnalysisRiskStatus`'s own translation-key map
 * (`RISK_STATUS_KEY`, `../changeIntelligence/describeChange`) verbatim
 * rather than declaring a fourth copy of the same five-value enum --
 * Portfolio and Investment Case must read the same Risk vocabulary,
 * the same cross-surface consistency rule already applied to
 * Conviction/Confidence. */
type CockpitConvictionLevel = ConvictionLevel;
type CockpitAnalysisCoverageLevel = AnalysisCoverageLevel;
type CockpitValuationStatus = "not_evaluated" | "insufficient_input" | "undervalued" | "fairly_valued" | "expensive";
type CockpitRiskCategory = "business_risk" | "financial_risk" | "valuation_risk" | "thesis_risk";
type CockpitRiskStatus = AnalysisRiskStatus;
type CockpitBusinessStatus = "not_evaluated" | "insufficient_input" | "weak" | "moderate" | "strong";
type CockpitReviewPriority = ReviewPriority;
type CockpitAttentionReason =
  | "high_financial_risk"
  | "high_valuation_risk"
  | "low_conviction"
  | "contradicting_evidence"
  | "insufficient_evidence";

interface CockpitConvictionView {
  level: CockpitConvictionLevel;
  reasons: string[];
}

interface CockpitAnalysisCoverageView {
  level: CockpitAnalysisCoverageLevel;
  reasons: string[];
}

interface CockpitValuationView {
  status: CockpitValuationStatus;
}

interface CockpitBusinessSummaryView {
  growth: CockpitBusinessStatus;
  capitalAllocation: CockpitBusinessStatus;
}

interface CockpitRiskProjectionView {
  category: CockpitRiskCategory;
  status: CockpitRiskStatus;
}

interface CockpitAttentionView {
  priority: CockpitReviewPriority;
  reasons: CockpitAttentionReason[];
}

/** Migration Review §11.1's Holdings-table Action column -- evidence-
 * support language only, never a raw RecommendationDirection member
 * name (Decision Log #1). See `atlas.alpha.decision_support`'s own
 * module docstring (backend) for the full presentation-layer
 * rationale; `badgeLabel`/`statement` are read only as an English-only
 * fallback shape check -- this page owns the localized text via
 * `DECISION_SUPPORT_BADGE_KEY`, the same convention every other
 * categorical field on this page already follows. */
interface CockpitDecisionSupportView {
  level: DecisionSupportLevel;
  badgeLabel: string;
  statement: string;
}

interface PortfolioCockpitHoldingView {
  ticker: string;
  caseId: string;
  weightPercent: number;
  valueAbsolute: number | null;
  reconciliationStatus: "NONE" | "UPDATED" | "AWAITING_RECONCILIATION";
  conviction: CockpitConvictionView;
  analysisCoverage: CockpitAnalysisCoverageView;
  valuation: CockpitValuationView;
  business: CockpitBusinessSummaryView;
  riskProjection: CockpitRiskProjectionView;
  confidence: EvidenceCoverageLevel;
  isThesisStale: boolean;
  attention: CockpitAttentionView;
  decisionSupport: CockpitDecisionSupportView;
}

interface CockpitUnresolvedHoldingView {
  ticker: string;
  caseId: string | null;
}

interface PortfolioCockpitView {
  exists: boolean;
  holdings: PortfolioCockpitHoldingView[];
  unresolvedHoldings: CockpitUnresolvedHoldingView[];
  priorityReviewCount: number;
}

type Status =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: PortfolioView };

/** Same independent-fetch pattern -- a Cockpit fetch failure never
 *  blocks Holdings from rendering; each row simply falls back to its
 *  pre-Cockpit appearance (ticker/weight/reconciliation only). */
type PortfolioCockpitFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: PortfolioCockpitView };

type CaseCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "error"; message: string };

type ReconcileStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string };

interface ReplaceRow {
  ticker: string;
  weightPercent: string;
  valueAbsolute: string;
}

/**
 * Portfolio (Alpha Sprint 1A, extended Alpha Sprint 1B). Shows holdings,
 * allocation percentages, cash/unallocated when known, a path from any
 * holding into an Investment Case, and -- since Sprint 1B -- each
 * holding's status relative to the most recently recorded trade
 * ("Updated automatically" or "Awaiting reconciliation"), plus a
 * portfolio-level banner and reconciliation actions when any holding is
 * awaiting reconciliation.
 *
 * Foundation Patch: a holding that already has a linked Investment Case
 * (`holding.caseId`, persisted by the backend's case-link endpoint)
 * navigates straight there — no new Case is created. Only a holding
 * with no linked Case yet creates one and records the association.
 */
export function PortfolioPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const portfolioResource = useAlphaPortfolio();
  const status: Status =
    portfolioResource.kind === "loaded" ? { kind: "loaded", view: portfolioResource.data as PortfolioView } : portfolioResource;
  const [cockpit, setCockpit] = useState<PortfolioCockpitFetchStatus>({ kind: "loading" });
  /** Deliverable 7 (Portfolio Fit Engine) -- best/worst fit today and
   * improved/worsened, all read from one `/api/portfolio-fit/holdings`
   * fetch (already sorted best-first server-side). */
  const [portfolioFitHoldings, setPortfolioFitHoldings] = useState<PortfolioFitFetchStatus>({ kind: "loading" });
  const [stanceHoldings, setStanceHoldings] = useState<StanceHoldingsFetchStatus>({ kind: "loading" });
  /** Deliverable 13 -- the same shared agenda Daily Brief itself reads. */
  const [dailyBriefAgenda, setDailyBriefAgenda] = useState<DailyBriefAgendaFetchStatus>({ kind: "loading" });
  /** Atlas Intelligence Sprint 8 (Automated Monitoring Operations,
   * Deliverable 9) -- operational freshness only, never Portfolio
   * quality/performance/Portfolio Fit. */
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringOperationalStatusView | null>(null);
  const [caseCreateStatus, setCaseCreateStatus] = useState<Record<string, CaseCreateStatus>>({});

  const [showReplaceForm, setShowReplaceForm] = useState(false);
  const [replaceRows, setReplaceRows] = useState<ReplaceRow[]>([]);
  const [replaceCashWeight, setReplaceCashWeight] = useState("");
  const [replaceCashValue, setReplaceCashValue] = useState("");
  const [replaceStatus, setReplaceStatus] = useState<ReconcileStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioFitForHoldings(controller.signal)
      .then((assessments) => setPortfolioFitHoldings({ kind: "loaded", assessments }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioFitHoldings({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchStanceForHoldings(controller.signal)
      .then((entries) => setStanceHoldings({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStanceHoldings({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  /** Reliability Fix Sprint P2.1 -- this fetch used to cancel itself via
   * `AbortController`, the same pattern every other fetch on this page
   * still uses. Under React 18 StrictMode's dev-only mount -> cleanup ->
   * remount cycle, that abort call was confirmed (via direct
   * instrumentation, then experimentally verified by removing it) to
   * corrupt the *second*, kept request as well -- not just the first,
   * StrictMode-discarded one -- leaving `dailyBriefAgenda` stuck at its
   * initial `{ kind: "loading" }` forever, since the one effect that
   * would ever move it out of that state never got a chance to resolve
   * successfully. This endpoint's own response is large enough (~38
   * items, each carrying translated reason facts) relative to the dozen
   * other requests this page fires on mount that it was the one
   * request consistently unlucky enough to lose that race; the sibling
   * `AbortController`-cancelled fetches on this page have not shown
   * the same failure and are intentionally left as they are -- this
   * fix is scoped to the one proven-broken effect, not a page-wide
   * data-fetching refactor. A plain `cancelled` flag replaces the
   * AbortController: both the StrictMode-discarded request and the
   * real one are now allowed to actually complete over the network:
   * the stale request's own result, whenever it arrives, is inert
   * (ignored via the flag) rather than being denied outright, so it
   * can never corrupt the current request's connection, and the
   * current request can always reach `loaded` or `error` -- never an
   * indefinite `loading`. */
  useEffect(() => {
    let cancelled = false;
    fetchDailyBriefAgenda()
      .then((agenda) => {
        if (cancelled) return;
        setDailyBriefAgenda({ kind: "loaded", items: agenda.items.filter((item) => item.group === "portfolio") });
      })
      .catch(() => {
        if (cancelled) return;
        setDailyBriefAgenda({ kind: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchMonitoringStatus(controller.signal)
      .then((s) => setMonitoringStatus(s))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/alpha-portfolio/cockpit", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<PortfolioCockpitView>;
      })
      .then((report) => setCockpit({ kind: "loaded", report }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCockpit({ kind: "error" });
      });

    return () => controller.abort();
  }, []);

  function openInvestmentCase(ticker: string, existingCaseId: string | null) {
    if (existingCaseId) {
      navigate(`/investment-case/${existingCaseId}`, { state: { origin: "portfolio", ticker } });
      return;
    }

    setCaseCreateStatus((current) => ({ ...current, [ticker]: { kind: "creating" } }));
    fetch("/api/cases", { method: "POST" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<{ caseId: string }>;
      })
      .then((created) => {
        if (ticker === "__new__") {
          navigate(`/investment-case/${created.caseId}`, { state: { origin: "portfolio" } });
          return;
        }
        return fetch(`/api/alpha-portfolio/holdings/${encodeURIComponent(ticker)}/case-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidateCaseId: created.caseId }),
        })
          .then((linkResponse) => {
            if (!linkResponse.ok) {
              throw new Error(`Backend responded with ${linkResponse.status}`);
            }
            return linkResponse.json() as Promise<{ caseId: string }>;
          })
          .then((linked) => {
            invalidateAlphaPortfolio();
            navigate(`/investment-case/${linked.caseId}`, { state: { origin: "portfolio", ticker } });
          });
      })
      .catch((error: unknown) => {
        setCaseCreateStatus((current) => ({
          ...current,
          [ticker]: {
            kind: "error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function openReplaceForm() {
    if (status.kind === "loaded" && status.view.exists) {
      setReplaceRows(
        status.view.holdings.map((holding) => ({
          ticker: holding.ticker,
          weightPercent: String(holding.weightPercent),
          valueAbsolute: holding.valueAbsolute !== null ? String(holding.valueAbsolute) : "",
        })),
      );
      setReplaceCashWeight(
        status.view.cashWeightPercent !== null ? String(status.view.cashWeightPercent) : "",
      );
      setReplaceCashValue(
        status.view.cashValueAbsolute !== null ? String(status.view.cashValueAbsolute) : "",
      );
    }
    setReplaceStatus({ kind: "idle" });
    setShowReplaceForm(true);
  }

  function updateReplaceRow(index: number, patch: Partial<ReplaceRow>) {
    setReplaceRows((current) =>
      current.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );
  }

  /** Phase 6E, Phase 2 (Edit Portfolio): the one add-a-holding action --
   * an empty row the investor fills in and saves, exactly like editing
   * any other row. No separate "add holding" flow, no separate form. */
  function addReplaceRow() {
    setReplaceRows((current) => [...current, { ticker: "", weightPercent: "", valueAbsolute: "" }]);
  }

  /** The one remove-a-holding action -- deleting the row and saving
   * submits the same `REPLACE_ALLOCATION` request without that ticker,
   * exactly as if it had never been entered. */
  function removeReplaceRow(index: number) {
    setReplaceRows((current) => current.filter((_, i) => i !== index));
  }

  function submitReplaceAllocation() {
    const holdings = replaceRows
      .filter((row) => row.ticker.trim() !== "")
      .map((row) => ({
        ticker: row.ticker.trim(),
        weightPercent: Number.parseFloat(row.weightPercent),
        valueAbsolute: row.valueAbsolute.trim() === "" ? null : Number.parseFloat(row.valueAbsolute),
      }));

    if (holdings.length === 0 || holdings.some((h) => Number.isNaN(h.weightPercent))) {
      setReplaceStatus({
        kind: "error",
        message: t("portfolio.replaceForm.errors.invalidPercentage"),
      });
      return;
    }

    setReplaceStatus({ kind: "submitting" });
    fetch("/api/alpha-portfolio/reconcile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "REPLACE_ALLOCATION",
        holdings,
        cashWeightPercent:
          replaceCashWeight.trim() === "" ? null : Number.parseFloat(replaceCashWeight),
        cashValueAbsolute:
          replaceCashValue.trim() === "" ? null : Number.parseFloat(replaceCashValue),
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setReplaceStatus({ kind: "error", message: body.detail ?? t("common.invalidInput") });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const view = (await response.json()) as PortfolioView;
        setAlphaPortfolioData(view);
        setReplaceStatus({ kind: "idle" });
        setShowReplaceForm(false);
      })
      .catch((error: unknown) => {
        setReplaceStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  const unallocatedPercent =
    status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0
      ? 100 -
        status.view.holdings.reduce((sum, holding) => sum + holding.weightPercent, 0) -
        (status.view.cashWeightPercent ?? 0)
      : null;

  /** Product Sprint 8 (Portfolio Excellence): weight-sorted holdings and
   * the Cockpit coverage count were previously each computed twice
   * independently (once in `PortfolioPulse`, once in `PortfolioSidebar`)
   * over the exact same source data -- the same duplication risk this
   * sprint's own Deliverable 16 flags. Computed once here instead and
   * passed down, so the two can never quietly disagree. */
  const holdings = status.kind === "loaded" && status.view.exists ? status.view.holdings : [];
  const holdingsByWeightDesc = [...holdings].sort((a, b) => b.weightPercent - a.weightPercent);
  const largestHolding = holdingsByWeightDesc[0] ?? null;
  const coveredCount =
    cockpit.kind === "loaded"
      ? cockpit.report.holdings.filter((h) => h.analysisCoverage.level !== "no_coverage").length
      : null;

  /** Alpha Integration Fix (One Product Pass): Portfolio no longer
   * maintains its own priority-ranked view of the shared Daily Brief
   * Agenda -- "what changed, and how urgent is it" is Daily Brief's own
   * job (see the Alpha Product Integration Review's Phase 8 finding).
   * The one remaining, in-scope consumer of the Agenda fetch on this
   * page is `TodaysBiggestRiskOpportunity`'s own "what changed" line,
   * which reads real items by ticker only -- no priority ranking, no
   * attention count. */
  const agendaItems = dailyBriefAgenda.kind === "loaded" ? dailyBriefAgenda.items : [];
  const agendaItemByTicker = new Map<string, AgendaItemView>();
  for (const item of agendaItems) {
    if (item.ticker) {
      agendaItemByTicker.set(item.ticker, item);
    }
  }

  /** Same reasoning, for Portfolio Fit -- one ticker->assessment map,
   * shared by the Holdings Table's Fit column/sort and the Weakest
   * Holdings section below, both reading the one already-sorted
   * `/api/portfolio-fit/holdings` fetch. */
  const fitAssessments = portfolioFitHoldings.kind === "loaded" ? portfolioFitHoldings.assessments : [];
  const fitByTicker = new Map<string, PortfolioFitAssessmentView>();
  for (const assessment of fitAssessments) {
    fitByTicker.set(assessment.ticker, assessment);
  }

  /** Portfolio Redesign V1 -- one selection, shared by the Executive
   * Summary Strip's own compact "Largest Risk"/"Largest Opportunity"
   * fields and the fuller Today's Biggest Risk/Opportunity cards below
   * them, so the same two tickers never diverge between a compact
   * mention and its own full explanation. Reads the same server-sorted
   * (best-first) `PortfolioFitAssessmentView[]` `PortfolioFitOverviewSection`
   * already renders in full further down the page -- no new fetch, no
   * new fit computation. `null` when fewer than two holdings have been
   * evaluated, or the single evaluated holding would have to serve as
   * both its own biggest risk and biggest opportunity. */
  const fitEvaluated = fitAssessments.filter((a) => a.overall !== "unavailable");
  const biggestOpportunity = fitEvaluated[0] ?? null;
  const biggestRisk = fitEvaluated.length > 1 ? fitEvaluated[fitEvaluated.length - 1]! : null;
  const hasDistinctRiskAndOpportunity =
    biggestOpportunity !== null && biggestRisk !== null && biggestOpportunity.ticker !== biggestRisk.ticker;

  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 6) -- one ticker->Stance map, the same
   * "single shared fetch, no divergent copies" pattern `fitByTicker`
   * above already establishes, feeding the Holdings Table's own
   * "Current view" column and sort. */
  const stanceEntries = stanceHoldings.kind === "loaded" ? stanceHoldings.entries : [];
  const stanceByTicker = new Map<string, StanceLevel>();
  /** Status Consolidation (Implementation Sprint B3): the same
   * already-fetched entries, kept as full `StanceView` objects (not
   * just `.level`) so the Holdings Table's "Why" column can read
   * `.reasoning[0]` -- no new fetch, `stanceByTicker` above is
   * untouched and still feeds `sortHoldings`'s own "stance" sort key. */
  const stanceViewByTicker = new Map<string, StanceView>();
  for (const entry of stanceEntries) {
    stanceByTicker.set(entry.ticker, entry.stance.level);
    stanceViewByTicker.set(entry.ticker, entry.stance);
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <PortfolioPageHeader
          monitoringStatus={monitoringStatus}
          hasHoldings={status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0}
          onEditPortfolio={openReplaceForm}
          t={t}
        />

        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {status.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("portfolio.loadError", { message: status.message })}
          </Text>
        )}

        {status.kind === "loaded" && !status.view.exists && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>{t("portfolio.notEstablished")}</Text>
              <RouterLink to="/welcome" style={ACCENT_LINK_STYLE}>
                {t("portfolio.setupLink")}
              </RouterLink>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length === 0 && (
          <PortfolioEmptyState view={status.view} t={t} />
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0 && (
          <Stack gap="intra-section">
            {/* Alpha Integration Fix (One Product Pass): the Hero leads
                with ownership, Portfolio's own doctrine question ("what
                do I own"), not an attention-count verdict -- that's
                Daily Brief's job. */}
            <PortfolioHero view={status.view} t={t} />

            {status.view.awaitingReconciliation && !showReplaceForm && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Text color="tertiary" role="status">
                    {t("portfolio.awaitingBanner.title")}
                  </Text>
                  <Text color="secondary">{t("portfolio.awaitingBanner.body")}</Text>
                  <div>
                    <Button variant="tertiary" onClick={openReplaceForm}>
                      {t("portfolio.editPortfolio.button")}
                    </Button>
                  </div>
                </Stack>
              </Surface>
            )}

            {/* Product Simplification Sprint 6E, Phase 2 -- the one
                portfolio-management action: add, remove, increase, or
                decrease any holding, all as edits to the same list,
                saved together. Atlas infers everything else (Case
                creation/linking, re-analysis) from the result, exactly
                as it already does for an import. Replaces both the
                old, always-hidden "Replace entire allocation" form and
                the per-row inline Reconcile toggle that used to offer a
                second, competing way to change a holding's weight. */}
            {showReplaceForm && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Heading level={2}>{t("portfolio.editPortfolio.heading")}</Heading>
                  {replaceRows.map((row, index) => (
                    <Stack key={index} gap="inter-section">
                      <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
                        <Text as="label">
                          {t("form.ticker")}
                          <br />
                          <input
                            value={row.ticker}
                            onChange={(event) => updateReplaceRow(index, { ticker: event.target.value })}
                          />
                        </Text>
                        <Text as="label">
                          {t("form.weightPercent")}
                          <br />
                          <input
                            value={row.weightPercent}
                            onChange={(event) =>
                              updateReplaceRow(index, { weightPercent: event.target.value })
                            }
                          />
                        </Text>
                        <Text as="label">
                          {t("form.valueOptional")}
                          <br />
                          <input
                            value={row.valueAbsolute}
                            onChange={(event) =>
                              updateReplaceRow(index, { valueAbsolute: event.target.value })
                            }
                          />
                        </Text>
                        <Link
                          href="#"
                          style={{ color: "var(--color-text-tertiary)" }}
                          onClick={(event) => {
                            event.preventDefault();
                            removeReplaceRow(index);
                          }}
                        >
                          {t("form.removeButton")}
                        </Link>
                      </Inline>
                      <Divider tone="hairline" />
                    </Stack>
                  ))}
                  <div>
                    <Button variant="tertiary" onClick={addReplaceRow}>
                      {t("portfolio.editPortfolio.addHoldingButton")}
                    </Button>
                  </div>
                  <Text as="label">
                    {t("form.cashPercent")}
                    <br />
                    <input
                      value={replaceCashWeight}
                      onChange={(event) => setReplaceCashWeight(event.target.value)}
                    />
                  </Text>
                  <Text as="label">
                    {t("form.cashValueOptional")}
                    <br />
                    <input
                      value={replaceCashValue}
                      onChange={(event) => setReplaceCashValue(event.target.value)}
                    />
                  </Text>
                  {replaceStatus.kind === "error" && (
                    <Text color="tertiary" role="alert">
                      {replaceStatus.message}
                    </Text>
                  )}
                  <div>
                    <Button
                      variant="primary"
                      onClick={submitReplaceAllocation}
                      disabled={replaceStatus.kind === "submitting"}
                    >
                      {replaceStatus.kind === "submitting"
                        ? t("common.saving")
                        : t("portfolio.editPortfolio.saveButton")}
                    </Button>{" "}
                    <Button variant="tertiary" onClick={() => setShowReplaceForm(false)}>
                      {t("common.cancel")}
                    </Button>
                  </div>
                </Stack>
              </Surface>
            )}

            {/* Portfolio Redesign V1 -- the Executive Summary Strip now
                sits directly under the Hero, ahead of the Risk/
                Opportunity cards, so every fact promised by "five
                seconds to understand the portfolio" is visible before
                any individual holding. Alpha Integration Fix: the
                Agenda-derived Attention Items figure and critical-item
                pill are gone -- that surface duplicated Daily Brief's
                own job (Alpha Product Integration Review, Phase 8). */}
            <PortfolioPulse
              view={status.view}
              largestHolding={largestHolding}
              coveredCount={coveredCount}
              biggestRisk={hasDistinctRiskAndOpportunity ? biggestRisk : null}
              biggestOpportunity={hasDistinctRiskAndOpportunity ? biggestOpportunity : null}
              t={t}
            />

            {/* Portfolio Redesign V1 -- "Today's Biggest Risk" /
                "Today's Biggest Opportunity": the same two tickers the
                Executive Summary Strip just named, now with their own
                full reasoning, what changed, and an explicit action --
                the "compact fact in the story, full detail as evidence
                right after" shape this codebase already uses for Since
                You Were Here and the top limiting factor on Investment
                Case. No new fetch, no new fit computation. */}
            <TodaysBiggestRiskOpportunity
              biggestOpportunity={hasDistinctRiskAndOpportunity ? biggestOpportunity : null}
              biggestRisk={hasDistinctRiskAndOpportunity ? biggestRisk : null}
              agendaItemByTicker={agendaItemByTicker}
              onOpenCase={openInvestmentCase}
              t={t}
            />

            {/* Alpha Integration Fix (One Product Pass): Attention
                Required is gone -- it re-ranked this same page's holdings
                by Daily Brief's own Agenda priority, duplicating Daily
                Brief's "what changed" job outright (Alpha Product
                Integration Review, Phase 8). Portfolio Weaknesses further
                below already answers "which holdings are worth a second
                look," using Portfolio's own Fit/Decision-Support signals
                instead of Daily Brief's urgency feed. */}

            {/* Deliverable 2, step 3: Holdings -- what do I own, in
                detail, ordered so what matters is on top by default. */}
            <Inline gap="inter-section" wrap align="start">
              <div style={{ flex: "3 1 480px", minWidth: 0 }}>
                <HoldingsTable
                  view={status.view}
                  cockpit={cockpit}
                  fitByTicker={fitByTicker}
                  stanceByTicker={stanceByTicker}
                  stanceViewByTicker={stanceViewByTicker}
                  caseCreateStatus={caseCreateStatus}
                  openInvestmentCase={openInvestmentCase}
                  onOpenEditPortfolio={openReplaceForm}
                  t={t}
                />
              </div>
              {/* Deliverable 2, step 4: Allocation / Concentration --
                  paired beside Holdings rather than stacked below it, so
                  "what do I own" and "where is it concentrated" read
                  together in one glance. */}
              <div style={{ flex: "1 1 260px", minWidth: 0 }}>
                <PortfolioSidebar
                  view={status.view}
                  holdingsByWeightDesc={holdingsByWeightDesc}
                  coveredCount={coveredCount}
                  unallocatedPercent={unallocatedPercent}
                  t={t}
                />
              </div>
            </Inline>

            {/* Phase 6D-3: Portfolio Opportunities / Portfolio Weaknesses
                -- one editorial section per direction, replacing the old
                four-column Portfolio Fit overview and the separate
                Weakest Holdings section, all from the one already-
                sorted `/api/portfolio-fit/holdings` fetch, the same
                engine Investment Case and Discovery read. Never a
                buy/sell recommendation. */}
            <PortfolioOpportunitiesSection status={portfolioFitHoldings} onOpenCase={openInvestmentCase} navigate={navigate} t={t} />

            <PortfolioWeaknessesSection
              holdings={status.view.holdings}
              cockpit={cockpit}
              fitByTicker={fitByTicker}
              openInvestmentCase={openInvestmentCase}
              navigate={navigate}
              t={t}
            />

            {/* Phase 6E (Product Simplification): Recent Activity was
                removed entirely -- a plain Decision/Outcome/Trade log
                does not itself help today's investment decisions, and
                Atlas's real activity history remains fully accessible
                on its own dedicated History page. This portfolio-local
                preview of it is gone, not hidden; nothing about History
                itself changed. */}

            {/* Deliverable 2, step 6 / Deliverable 11: Watchlist
                relationship -- entry points only, no duplicated
                Watchlist functionality on this page. */}
            <WatchlistRelationshipSection t={t} />
          </Stack>
        )}
      </Stack>
    </Container>
  );
}

/**
 * Portfolio Workspace v1 -- the first-run "getting started" screen,
 * matching the approved `portfolio-empty-state` frame. Three real
 * affordances only: import (routes to the existing import flow),
 * try-with-sample (out of scope -- no sample-portfolio seeding exists
 * anywhere in this backend, so the button stays disabled rather than
 * silently doing nothing), and three explanatory steps describing what
 * happens after import, using this workspace's own real vocabulary
 * (verify / understand / attention) rather than the Figma wizard's own
 * screen names, since that four-step wizard is out of scope for this
 * sprint (see PortfolioPage.tsx module notes).
 */
function PortfolioEmptyState({ view, t }: { view: PortfolioView; t: (key: TranslationKey, params?: Record<string, string | number>) => string }) {
  return (
    <Surface tier="primary">
      <Stack gap="inter-section">
        <Stack gap="metadata">
          <Label>{t("portfolio.empty.eyebrow")}</Label>
          <Heading level={2}>{t("portfolio.empty.heading")}</Heading>
          <Text color="secondary">{t("portfolio.empty.subheading")}</Text>
        </Stack>
        <Inline gap="row" wrap>
          <RouterLink to="/portfolio/import">
            <Button variant="primary">{t("portfolio.empty.importButton")}</Button>
          </RouterLink>
          <Button variant="tertiary" disabled title={t("portfolio.holdingDetail.dismissUnavailable")}>
            {t("portfolio.empty.trySample")}
          </Button>
        </Inline>
        {view.objective && <Text color="secondary">{t("portfolio.empty.objective", { value: view.objective })}</Text>}
        {view.horizon && <Text color="secondary">{t("portfolio.empty.horizon", { value: view.horizon })}</Text>}
        <Divider tone="hairline" />
        <Inline gap="inter-section" wrap>
          <div style={{ flex: "1 1 200px", minWidth: 0 }}>
            <Stack gap="metadata">
              <Text as="p" style={{ fontWeight: 600 }}>
                {t("portfolio.empty.step.verify.title")}
              </Text>
              <Text as="p" color="secondary">
                {t("portfolio.empty.step.verify.body")}
              </Text>
            </Stack>
          </div>
          <div style={{ flex: "1 1 200px", minWidth: 0 }}>
            <Stack gap="metadata">
              <Text as="p" style={{ fontWeight: 600 }}>
                {t("portfolio.empty.step.understand.title")}
              </Text>
              <Text as="p" color="secondary">
                {t("portfolio.empty.step.understand.body")}
              </Text>
            </Stack>
          </div>
          <div style={{ flex: "1 1 200px", minWidth: 0 }}>
            <Stack gap="metadata">
              <Text as="p" style={{ fontWeight: 600 }}>
                {t("portfolio.empty.step.attention.title")}
              </Text>
              <Text as="p" color="secondary">
                {t("portfolio.empty.step.attention.body")}
              </Text>
            </Stack>
          </div>
        </Inline>
      </Stack>
    </Surface>
  );
}

/** Visual Fidelity Pass -- compact page title, shared by every non-
 * primary state (loading/error/not-established/empty). The primary
 * "loaded with holdings" state instead renders its title inline with
 * the header stat row (`PortfolioHeaderBar` below), matching Figma's
 * single-row title+stats layout.
 *
 * Product Simplification Sprint 6E, Phase 2 -- the header offers
 * exactly one portfolio-management action, context-appropriate: a
 * portfolio that already has holdings gets "Edit Portfolio" (opens the
 * one add/remove/increase/decrease panel, no navigation away); a
 * portfolio that does not yet exist still gets the real first-time
 * setup flow ("Import Portfolio"), a genuinely different action
 * (establishing a portfolio, not editing one). */
function PageTitle({
  hasHoldings,
  onEditPortfolio,
  t,
}: {
  hasHoldings: boolean;
  onEditPortfolio: () => void;
  t: (key: TranslationKey) => string;
}) {
  return (
    <Inline gap="row" align="baseline" wrap>
      <Heading level={3} style={PAGE_TITLE_STYLE}>
        {t("portfolio.title")}
      </Heading>
      {hasHoldings ? (
        <Link
          href="#"
          style={ACCENT_LINK_STYLE}
          onClick={(event) => {
            event.preventDefault();
            onEditPortfolio();
          }}
        >
          {t("portfolio.editPortfolio.button")}
        </Link>
      ) : (
        <RouterLink to="/portfolio/import" style={ACCENT_LINK_STYLE}>
          {t("portfolioImport.title")}
        </RouterLink>
      )}
    </Inline>
  );
}

/** Implementation Sprint B2 (Hero Reordering): the page's own title and
 * operational status notes, factored out of `PortfolioPulse` (which
 * used to bundle them with the stats card) so they can stay pinned at
 * the very top of the page while the stats card itself -- Decision
 * First's own "Portfolio health" step -- moves down to make room for
 * Atlas's conclusion above it. A page's own heading is chrome, not a
 * hero fact; it was never meant to travel with whichever card happened
 * to render first. Unchanged content, unchanged components -- `Page
 * Title` above still exists for the empty/loading states, which never
 * reach `PortfolioPulse` at all. */
function PortfolioPageHeader({
  monitoringStatus,
  hasHoldings,
  onEditPortfolio,
  t,
}: {
  monitoringStatus: MonitoringOperationalStatusView | null;
  hasHoldings: boolean;
  onEditPortfolio: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Stack gap="metadata">
      <PageTitle hasHoldings={hasHoldings} onEditPortfolio={onEditPortfolio} t={t} />
      {monitoringStatus && <MonitoringFreshnessNote status={monitoringStatus} t={t} />}
      {monitoringStatus && (
        <ScopeFreshnessSummaryNote summary={monitoringStatus.portfolioFreshness} scopeKey="monitoring.freshnessSummary.scope.portfolio" t={t} />
      )}
    </Stack>
  );
}

const PAGE_TITLE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.02em",
};

/**
 * Figma-fidelity rebuild, Visual Fidelity Pass -- title and the header
 * stat row (`atlas-portfolio-redesign`) share a single line: page title
 * on the left, Holdings / Cash / Unallocated / Expected Return / Action
 * Required on the right, no card chrome, no "Portfolio Summary" heading
 * (the Figma screen has none). "Action Required" reads
 * `PortfolioCockpitView.priorityReviewCount` -- an already-real,
 * dedicated count of holdings in `priority_review` state, not a second
 * count recomputed a different way from the priority strip's own
 * action list. Expected Return has no real source (scenario valuation
 * remains structurally locked -- `UnavailableCapability
 * (NOT_YET_IMPLEMENTED)`) and renders the same literal "—" every other
 * missing value on this page uses, never a fabricated percentage.
 */
/**
 * Portfolio Pulse (Product Sprint 8, Deliverable 3 -- Portfolio Status)
 * -- the top-of-page status line: total value, largest position,
 * Atlas coverage, and the same `biggestOpportunity`/`biggestRisk`
 * tickers `TodaysBiggestRiskOpportunity` shows in full just below --
 * a compact mention here, the real reasoning there, never the same
 * sentence twice. Every value here is either read verbatim off the
 * already-fetched `PortfolioView` or a plain, undisputed derivation
 * over it. No health score, grade, or synthetic risk score -- only
 * real counts and real values, honestly disclosed as unavailable
 * where they are. "Covered" is defined as any holding whose real
 * `AnalysisCoverageLevel` is not `no_coverage` -- a holding the
 * cockpit hasn't resolved at all does not count as covered either.
 * Sector Allocation has no real per-holding source anywhere in this
 * codebase (grepped: no `sector` field exists on any company/holding
 * model) and is deliberately not rendered here or anywhere else on
 * this page.
 *
 * Alpha Integration Fix (One Product Pass): the Agenda-sourced
 * "Attention Items" figure and critical-item pill are gone. That
 * count duplicated Daily Brief's own "what changed" job on a page
 * whose own doctrine is "what do I own" (Alpha Product Integration
 * Review, Phase 8) -- Concentration/Holdings/Cash live in the Hero
 * above this card.
 */
function PortfolioPulse({
  view,
  largestHolding,
  coveredCount,
  biggestRisk,
  biggestOpportunity,
  t,
}: {
  view: PortfolioView;
  largestHolding: HoldingView | null;
  coveredCount: number | null;
  biggestRisk: PortfolioFitAssessmentView | null;
  biggestOpportunity: PortfolioFitAssessmentView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Stack gap="metadata">
      <Surface tier="primary">
        <Inline gap="inter-section" wrap style={{ justifyContent: "space-between" }}>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.totalValueLabel")}</Label>
            <Text as="span" style={{ fontSize: "var(--type-heading-3-size, 1.5rem)", fontWeight: 700 }}>
              {view.totalValue !== null ? view.totalValue : t("portfolio.pulse.totalValueUnavailable")}
            </Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.largestPositionLabel")}</Label>
            <Text as="span">
              {largestHolding
                ? t("portfolio.pulse.largestPositionValue", {
                    ticker: largestHolding.ticker,
                    percent: largestHolding.weightPercent,
                  })
                : t("portfolio.header.notAvailable")}
            </Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.coverageLabel")}</Label>
            <Text as="span">
              {coveredCount !== null
                ? t("portfolio.pulse.coverageValue", { covered: coveredCount, total: view.numberOfHoldings })
                : t("portfolio.header.notAvailable")}
            </Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.todaysFocus.biggestOpportunityLabel")}</Label>
            <Text as="span">{biggestOpportunity ? biggestOpportunity.ticker : t("portfolio.header.notAvailable")}</Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.todaysFocus.biggestRiskLabel")}</Label>
            <Text as="span">{biggestRisk ? biggestRisk.ticker : t("portfolio.header.notAvailable")}</Text>
          </Stack>
        </Inline>
      </Surface>
    </Stack>
  );
}

/**
 * Concentration / Allocation / Atlas Coverage sidebar (Product Sprint 8,
 * Deliverables 7 & 8). Top-N by weight and the concentration level are
 * both read from data `PortfolioPage` already computed/fetched once and
 * passed down -- never recomputed here (this used to independently
 * re-sort `view.holdings` a second time; see this file's own
 * "computed once here" note where `holdingsByWeightDesc` is built).
 * Reuses the exact same backend `concentrationLevel` the Pulse card
 * shows, with one added plain-language sentence explaining *why*
 * concentration matters (Deliverable 7's own explicit ask) -- never a
 * second, re-derived concentration judgment. Allocation is cash +
 * unallocated only, both already-known real values (or honestly marked
 * unavailable) -- never an inferred split. Sector Allocation stays a
 * deliberate, explained omission: no `sector` field exists on any
 * company/holding model anywhere in this codebase.
 */
const CONCENTRATION_TOP_N = 3;

function PortfolioSidebar({
  view,
  holdingsByWeightDesc,
  coveredCount,
  unallocatedPercent,
  t,
}: {
  view: PortfolioView;
  holdingsByWeightDesc: HoldingView[];
  coveredCount: number | null;
  unallocatedPercent: number | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const topHoldings = holdingsByWeightDesc.slice(0, CONCENTRATION_TOP_N);
  const topWeightSum = Math.round(topHoldings.reduce((sum, h) => sum + h.weightPercent, 0) * 10) / 10;

  return (
    <Stack gap="inter-section">
      <Surface tier="primary">
        <Stack gap="metadata">
          <Label>{t("portfolio.concentrationSummary.heading")}</Label>
          <Text color="secondary" as="p">
            {t("portfolio.concentrationSummary.subheading", { count: topHoldings.length, percent: topWeightSum })}
          </Text>
          <Text color="tertiary" as="p">
            {t("portfolio.concentrationSummary.explainer")}
          </Text>
          <Stack gap="row">
            {topHoldings.map((holding, index) => (
              <Inline key={holding.ticker} gap="row" style={{ justifyContent: "space-between" }}>
                <Text as="span">
                  {index + 1}. {holding.ticker}
                </Text>
                <Text as="span" color="secondary">
                  {holding.weightPercent}%
                </Text>
              </Inline>
            ))}
          </Stack>
        </Stack>
      </Surface>
      <Surface tier="primary">
        <Stack gap="metadata">
          <Label>{t("portfolio.allocation.heading")}</Label>
          <Inline gap="row" style={{ justifyContent: "space-between" }}>
            <Text as="span" color="secondary">
              {t("portfolio.allocation.cashLabel")}
            </Text>
            <Text as="span">
              {view.cashValueAbsolute !== null
                ? view.cashValueAbsolute
                : view.cashWeightPercent !== null
                  ? `${view.cashWeightPercent}%`
                  : t("portfolio.header.notAvailable")}
            </Text>
          </Inline>
          <Inline gap="row" style={{ justifyContent: "space-between" }}>
            <Text as="span" color="secondary">
              {t("portfolio.allocation.unallocatedLabel")}
            </Text>
            <Text as="span">
              {unallocatedPercent !== null ? `${Math.round(unallocatedPercent * 10) / 10}%` : t("portfolio.header.notAvailable")}
            </Text>
          </Inline>
        </Stack>
      </Surface>
      <Surface tier="primary">
        <Stack gap="metadata">
          <Label>{t("portfolio.sectorAllocation.heading")}</Label>
          <Text color="tertiary" as="p">
            {t("portfolio.sectorAllocation.unavailable")}
          </Text>
        </Stack>
      </Surface>
      {coveredCount !== null && (
        <Surface tier="primary">
          <Inline gap="row" align="baseline" wrap>
            <StatusBadge label={t("portfolio.coverageActive.title")} tone="positive" />
            <Text color="secondary" as="span">
              {t("portfolio.coverageActive.body", { covered: coveredCount, total: view.numberOfHoldings })}
            </Text>
          </Inline>
        </Surface>
      )}
    </Stack>
  );
}

/** Figma-fidelity rebuild -- rows shown before "View All Holdings"
 * expands the table, matching the approved screen's own "Showing 15 of
 * 25" / "View All Holdings (25)" pattern. Purely a display cap over
 * data already fully fetched -- no second request, no backend change. */
const HOLDINGS_PAGE_SIZE = 15;

/**
 * Holdings Table (Figma-fidelity rebuild) -- columns now match the
 * approved screen's real target set exactly: Ticker / Weight /
 * Conviction / Fit / Exp. Return / Upside / Downside / Risk / Action.
 * The previous Status/Analysis Coverage/Evidence/Priority/Thesis
 * columns are gone, not hidden -- Analysis Coverage in particular stays
 * reachable on the Investment Case page (its own "Evidence Quality"
 * section), so dropping it here is a placement change, not a loss of
 * the underlying distinction (Migration Review §9's regression note).
 *
 * Fit/Exp. Return/Upside/Downside have no real source yet (scenario
 * valuation remains `UnavailableCapability(NOT_YET_IMPLEMENTED)`) and
 * render the literal "—" every missing value on this page already
 * uses -- never a fabricated number. Action renders the real Decision
 * Support badge (`atlas.alpha.decision_support`, one of seven
 * evidence-support states) -- never the imperative HOLD/ADD/REVIEW/TRIM
 * pill the approved screen shows; Decision Log #1's evidence-support-
 * only language overrides that literal wording (approved exception).
 *
 * **Row click is plain route navigation, not a true overlay.** Clicking
 * a row (or pressing Enter/Space on it) calls the same
 * `openInvestmentCase` this page has always used -- a `navigate()` to
 * `/investment-case/:id` with `state: { origin: "portfolio" }`, giving a
 * "← Back to Portfolio" link on the Case page. Making Investment Case
 * open as a true overlay so that closing it restores this exact
 * Portfolio scroll/expansion state remains explicit, planned follow-up
 * work for a future sprint -- out of scope here.
 */
/**
 * Portfolio Hero (Alpha Integration Fix, One Product Pass) -- one
 * visual block answering Portfolio's own doctrine question first:
 * "what do I own." The opening sentence states ownership scale
 * (holdings count); Concentration and Cash sit directly beneath it in
 * the same card. This Hero used to lead with an attention-count
 * verdict synthesized from the shared Daily Brief Agenda -- the Alpha
 * Product Integration Review's Phase 5 finding was that this quietly
 * repositioned Portfolio's own opening moment toward "what needs
 * attention," which is Daily Brief's job, not Portfolio's. No new
 * computation -- `numberOfHoldings`/`concentrationLevel`/cash are the
 * same `PortfolioView` fields the Executive Summary Strip below
 * already reads.
 */
function PortfolioHero({
  view,
  t,
}: {
  view: PortfolioView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const cashDisplay =
    view.cashValueAbsolute !== null
      ? view.cashValueAbsolute
      : view.cashWeightPercent !== null
        ? `${view.cashWeightPercent}%`
        : t("portfolio.header.notAvailable");

  return (
    <Surface tier="elevated">
      <Stack gap="metadata">
        <Text
          as="p"
          style={{
            fontFamily: "var(--type-family-display)",
            fontSize: "var(--type-size-h3)",
            lineHeight: "var(--type-heading-line-height)",
            color: "var(--color-text-primary)",
          }}
        >
          {t(
            view.numberOfHoldings === 1 ? "portfolio.overallConclusion.ownershipOne" : "portfolio.overallConclusion.ownershipOther",
            { count: view.numberOfHoldings },
          )}
        </Text>
        <Inline gap="inter-section" wrap>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.concentrationLabel")}</Label>
            <Text as="span">
              {view.concentrationLevel && CONCENTRATION_LEVEL_KEY[view.concentrationLevel]
                ? t(CONCENTRATION_LEVEL_KEY[view.concentrationLevel]!)
                : t("portfolio.header.notAvailable")}
            </Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.holdingsLabel")}</Label>
            <Text as="span">{t("portfolio.pulse.holdingsCount", { count: view.numberOfHoldings })}</Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.cashLabel")}</Label>
            <Text as="span">{cashDisplay}</Text>
          </Stack>
        </Inline>
      </Stack>
    </Surface>
  );
}

/**
 * Alpha Integration Fix (One Product Pass): "Today's Story" and
 * "Attention Required" -- Portfolio's own priority-ranked re-surfacing
 * of the shared Daily Brief Agenda -- are removed. Both duplicated
 * Daily Brief's own "what changed" job outright (Alpha Product
 * Integration Review, Phase 8); `TodaysBiggestRiskOpportunity` below
 * remains as Portfolio's one legitimate, Fit-derived read of "what's
 * most notable in what I own" and `PortfolioWeaknessesSection` further
 * down remains as the "worth a second look" surface, both using
 * Portfolio's own signals rather than Daily Brief's urgency feed.
 */

/**
 * Redesign From Zero Sprint V2 -- "Today's Biggest Risk" / "Today's
 * Biggest Opportunity": the single weakest-fit and single best-fit
 * holding, each with its own real `overallReasoning[0]` sentence,
 * side by side. Reads the exact same server-sorted (best-first)
 * `PortfolioFitAssessmentView[]` `PortfolioFitOverviewSection` already
 * renders in full further down this page -- this is a one-entry
 * preview of that same real ranking, not a second computation. Renders
 * nothing when fewer than two holdings have been evaluated (nothing
 * true and distinct to say yet), never a fabricated placeholder.
 */
/**
 * Portfolio Redesign V1 -- "Today's Biggest Risk" / "Today's Biggest
 * Opportunity", mirrored: each card now states why (the real Portfolio
 * Fit reasoning), what changed (the same real Agenda signal the
 * Holdings Table's own "Change" column reads, looked up by the same
 * `agendaItemByTicker` map -- omitted honestly when nothing has
 * changed for that ticker), and one explicit action link, rather than
 * a ticker and a single sentence. `biggestOpportunity`/`biggestRisk`
 * are computed once in the parent and shared with the Executive
 * Summary Strip's own compact mention of the same two tickers -- this
 * component never re-selects them.
 */
function TodaysRiskOpportunityCard({
  label,
  assessment,
  agendaItem,
  onOpenCase,
  t,
}: {
  label: string;
  assessment: PortfolioFitAssessmentView;
  agendaItem: AgendaItemView | undefined;
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="elevated">
      <Stack gap="metadata">
        <Label>{label}</Label>
        <Text as="span" style={{ fontWeight: 600, fontSize: "var(--type-size-h5)" }}>
          {assessment.ticker}
        </Text>
        {assessment.overallReasoning[0] && <Text as="p" color="secondary">{assessment.overallReasoning[0]}</Text>}
        <Text as="p" color="tertiary">
          {t("portfolio.todaysFocus.whatChangedLabel")}:{" "}
          {agendaItem && realHeadlineText(agendaItem, t) !== null
            ? realHeadlineText(agendaItem, t)
            : t("watchlist.attention.noSignificantChanges")}
        </Text>
        <div>
          <Link
            href="#"
            style={{ color: "var(--global-color-accent)" }}
            onClick={(event) => {
              event.preventDefault();
              onOpenCase(assessment.ticker, assessment.caseId);
            }}
          >
            {t("dailyBriefAgenda.action.openInvestmentCase")} →
          </Link>
        </div>
      </Stack>
    </Surface>
  );
}

function TodaysBiggestRiskOpportunity({
  biggestOpportunity,
  biggestRisk,
  agendaItemByTicker,
  onOpenCase,
  t,
}: {
  biggestOpportunity: PortfolioFitAssessmentView | null;
  biggestRisk: PortfolioFitAssessmentView | null;
  agendaItemByTicker: Map<string, AgendaItemView>;
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (!biggestOpportunity || !biggestRisk) return null;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "var(--space-row)",
      }}
    >
      <TodaysRiskOpportunityCard
        label={t("portfolio.todaysFocus.biggestOpportunityLabel")}
        assessment={biggestOpportunity}
        agendaItem={agendaItemByTicker.get(biggestOpportunity.ticker)}
        onOpenCase={onOpenCase}
        t={t}
      />
      <TodaysRiskOpportunityCard
        label={t("portfolio.todaysFocus.biggestRiskLabel")}
        assessment={biggestRisk}
        agendaItem={agendaItemByTicker.get(biggestRisk.ticker)}
        onOpenCase={onOpenCase}
        t={t}
      />
    </div>
  );
}

/**
 * Portfolio Lower-Half Reconstruction Sprint 6D (Phase 3) -- "Portfolio
 * Opportunities": the positive-direction half of what used to be four
 * separate `FitGroupColumn` lists (Best Fit / Weakest Fit / Improved /
 * Worsened) plus a fifth, richer `WeakestHoldingsSection` -- one
 * editorial section per direction (Opportunities here, Weaknesses just
 * below) instead of two overlapping analytical modules. A holding
 * qualifies by fit rating (good/excellent) or by trend (improving,
 * Change Intelligence's own real signal) -- either is real, already-
 * computed evidence that this position currently looks more
 * attractive, never a buy signal on its own. Same server-sorted
 * (best-first) data `PortfolioFitOverviewSection` always read; no new
 * fetch, no new fit computation.
 */
const OPPORTUNITY_FIT_RATINGS: FitRating[] = ["excellent", "good"];
const PORTFOLIO_SIGNAL_CAP = 6;

function PortfolioOpportunitiesSection({
  status,
  onOpenCase,
  navigate,
  t,
}: {
  status: PortfolioFitFetchStatus;
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
  navigate: ReturnType<typeof useNavigate>;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (status.kind === "loading") {
    return (
      <Text role="status" aria-live="polite">
        {t("portfolioFit.section.loading")}
      </Text>
    );
  }
  if (status.kind === "error" || status.assessments.length === 0) {
    return (
      <Stack gap="metadata">
        <Heading level={2}>{t("portfolio.opportunities.heading")}</Heading>
        <Text color="tertiary">{t("portfolioFit.portfolioSection.empty")}</Text>
      </Stack>
    );
  }

  const candidates = status.assessments
    .filter((a) => OPPORTUNITY_FIT_RATINGS.includes(a.overall) || a.trend === "improving")
    .sort((a, b) => (b.currentWeightPercent ?? 0) - (a.currentWeightPercent ?? 0))
    .slice(0, PORTFOLIO_SIGNAL_CAP);

  if (candidates.length === 0) {
    return (
      <Stack gap="metadata">
        <Heading level={2}>{t("portfolio.opportunities.heading")}</Heading>
        <Text color="tertiary">{t("portfolioFit.portfolioSection.empty")}</Text>
      </Stack>
    );
  }

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("portfolio.opportunities.heading")}</Heading>
      <Stack gap="row">
        {candidates.map((assessment) => (
          <PortfolioSignalCard
            key={assessment.caseId}
            ticker={assessment.ticker}
            weightPercent={assessment.currentWeightPercent}
            fit={assessment}
            decisionSupport={null}
            caseId={assessment.caseId}
            onOpenCase={onOpenCase}
            navigate={navigate}
            t={t}
          />
        ))}
      </Stack>
    </Stack>
  );
}

/** Shared by Portfolio Opportunities and Portfolio Weaknesses -- the
 * one compact editorial card both sections render, so a company's
 * fit/decision-support signals and its real actions (Compare
 * alternatives, Open Investment Case) always look identical regardless
 * of which direction placed it there. Alpha Integration Fix (One
 * Product Pass): the former "Review position" link to the Holding
 * Attention waypoint page is gone -- it duplicated Investment Case's
 * own job one click further away (Alpha Product Integration Review,
 * Phase 1). "Open Investment Case" now always navigates directly,
 * creating a Case first if this holding doesn't have one yet. */
function PortfolioSignalCard({
  ticker,
  weightPercent,
  fit,
  decisionSupport,
  caseId,
  onOpenCase,
  navigate,
  t,
}: {
  ticker: string;
  weightPercent: number | null;
  fit: PortfolioFitAssessmentView | null;
  decisionSupport: { level: DecisionSupportLevel } | null;
  caseId: string | null;
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
  navigate: ReturnType<typeof useNavigate>;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
          <Text as="span" style={{ fontWeight: 600 }}>
            {ticker}
          </Text>
          {weightPercent !== null && (
            <Text as="span" color="secondary">
              {weightPercent}%
            </Text>
          )}
        </Inline>
        <Inline gap="row" wrap>
          {fit && fit.overall !== "unavailable" && <FitBadge rating={fit.overall} />}
          {decisionSupport && (
            <StatusBadge
              label={t(DECISION_SUPPORT_BADGE_KEY[decisionSupport.level])}
              tone={DECISION_SUPPORT_TONE[decisionSupport.level]}
            />
          )}
        </Inline>
        <Inline gap="row" wrap>
          <Link
            href="#"
            style={{ color: "var(--global-color-accent)" }}
            onClick={(event) => {
              event.preventDefault();
              navigate(`/discovery/compare?a=${encodeURIComponent(ticker)}`);
            }}
          >
            {t("portfolio.weakestHoldings.compareAlternatives")} →
          </Link>
          <Link
            href="#"
            style={{ color: "var(--global-color-accent)" }}
            onClick={(event) => {
              event.preventDefault();
              onOpenCase(ticker, caseId);
            }}
          >
            {t("dailyBriefAgenda.action.openInvestmentCase")} →
          </Link>
        </Inline>
      </Stack>
    </Surface>
  );
}

const HOLDING_SORT_KEYS: HoldingSortKey[] = ["weight", "fit", "coverage", "stance", "alphabetical"];

const HOLDING_SORT_LABEL_KEY: Record<HoldingSortKey, TranslationKey> = {
  weight: "portfolio.holdingsTable.sort.weight",
  fit: "portfolio.holdingsTable.sort.fit",
  coverage: "coverage.portfolio.sortLabel",
  stance: "stance.portfolio.sortLabel",
  alphabetical: "portfolio.holdingsTable.sort.alphabetical",
};

function HoldingsTable({
  view,
  cockpit,
  fitByTicker,
  stanceByTicker,
  stanceViewByTicker,
  caseCreateStatus,
  openInvestmentCase,
  onOpenEditPortfolio,
  t,
}: {
  view: PortfolioView;
  cockpit: PortfolioCockpitFetchStatus;
  fitByTicker: Map<string, PortfolioFitAssessmentView>;
  stanceByTicker: Map<string, StanceLevel>;
  stanceViewByTicker: Map<string, StanceView>;
  caseCreateStatus: Record<string, CaseCreateStatus>;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  onOpenEditPortfolio: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const cellStyle: CSSProperties = {
    padding: "var(--space-metadata) var(--space-row)",
    textAlign: "left",
    borderBottom: `var(--width-border-hairline) solid var(--color-border-hairline)`,
    fontFamily: "var(--type-family-metadata)",
    fontVariantNumeric: "tabular-nums",
    fontSize: "var(--type-body-min-size)",
  };
  const headerCellStyle: CSSProperties = {
    ...cellStyle,
    color: "var(--color-text-tertiary)",
    fontWeight: 500,
    fontSize: "11px",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    borderBottom: `var(--width-border-standard) solid var(--color-border-standard)`,
  };

  const [showAllHoldings, setShowAllHoldings] = useState(false);
  /** Alpha Integration Fix (One Product Pass): defaults to "weight"
   * (largest position first) -- Portfolio's own doctrine question is
   * "what do I own," so its default ordering is ownership-scale, not
   * Daily Brief's Agenda-derived urgency ranking (the former "attention"
   * sort key, removed along with the rest of that duplication). The
   * other keys remain cheap client-side re-sorts over data already on
   * the page, no new fetch. */
  const [sortKey, setSortKey] = useState<HoldingSortKey>("weight");
  const fitRatingByTicker = new Map<string, FitRating>();
  for (const [ticker, assessment] of fitByTicker) {
    fitRatingByTicker.set(ticker, assessment.overall);
  }
  /** Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine,
   * Deliverable 6): the "coverage" sort key reuses `cockpit`'s own
   * already-fetched per-holding `analysisCoverage.level` -- no new
   * fetch, matching `fitRatingByTicker`'s own pattern above. */
  const coverageByTicker = new Map<string, AnalysisCoverageLevel>();
  /** Atlas UX Phase 7B, Phase 5 -- same cockpit report, same zero-new-
   * fetch pattern as `coverageByTicker` immediately above: feeds the
   * one compact Investment rating badge the Holdings Table row now
   * shows next to Stance, so a holding reads the same Investment
   * number here as it does on its own Investment Case. */
  const decisionSupportByTicker = new Map<string, DecisionSupportLevel>();
  if (cockpit.kind === "loaded") {
    for (const holding of cockpit.report.holdings) {
      coverageByTicker.set(holding.ticker, holding.analysisCoverage.level);
      decisionSupportByTicker.set(holding.ticker, holding.decisionSupport.level);
    }
  }
  const orderedHoldings = sortHoldings(
    view.holdings,
    sortKey,
    fitRatingByTicker,
    coverageByTicker,
    stanceByTicker,
  );
  const visibleHoldings = showAllHoldings ? orderedHoldings : orderedHoldings.slice(0, HOLDINGS_PAGE_SIZE);

  return (
    <Stack gap="metadata">
      <Heading level={2}>
        <VisuallyHidden>{t("portfolio.holdings.heading")}</VisuallyHidden>
      </Heading>
      {!view.hasAbsoluteValues && (
        <Text color="tertiary" as="p">
          {t("portfolio.holdings.percentOnly")}
        </Text>
      )}
      {view.hasAbsoluteValues && view.totalValue !== null && (
        <Text color="tertiary" as="p">
          {t("portfolio.holdings.totalValue", { value: view.totalValue })}
        </Text>
      )}

      <Inline gap="row" align="center" wrap>
        <Text color="tertiary" as="span">
          {t("portfolio.holdingsTable.sortLabel")}
        </Text>
        {HOLDING_SORT_KEYS.map((key) => (
          <Link
            key={key}
            href="#"
            style={{
              color: sortKey === key ? "var(--global-color-accent)" : "var(--color-text-secondary)",
              fontWeight: sortKey === key ? 600 : 400,
            }}
            aria-current={sortKey === key ? "true" : undefined}
            onClick={(event) => {
              event.preventDefault();
              setSortKey(key);
            }}
          >
            {t(HOLDING_SORT_LABEL_KEY[key])}
          </Link>
        ))}
      </Inline>

      <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {/* Portfolio Lower-Half Reconstruction Sprint 6D (Phase
                    2): four columns -- Company, Atlas view, Reason,
                    Action. Value and Share live inside the Company cell,
                    shown only when genuinely populated -- a portfolio
                    entered as percent-only no longer renders a
                    permanently-empty Value column. Alpha Integration Fix
                    (One Product Pass): the Reason cell now always shows
                    Stance's own steady-state reasoning -- it no longer
                    leads with a real-time Daily Brief Agenda signal,
                    which duplicated Daily Brief's own job. */}
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.tickerHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.currentViewHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.reasonHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.actionHeader")}</th>
              </tr>
            </thead>
            <tbody>
              {visibleHoldings.map((holding) => {
                const isUnresolvedInCockpit =
                  cockpit.kind === "loaded" &&
                  cockpit.report.unresolvedHoldings.some((h) => h.ticker === holding.ticker);

                return (
                  <HoldingsTableRow
                    key={holding.ticker}
                    holding={holding}
                    isUnresolvedInCockpit={isUnresolvedInCockpit}
                    stanceLevel={stanceByTicker.get(holding.ticker)}
                    stanceView={stanceViewByTicker.get(holding.ticker)}
                    investmentLevel={decisionSupportByTicker.get(holding.ticker)}
                    thisCaseCreateStatus={caseCreateStatus[holding.ticker] ?? { kind: "idle" }}
                    openInvestmentCase={openInvestmentCase}
                    onOpenEditPortfolio={onOpenEditPortfolio}
                    cellStyle={cellStyle}
                    t={t}
                  />
                );
              })}
            </tbody>
          </table>
        </div>

        <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
          <Text color="tertiary" as="span">
            {[
              view.holdings.length > HOLDINGS_PAGE_SIZE
                ? t("portfolio.holdingsTable.showingCount", {
                    shown: visibleHoldings.length,
                    total: view.holdings.length,
                  })
                : null,
              view.concentrationLevel
                ? t("portfolio.concentration", {
                    value: CONCENTRATION_LEVEL_KEY[view.concentrationLevel]
                      ? t(CONCENTRATION_LEVEL_KEY[view.concentrationLevel]!)
                      : view.concentrationLevel,
                  })
                : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </Text>
          {view.holdings.length > HOLDINGS_PAGE_SIZE && (
            <Link
              href="#"
              style={{ color: "var(--global-color-accent)" }}
              onClick={(event) => {
                event.preventDefault();
                setShowAllHoldings((current) => !current);
              }}
            >
              {showAllHoldings
                ? t("portfolio.holdingsTable.viewFewer")
                : t("portfolio.holdingsTable.viewAll", { count: view.holdings.length })}
            </Link>
          )}
        </Inline>

        <div>
          <Link
            href="#"
            onClick={(event) => {
              event.preventDefault();
              openInvestmentCase("__new__", null);
            }}
          >
            {t("portfolio.openNewCase")}
          </Link>
        </div>
    </Stack>
  );
}

/**
 * Alpha Integration Fix (One Product Pass) -- the Holdings Table's
 * Reason cell now shows only Stance's own steady-state reasoning
 * sentence. It used to lead with a real-time Daily Brief Agenda signal
 * (Sprint B3's own "Change" column, folded in here) whenever one
 * existed -- the Alpha Product Integration Review's Phase 8 finding was
 * that this made the Holdings Table one of several surfaces on this
 * page independently re-ranking holdings by Daily Brief's own urgency
 * feed. "What changed" belongs on Daily Brief; this cell answers only
 * "why does Atlas hold this view."
 */
function HoldingReasonCell({
  stanceView,
  t,
}: {
  stanceView: StanceView | undefined;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const primaryReason = stanceView ? primaryStanceReason(stanceView) : null;
  const whySentence = primaryReason ? stanceReasonSentence(primaryReason, t) : null;

  if (whySentence) {
    return <Text as="span">{whySentence}</Text>;
  }

  return (
    <Text color="tertiary" as="span">
      {t("portfolio.holdingsTable.coverage.new")}
    </Text>
  );
}

/**
 * One dense, clickable row. `role="button"`/`tabIndex`/`onKeyDown` make
 * the whole row a keyboard-operable navigation target (Enter/Space open
 * the Investment Case) rather than requiring a separate visible button
 * per row -- consistent with "the user should never feel they are
 * leaving the Portfolio workspace" and this sprint's density goal.
 *
 * Phase 6E (Product Simplification): the per-row inline "Reconcile"
 * toggle + its own weight-input form -- a second, competing way to
 * change a holding's weight, alongside the page's own general "Edit
 * Portfolio" action -- is gone. A holding awaiting reconciliation now
 * just says so in plain language and opens the one, same Edit
 * Portfolio panel every other portfolio change goes through.
 */
function HoldingsTableRow({
  holding,
  isUnresolvedInCockpit,
  stanceLevel,
  stanceView,
  investmentLevel,
  thisCaseCreateStatus,
  openInvestmentCase,
  onOpenEditPortfolio,
  cellStyle,
  t,
}: {
  holding: HoldingView;
  isUnresolvedInCockpit: boolean;
  stanceLevel: StanceLevel | undefined;
  stanceView: StanceView | undefined;
  investmentLevel: DecisionSupportLevel | undefined;
  thisCaseCreateStatus: CaseCreateStatus;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  onOpenEditPortfolio: () => void;
  cellStyle: CSSProperties;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const isCreating = thisCaseCreateStatus.kind === "creating";
  const isAwaitingReconciliation = holding.reconciliationStatus === "AWAITING_RECONCILIATION";

  /** Alpha Integration Fix (One Product Pass): a Holdings row now opens
   * the real Investment Case directly, the same fix already made to
   * Watchlist's own row-click. It used to route through Company
   * Workspace first -- a mid-flow waypoint whose own content (Hero,
   * limiting factors, "what changed") duplicates Investment Case
   * outright (Alpha Product Integration Review, Phase 1). Company
   * Workspace itself is unchanged and untouched by this fix. */
  function handleRowActivate() {
    if (isCreating) return;
    openInvestmentCase(holding.ticker, holding.caseId);
  }

  return (
    <>
      <tr
        role="button"
        tabIndex={0}
        aria-label={t("portfolio.holdingsTable.rowAriaLabel", { ticker: holding.ticker })}
        onClick={handleRowActivate}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            handleRowActivate();
          }
        }}
        style={{ cursor: isCreating ? "default" : "pointer" }}
      >
        <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)" }}>
          <Inline gap="metadata" align="baseline" wrap>
            <Text as="span" style={{ fontWeight: 600 }}>
              {holding.ticker}
            </Text>
            <Text as="span" color="tertiary">
              {holding.weightPercent}%
            </Text>
            {/* Real Value, shown only when this portfolio actually has
                one -- a percent-only portfolio (the common case in this
                data) no longer renders a permanently-empty column for
                it. */}
            {holding.valueAbsolute !== null && (
              <Text as="span" color="tertiary">
                {holding.valueAbsolute}
              </Text>
            )}
            {isCreating && (
              <Text as="span" color="tertiary">
                {t("portfolio.holdings.opening")}
              </Text>
            )}
            {holding.reconciliationStatus === "UPDATED" && (
              <Text as="span" color="tertiary">
                {t("portfolio.holdings.updatedAutomatically")}
              </Text>
            )}
            {isUnresolvedInCockpit && (
              <Text as="span" color="tertiary">
                {t("portfolio.cockpit.unresolved")}
              </Text>
            )}
            {thisCaseCreateStatus.kind === "error" && (
              <Text as="span" color="tertiary">
                {t("portfolio.holdings.openCaseError")}
              </Text>
            )}
            {isAwaitingReconciliation && (
              <Link
                href="#"
                style={{ color: "var(--global-color-accent)" }}
                onClick={(event) => {
                  event.stopPropagation();
                  event.preventDefault();
                  onOpenEditPortfolio();
                }}
              >
                {t("portfolio.holdingsTable.needsUpdateLink")}
              </Link>
            )}
          </Inline>
        </td>
        <td style={cellStyle}>
          <Inline gap="metadata" wrap>
            {stanceLevel ? (
              <StanceBadge level={stanceLevel} weight="strong" />
            ) : (
              <Text color="tertiary" as="span">
                {t("portfolio.holdingsTable.coverage.new")}
              </Text>
            )}
            {/* Atlas UX Phase 7B, Phase 5 -- the same Investment rating
                Watchlist's own compact cluster and Investment Case's
                own Seven Categories bar show, so this holding reads the
                same real number wherever it appears. Stance stays the
                primary, leftmost badge (Portfolio's own established
                "what should I do now" signal, unchanged) -- this is an
                addition, not a redesign of the column. */}
            {investmentLevel && <CompactRatingBadge labelKey="investmentCase.ratings.investment.label" rating={deriveInvestmentRating(investmentLevel)} t={t} />}
          </Inline>
        </td>
        <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)", maxWidth: "320px" }} onClick={(event) => event.stopPropagation()}>
          <HoldingReasonCell stanceView={stanceView} t={t} />
        </td>
        <td style={cellStyle}>
          <Link
            href="#"
            style={{ color: "var(--global-color-accent)" }}
            onClick={(event) => {
              event.stopPropagation();
              event.preventDefault();
              handleRowActivate();
            }}
          >
            {t("portfolio.holdingsTable.openAction")}
          </Link>
        </td>
      </tr>
    </>
  );
}

/**
 * Portfolio Lower-Half Reconstruction Sprint 6D (Phase 3) -- "Portfolio
 * Weaknesses": the negative-direction counterpart of Portfolio
 * Opportunities above, replacing what used to be a separate
 * `WeakestHoldingsSection` plus two more `FitGroupColumn`s (Weakest
 * Fit / Worsened) inside the old four-column Portfolio Fit overview --
 * one section instead of two overlapping ones, per this sprint's own
 * "Portfolio Opportunities / Portfolio Weaknesses" instruction. A
 * holding qualifies by fit rating (weak/poor), by Decision Support
 * (`reduction_supported`/`exit_supported` -- the same real,
 * already-existing evidence-support states Investment Case's own badge
 * uses), or by trend (declining) -- three real, already-computed
 * signals, never a new one. Neither this section nor any one signal is
 * a sell recommendation; it only surfaces the evidence and offers
 * investigation ("Review position" / "Compare alternatives" / "Open
 * Investment Case"), never action.
 */
const WEAK_FIT_RATINGS: FitRating[] = ["weak", "poor"];
const WEAK_DECISION_SUPPORT: DecisionSupportLevel[] = ["reduction_supported", "exit_supported"];

function PortfolioWeaknessesSection({
  holdings,
  cockpit,
  fitByTicker,
  openInvestmentCase,
  navigate,
  t,
}: {
  holdings: HoldingView[];
  cockpit: PortfolioCockpitFetchStatus;
  fitByTicker: Map<string, PortfolioFitAssessmentView>;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  navigate: ReturnType<typeof useNavigate>;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (cockpit.kind !== "loaded") return null;

  const candidates = holdings
    .map((holding) => {
      const cockpitHolding = cockpit.report.holdings.find((h) => h.ticker === holding.ticker);
      const fit = fitByTicker.get(holding.ticker);
      const weakFit = fit && (WEAK_FIT_RATINGS.includes(fit.overall) || fit.trend === "declining") ? fit : null;
      const weakDecisionSupport =
        cockpitHolding && WEAK_DECISION_SUPPORT.includes(cockpitHolding.decisionSupport.level)
          ? cockpitHolding.decisionSupport
          : null;
      if (!weakFit && !weakDecisionSupport) return null;
      return { holding, weakFit, weakDecisionSupport };
    })
    .filter((c): c is NonNullable<typeof c> => c !== null)
    .sort((a, b) => b.holding.weightPercent - a.holding.weightPercent)
    .slice(0, PORTFOLIO_SIGNAL_CAP);

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("portfolio.weakestHoldings.heading")}</Heading>
      <Text color="tertiary" as="p">
        {t("portfolio.weakestHoldings.subheading")}
      </Text>
      {candidates.length === 0 && <Text color="secondary">{t("portfolio.weakestHoldings.empty")}</Text>}
      <Stack gap="row">
        {candidates.map(({ holding, weakFit, weakDecisionSupport }) => (
          <PortfolioSignalCard
            key={holding.ticker}
            ticker={holding.ticker}
            weightPercent={holding.weightPercent}
            fit={weakFit}
            decisionSupport={weakDecisionSupport}
            caseId={holding.caseId}
            onOpenCase={openInvestmentCase}
            navigate={navigate}
            t={t}
          />
        ))}
      </Stack>
    </Stack>
  );
}

/**
 * Watchlist Relationship (Product Sprint 8, Deliverable 11) -- entry
 * points only, reusing the existing Watchlist and Discovery routes
 * exactly as they already exist. No Watchlist data is duplicated onto
 * this page; per-holding "compare against an alternative" already lives
 * in Portfolio Weaknesses above and every Holdings Table row, both
 * reusing the same existing Compare route.
 */
function WatchlistRelationshipSection({ t }: { t: (key: TranslationKey) => string }) {
  return (
    <Stack gap="metadata">
      <Label>{t("portfolio.watchlistRelationship.heading")}</Label>
      <Inline gap="row" wrap>
        <RouterLink to="/watchlist" style={ACCENT_LINK_STYLE}>
          {t("portfolio.watchlistRelationship.openWatchlist")} →
        </RouterLink>
        <RouterLink to="/discovery" style={ACCENT_LINK_STYLE}>
          {t("portfolio.watchlistRelationship.openDiscovery")} →
        </RouterLink>
      </Inline>
    </Stack>
  );
}

/**
 * "Today's Discussions" (the page-local Ask Atlas box, Portfolio
 * Workspace v3) was removed in the Workspace Migration, Phase 2
 * (Migration Review Decision Log #2 / §6 / §11.5): every page-local Ask
 * Atlas placeholder is deprecated in favor of the future, persistent,
 * cross-workspace Atlas Companion -- a separate, later, cross-cutting
 * workstream, not part of any single page's migration. Removing this
 * box (rather than reskinning it) is the explicit instruction, not an
 * oversight; `deriveDiscussionPrompts.ts`/`DiscussionPrompt` remain on
 * disk, unused here, as real candidate input for that future build.
 */
