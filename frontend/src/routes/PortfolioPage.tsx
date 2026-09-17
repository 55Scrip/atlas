import { useEffect, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  ACCENT_LINK_STYLE,
  Button,
  Container,
  Divider,
  formatCurrency,
  formatPercentPoints,
  Heading,
  Inline,
  Label,
  Link,
  Stack,
  StatusBadge,
  Surface,
  Text,
  VisuallyHidden,
} from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  ANALYSIS_COVERAGE_LEVEL_KEY,
  ANALYSIS_COVERAGE_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  type AnalysisCoverageLevel,
  type ConvictionLevel,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type ReviewPriority,
} from "../status/statusTone";
import type { StatusTone } from "../foundation";
import {
  RISK_CATEGORY_KEY,
  RISK_STATUS_KEY,
  VALUATION_STATUS_KEY,
  type AnalysisBusinessCategory,
  type AnalysisBusinessStatus,
  type AnalysisRiskStatus,
} from "../changeIntelligence/describeChange";
/** Portfolio Holdings Cockpit v1 -- the Investment Case's own rating
 * derivations and tier vocabulary, imported rather than reimplemented.
 * A second, competing way of turning the same statuses into a number is
 * exactly how two screens end up disagreeing about one holding. */
import {
  deriveCompanyRating,
  deriveInvestmentRating,
  type AtlasRating,
} from "../investmentCase/atlasRatingModel";
import { RATING_TIER_LABEL_KEY } from "../investmentCase/SevenCategoriesSection";
import {
  COCKPIT_COLUMN_HEADER_KEY,
  COCKPIT_COLUMN_LINK_LABEL_KEY,
  cockpitCellHref,
  type CockpitColumnKey,
} from "../portfolioCockpit/cockpitColumns";
import { describeFitVerdict } from "../portfolioFit/describeFitVerdict";
import { FitBadge } from "../portfolioFit/FitBadge";
import { fetchPortfolioFitForHoldings, type PortfolioFitAssessmentView, type FitRating } from "../portfolioFit/portfolioFitApi";
import { fetchStanceForHoldings, type TickerStanceView } from "../stance/stanceApi";
import { StanceBadge } from "../stance/StanceBadge";
import type { StanceLevel } from "../status/statusTone";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { realHeadlineText } from "../dailyBriefAgenda/bookkeepingFilter";
import { MonitoringFreshnessNote } from "../monitoring/MonitoringFreshnessNote";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { invalidateAlphaPortfolio, setAlphaPortfolioData, useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { fetchMonitoringStatus, type MonitoringOperationalStatusView } from "../monitoring/monitoringApi";
import { sortHoldings, type HoldingSortKey } from "../portfolio/sortHoldings";
import styles from "./PortfolioPage.module.css";
import { selectOpportunity } from "../portfolio/opportunityEligibility";
import { reductionExposure, type ReductionExposure } from "../portfolio/reductionExposure";
/** Portfolio Editing & Simulation Layer v1 -- the hypothetical
 * portfolio. One canonical state for the whole page: rows, the
 * allocation summary and the reduction-exposure aggregate all derive
 * from the same `hypothetical`, so none of them can disagree about what
 * the investor is currently exploring. See `simulationModel.ts` for the
 * economic model and the audit that chose it. */
import {
  applyPortfolioEdits,
  availableCapital,
  editStep,
  holdingKey,
  resetPosition,
  resetSimulation,
  setPosition,
  type HypotheticalHolding,
  type HypotheticalPortfolio,
  type PortfolioEdits,
  type PortfolioSimulationBase,
} from "../portfolioSimulation/simulationModel";

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
  /** Portfolio Holdings Cockpit v1 -- the whole already-computed
   * six-category vector. The row derives its Business rating from this
   * with the Investment Case's own `deriveCompanyRating`, so one
   * holding reads the same number on both screens. Deriving it from
   * `business` (Growth + Capital Allocation only) instead produced a
   * different rating for 15 of 25 real holdings. */
  businessCategories?: { kind: AnalysisBusinessCategory; status: AnalysisBusinessStatus }[];
  /** Counts of verified forward evidence, or `null` when the
   * recommendation carries no reasoning. Counts only: never content,
   * never polarity, never a forecast. */
  forwardEvidence?: { guidanceCount: number; contractedVolumeCount: number } | null;
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
  /* Portfolio Editing & Simulation Layer v1 -- see the derivation
     below. Hypothetical only: no persistence, no trade, no Decision
     Memory. */
  const [edits, setEdits] = useState<PortfolioEdits>({});
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

  /** Product Sprint 8 (Portfolio Excellence): weight-sorted holdings and
   * the Cockpit coverage count were previously each computed twice
   * independently (once in `PortfolioPulse`, once in `PortfolioSidebar`)
   * over the exact same source data -- the same duplication risk this
   * sprint's own Deliverable 16 flags. Computed once here instead and
   * passed down, so the two can never quietly disagree. */
  /* Portfolio Editing & Simulation Layer v1.
   *
   * `edits` is the entire hypothetical state: absolute target values
   * keyed by holding identity. Everything else is derived, so there is
   * nothing to keep in sync and nothing to drift. It lives here, at the
   * page, because rows, the allocation summary and the reduction
   * aggregate must all read one hypothetical portfolio rather than
   * three.
   *
   * Deliberately not persisted anywhere -- not to the portfolio, not to
   * local storage, not to the URL. A reload returns the real portfolio,
   * which is the clearest possible statement that nothing explored here
   * was an action. */
  const simulationHoldings = status.kind === "loaded" ? status.view.holdings : [];
  /* The editable quantum. `valueAbsolute` when the portfolio carries
     real values -- it does for all 25 real holdings -- and otherwise
     the weight itself, so a percent-only portfolio stays editable
     without inventing money it never stated. The model only conserves a
     total, so it is honest either way; only the unit the UI renders
     differs. */
  const simulationUsesValue = status.kind === "loaded" && status.view.hasAbsoluteValues;
  const simulationBase: PortfolioSimulationBase = {
    holdings: simulationHoldings.map((holding) => ({
      ticker: holding.ticker,
      caseId: holding.caseId,
      valueAbsolute: simulationUsesValue ? (holding.valueAbsolute ?? 0) : holding.weightPercent,
      currency: null,
    })),
    /* Base unallocated capital, in the same quantum as the positions.
       In the value path that is the investor's own stated cash, which
       is null for the real portfolio and so contributes nothing.
       In the percent-only path it is deliberately zero: there the
       quantum *is* the weight, weights already sum to 100, and adding a
       separately-stated cash weight on top would renormalize every
       holding and change displayed weights with no edit made. Freed
       weight still becomes unallocated -- inside the same 100. */
    unallocatedValue:
      status.kind === "loaded" && simulationUsesValue ? (status.view.cashValueAbsolute ?? 0) : 0,
  };
  const hypothetical = applyPortfolioEdits(simulationBase, edits);
  const hypotheticalByKey = new Map(hypothetical.holdings.map((h) => [h.key, h]));

  /* One canonical state, read by everything that participates in the
     simulation. `holdings` below is the *hypothetical* holdings list,
     so largest position, the concentration summary and the allocation
     card cannot quietly disagree with the rows about what the investor
     is exploring. Only position-derived facts change: nothing here
     re-derives an analytical verdict. */
  const persistedHoldings = status.kind === "loaded" && status.view.exists ? status.view.holdings : [];
  const holdings: HoldingView[] = persistedHoldings.map((holding) => {
    const simulated = hypotheticalByKey.get(holdingKey(holding));
    if (!simulated) return holding;
    return {
      ...holding,
      weightPercent: simulated.hypotheticalWeightPercent,
      valueAbsolute: simulationUsesValue ? simulated.hypotheticalValue : holding.valueAbsolute,
    };
  });
  const holdingsByWeightDesc = [...holdings].sort((a, b) => b.weightPercent - a.weightPercent);
  /* Unallocated capital, from the same hypothetical portfolio. It was
     `100 - sum(weights) - cash` over the persisted holdings, which is
     exactly what `unallocatedWeightPercent` already is once freed
     capital is included -- so this reads it rather than recomputing a
     second, divergent answer. With no edits the two are identical, and
     the Allocation card reads as it always did. */
  const unallocatedPercent =
    status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0
      ? hypothetical.unallocatedWeightPercent
      : null;
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
  /** Portfolio Opportunity / Action Consistency: the opportunity headline
   * used to be `fitEvaluated[0]` -- the best Portfolio Fit and nothing
   * else -- which announced ASSA-B as "today's biggest opportunity" while
   * its own Case said there was nothing to act on. Fit says how well a
   * holding suits the portfolio; only the Decision Layer says whether
   * Atlas supports doing anything. Eligibility now reads that, and fit
   * only orders the holdings that pass. Risk selection is unchanged. */
  const decisionSupportForHeadline = new Map<string, DecisionSupportLevel>();
  if (cockpit.kind === "loaded") {
    for (const holding of cockpit.report.holdings) {
      if (holding.decisionSupport) {
        decisionSupportForHeadline.set(holding.ticker, holding.decisionSupport.level);
      }
    }
  }
  const opportunity = selectOpportunity(fitEvaluated, decisionSupportForHeadline);
  /** Portfolio Reduction-Exposure Aggregation: each row already says
   * "Reduction supported" and each Case agrees, but the share of the
   * portfolio they add up to was never stated, so reading it meant
   * scanning for one enum and adding weights by hand. Counts what the
   * Decision Layer already published; decides nothing. */
  /** Portfolio Reduction-Exposure Aggregation: each row already says
   * "Reduction supported" and each Case agrees, but the share of the
   * portfolio they add up to was never stated, so reading it meant
   * scanning for one enum and adding weights by hand. Counts what the
   * Decision Layer already published; decides nothing.
   *
   * Simulation v1: fed the *hypothetical* weights. This is the one
   * aggregate safe to recompute here, because it is arithmetic over a
   * weight and an already-published `decisionSupport` level -- no
   * analytical conclusion is re-derived, and the level itself is read
   * verbatim from the cockpit report. Reduce a reduction-supported
   * holding and the exposure falls; remove it and its weight leaves the
   * total entirely. */
  const reduction = reductionExposure(
    cockpit.kind === "loaded"
      ? cockpit.report.holdings.map((holding) => {
          const simulated = hypotheticalByKey.get(holdingKey(holding));
          return simulated ? { ...holding, weightPercent: simulated.hypotheticalWeightPercent } : holding;
        })
      : [],
  );
  const biggestOpportunity = opportunity.holding;
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
  for (const entry of stanceEntries) {
    stanceByTicker.set(entry.ticker, entry.stance.level);
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
            <ReductionExposureNote exposure={reduction} t={t} />
            <TodaysBiggestRiskOpportunity
              opportunityKind={opportunity.kind}
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
              {/* Portfolio Control Room: the comparative table now carries
                  six columns, so it claims more of the desktop width
                  before the sidebar is allowed to wrap beneath it. */}
              <div style={{ flex: "4 1 640px", minWidth: 0 }}>
                <HoldingsTable
                  view={status.view}
                  cockpit={cockpit}
                  fitByTicker={fitByTicker}
                  stanceByTicker={stanceByTicker}
                  caseCreateStatus={caseCreateStatus}
                  openInvestmentCase={openInvestmentCase}
                  onOpenEditPortfolio={openReplaceForm}
                  hypothetical={hypothetical}
                  simulationUsesValue={simulationUsesValue}
                  onEditPosition={(key, value, baseValue) =>
                    setEdits((current) => setPosition(current, key, value, baseValue))
                  }
                  onResetPosition={(key) => setEdits((current) => resetPosition(current, key))}
                  onResetSimulation={() => setEdits(resetSimulation())}
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
  t,
}: {
  view: PortfolioView;
  largestHolding: HoldingView | null;
  coveredCount: number | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const cashDisplay =
    view.cashValueAbsolute !== null
      ? formatCurrency(view.cashValueAbsolute)
      : view.cashWeightPercent !== null
        ? formatPercentPoints(view.cashWeightPercent)
        : t("portfolio.header.notAvailable");

  return (
    <Stack gap="metadata">
      {/* Portfolio Control Room. This strip and the separate Portfolio
          Hero card above it were two stacked full-width blocks of
          Label+value pairs -- eight statistics, one card each, before
          the reader reached a single holding. They are one card now.
          No statistic was dropped and none is recomputed: the Hero's
          ownership sentence leads, and its Concentration / Holdings /
          Cash join the strip's own Value / Largest / Coverage /
          Opportunity / Risk on the same wrapping row. */}
      <Surface tier="primary">
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
        <Inline gap="inter-section" wrap style={{ justifyContent: "space-between" }}>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.totalValueLabel")}</Label>
            <Text
              as="span"
              style={{ fontSize: "var(--type-heading-3-size, 1.5rem)", fontWeight: 700, fontVariantNumeric: "tabular-nums" }}
            >
              {view.totalValue !== null ? formatCurrency(view.totalValue) : t("portfolio.pulse.totalValueUnavailable")}
            </Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.largestPositionLabel")}</Label>
            <Text as="span">
              {largestHolding
                ? t("portfolio.pulse.largestPositionValue", {
                    ticker: largestHolding.ticker,
                    // The translation template already supplies the "%" --
                    // pass the rounded figure only, not `formatPercentPoints`'s
                    // own "%"-suffixed string.
                    percent: largestHolding.weightPercent.toFixed(1),
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
          {/* Biggest opportunity / biggest risk are deliberately NOT
              repeated here. `TodaysBiggestRiskOpportunity` renders the
              same two tickers immediately below, under the identical
              labels, and adds what actually changed plus a link into
              the case -- a bare ticker above it was the weaker of two
              copies of one fact. */}
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
            <Text as="span" style={{ fontVariantNumeric: "tabular-nums" }}>{cashDisplay}</Text>
          </Stack>
        </Inline>
        </Stack>
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
  // The translation template already supplies "%" -- one decimal, no suffix.
  const topWeightSum = topHoldings.reduce((sum, h) => sum + h.weightPercent, 0).toFixed(1);

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
                <Text as="span" color="secondary" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {formatPercentPoints(holding.weightPercent)}
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
            <Text as="span" style={{ fontVariantNumeric: "tabular-nums" }}>
              {view.cashValueAbsolute !== null
                ? formatCurrency(view.cashValueAbsolute)
                : view.cashWeightPercent !== null
                  ? formatPercentPoints(view.cashWeightPercent)
                  : t("portfolio.header.notAvailable")}
            </Text>
          </Inline>
          <Inline gap="row" style={{ justifyContent: "space-between" }}>
            <Text as="span" color="secondary">
              {t("portfolio.allocation.unallocatedLabel")}
            </Text>
            <Text as="span" style={{ fontVariantNumeric: "tabular-nums" }}>
              {unallocatedPercent !== null ? formatPercentPoints(unallocatedPercent) : t("portfolio.header.notAvailable")}
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
/** Atlas UX Freeze v1 -- the approved atlas-portfolio frame differentiates
 * the Opportunity/Risk eyebrows with the same semantic tones the ticker
 * badges directly below them already use (teal for the positive signal,
 * amber for the one needing attention); this page previously rendered
 * both labels in the same neutral tertiary color. Reuses the existing
 * semantic-color tokens directly (`Label`'s own `color` prop is typed to
 * the primary/secondary/tertiary text tiers only, not these tones), so
 * no shared component changes -- a style override at these two call
 * sites only. */
const RISK_OPPORTUNITY_TONE_COLOR: Record<"opportunity" | "risk", string> = {
  opportunity: "var(--color-semantic-green)",
  risk: "var(--color-semantic-amber)",
};

function TodaysRiskOpportunityCard({
  label,
  tone,
  assessment,
  agendaItem,
  onOpenCase,
  t,
}: {
  label: string;
  tone: "opportunity" | "risk";
  assessment: PortfolioFitAssessmentView;
  agendaItem: AgendaItemView | undefined;
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const verdictText = describeFitVerdict(assessment, t);
  return (
    <Surface tier="elevated">
      <Stack gap="metadata">
        <Label style={{ color: RISK_OPPORTUNITY_TONE_COLOR[tone] }}>{label}</Label>
        <Text as="span" style={{ fontWeight: 600, fontSize: "var(--type-size-h5)" }}>
          {assessment.ticker}
        </Text>
        {verdictText && <Text as="p" color="secondary">{verdictText}</Text>}
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

/**
 * One line of portfolio-level truth: how much of the portfolio currently
 * sits in holdings Atlas supports reducing.
 *
 * Quiet when there is nothing to say -- a portfolio with no supported
 * reductions renders nothing here rather than a reassuring "0%", which
 * would be a claim of its own.
 *
 * The second sentence is not decoration. "21% of the portfolio is held in
 * positions Atlas supports reducing" and "Atlas recommends selling 21% of
 * the portfolio" are different statements, and the first is the only one
 * Atlas can make -- it does not size trades anywhere.
 */
function ReductionExposureNote({
  exposure,
  t,
}: {
  exposure: ReductionExposure;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (exposure.count === 0) return null;
  return (
    <Stack gap="metadata">
      <Text as="p">
        {t("portfolio.reductionExposure.summary", {
          percent: exposure.weightPercent.toFixed(1),
          count: exposure.count,
          holdings: exposure.tickers.join(" · "),
        })}
      </Text>
      <Text as="p" color="tertiary">
        {t("portfolio.reductionExposure.notASellTarget")}
      </Text>
    </Stack>
  );
}

function TodaysBiggestRiskOpportunity({
  opportunityKind,
  biggestOpportunity,
  biggestRisk,
  agendaItemByTicker,
  onOpenCase,
  t,
}: {
  /** Whether Atlas supports adding to the named holding, or whether it is
   * merely the strongest-fitting one. The card's own label depends on it:
   * "opportunity" is a claim about action, and must not be made when the
   * Decision Layer has not made it. */
  opportunityKind: "supported_action" | "strongest_setup";
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
        label={t(
          opportunityKind === "supported_action"
            ? "portfolio.todaysFocus.biggestOpportunityLabel"
            : "portfolio.todaysFocus.strongestSetupLabel",
        )}
        tone="opportunity"
        assessment={biggestOpportunity}
        agendaItem={agendaItemByTicker.get(biggestOpportunity.ticker)}
        onOpenCase={onOpenCase}
        t={t}
      />
      <TodaysRiskOpportunityCard
        label={t("portfolio.todaysFocus.biggestRiskLabel")}
        tone="risk"
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
            <Text as="span" color="secondary" style={{ fontVariantNumeric: "tabular-nums" }}>
              {formatPercentPoints(weightPercent)}
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
  caseCreateStatus,
  openInvestmentCase,
  onOpenEditPortfolio,
  hypothetical,
  simulationUsesValue,
  onEditPosition,
  onResetPosition,
  onResetSimulation,
  t,
}: {
  view: PortfolioView;
  cockpit: PortfolioCockpitFetchStatus;
  fitByTicker: Map<string, PortfolioFitAssessmentView>;
  stanceByTicker: Map<string, StanceLevel>;
  caseCreateStatus: Record<string, CaseCreateStatus>;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  onOpenEditPortfolio: () => void;
  /** Portfolio Editing & Simulation Layer v1 -- the one hypothetical
   * portfolio every part of this table reads. Never a second copy. */
  hypothetical: HypotheticalPortfolio;
  /** Whether the editable quantum is money or weight -- see the page's
   * own derivation. Decides only which unit the row renders. */
  simulationUsesValue: boolean;
  onEditPosition: (key: string, value: number, baseValue: number) => void;
  onResetPosition: (key: string) => void;
  onResetSimulation: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  /* Portfolio Holdings Cockpit v1: the table is a scanning surface, so
     its own density is part of the product. Vertical padding is tighter
     than the page default and the type steps down to the metadata size
     -- nine columns of short categorical values do not need prose
     sizing, and every extra pixel per row costs a holding the reader
     could otherwise have seen without scrolling. */
  const cellStyle: CSSProperties = {
    /* Simulation v1 trimmed the horizontal padding from 12px to 8px a
       side. The controls column is a tenth column, and at 12px it
       pushed the table 61px past the viewport -- reintroducing the
       horizontal scroll the cockpit sprint had just removed. Eight
       pixels across ten columns buys most of it back, and naming the
       step on the control ("−10%" rather than a bare glyph) needed the
       last of it -- so 6px a side. The columns are short categorical
       values that do not need a wider gutter, and this keeps the whole
       nine-column cockpit inside 1440px with no horizontal scroll. */
    padding: "4px 6px",
    textAlign: "left",
    borderBottom: `var(--width-border-hairline) solid var(--color-border-hairline)`,
    fontFamily: "var(--type-family-metadata)",
    fontVariantNumeric: "tabular-nums",
    fontSize: "13px",
    lineHeight: 1.25,
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
  /** Portfolio Control Room: `RiskProjection` is the single
   * highest-severity risk *category* plus its status
   * (`analysis_engine.risk.models.RiskProjection` -- "for compact
   * display only, explicitly never an aggregate score"). Read verbatim
   * from the cockpit report this page already fetches; nothing is
   * ranked, scored or combined here. */
  const riskProjectionByTicker = new Map<string, CockpitRiskProjectionView>();
  /** Portfolio Holdings Cockpit v1: the whole cockpit row, keyed by
   * ticker. The narrow maps above stay because the sort helpers read
   * them; the table itself now reads one object per holding rather than
   * threading eight parallel lookups into the row. That is also the
   * seam a future simulation layer needs -- one canonical holdings
   * collection it can transform before anything is rendered. */
  const cockpitByTicker = new Map<string, PortfolioCockpitHoldingView>();
  if (cockpit.kind === "loaded") {
    for (const holding of cockpit.report.holdings) {
      coverageByTicker.set(holding.ticker, holding.analysisCoverage.level);
      decisionSupportByTicker.set(holding.ticker, holding.decisionSupport.level);
      riskProjectionByTicker.set(holding.ticker, holding.riskProjection);
      cockpitByTicker.set(holding.ticker, holding);
    }
  }
  const orderedHoldings = sortHoldings(
    view.holdings,
    sortKey,
    fitRatingByTicker,
    coverageByTicker,
    stanceByTicker,
  );
  /** Portfolio Holdings Cockpit v1: every holding, in one continuous
   * list.
   *
   * The table used to cap at 15 rows behind a "View All Holdings"
   * toggle -- reasonable when a row was 99px tall and 25 of them ran to
   * ~2,475px. At 53px the whole portfolio is ~1,334px, barely more than
   * the old capped table, and a cockpit whose purpose is scanning the
   * portfolio as a whole cannot ask the reader to unhide half of it
   * first.
   *
   * Deliberately no virtualization and no replacement paging scheme:
   * the data is already fully fetched in one request, and 25 rows of
   * short categorical values is not a rendering problem. A portfolio
   * large enough to make this page long would be a real product
   * question about the cockpit, not something a hidden display cap
   * should answer silently. */
  const visibleHoldings = orderedHoldings;
  /* Holdings Atlas has no analysis for, straight from the backend's own
     coverage level. Nothing here decides *why* -- the Case does that. */
  const uncoveredHoldingCount = view.holdings.filter(
    (holding) => coverageByTicker.get(holding.ticker) === "no_coverage",
  ).length;

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
        <Text color="tertiary" as="p" style={{ fontVariantNumeric: "tabular-nums" }}>
          {t("portfolio.holdings.totalValue", { value: formatCurrency(view.totalValue) })}
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

      {/* Portfolio Editing & Simulation Layer v1 -- the one place the
          page says the investor is exploring rather than recording.
          Absent entirely when there are no edits, so an untouched
          Portfolio looks exactly as it did before this sprint. The
          wording is deliberately "hypothetical", never "unsaved": there
          is nothing to save, and saying otherwise would imply these
          edits are expected to become real. */}
      {hypothetical.isDirty && (
        <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
          <Inline gap="metadata" align="center" wrap>
            <StatusBadge label={t("portfolio.simulation.active")} tone="neutral" />
            <Text as="span" color="secondary" style={{ fontSize: "13px" }}>
              {t(
                hypothetical.changedCount === 1
                  ? "portfolio.simulation.changeCountOne"
                  : "portfolio.simulation.changeCountOther",
                { count: hypothetical.changedCount },
              )}
              {" · "}
              {t("portfolio.simulation.notRecorded")}
            </Text>
          </Inline>
          <Button variant="tertiary" onClick={onResetSimulation}>
            {t("portfolio.simulation.reset")}
          </Button>
        </Inline>
      )}

      <div style={{ overflowX: "auto", minWidth: 0 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {/* Portfolio Control Room. Five comparative columns,
                    every one a closed categorical vocabulary Atlas
                    already computes, so a reader can scan down a column
                    and compare positions rather than reading a
                    paragraph per row.

                    What each header does NOT claim matters as much as
                    what it does. There is deliberately no Conviction,
                    Expected Return, Upside or Downside column: the
                    field named `conviction` measures how well the
                    available *analysis* supports a conclusion (its own
                    reason codes are coverage, contradiction, open
                    questions), which is the analytical-confidence
                    concept investment conviction is defined against;
                    and no probability-weighted return exists anywhere
                    in the engine. "Största risk" names the single
                    highest-severity risk *category*, which is what
                    `RiskProjection` actually is -- not a
                    permanent-capital-loss estimate, so it is not
                    labelled "Risk".

                    Recommendation and Atlas view are separate columns
                    on purpose: they are different concepts (canonical
                    direction vs. review state) and each header does the
                    labelling that a bare pair of badges could not. The
                    Reason column's per-row Stance prose is gone -- it
                    was the one thing preventing this from being a table
                    you can compare across; the reasoning it summarised
                    is one click away in the Investment Case, which owns
                    that explanation. */}
                <th style={headerCellStyle}>{t("portfolio.cockpitTable.companyHeader")}</th>
                <th style={{ ...headerCellStyle, textAlign: "right" }}>
                  {t("portfolio.cockpitTable.positionHeader")}
                </th>
                <th style={headerCellStyle}>{t("portfolio.cockpitTable.atlasHeader")}</th>
                {(["business", "investment", "risk", "valuation", "forward", "fit"] as CockpitColumnKey[]).map(
                  (column) => (
                    <th key={column} style={headerCellStyle}>
                      {t(COCKPIT_COLUMN_HEADER_KEY[column])}
                    </th>
                  ),
                )}
                {/* Simulation controls. The header is visually empty --
                    a column of two icon buttons needs no title -- but
                    carries an accessible name so the column is
                    announced rather than read as a gap. */}
                <th style={headerCellStyle}>
                  <VisuallyHidden>{t("portfolio.simulation.columnHeader")}</VisuallyHidden>
                </th>
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
                    analysis={cockpitByTicker.get(holding.ticker)}
                    fitRating={fitRatingByTicker.get(holding.ticker)}
                    thisCaseCreateStatus={caseCreateStatus[holding.ticker] ?? { kind: "idle" }}
                    openInvestmentCase={openInvestmentCase}
                    simulated={hypothetical.holdings.find((h) => h.key === holdingKey(holding))}
                    simulationUsesValue={simulationUsesValue}
                    availableToInvest={availableCapital(hypothetical)}
                    onEditPosition={onEditPosition}
                    onResetPosition={onResetPosition}
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
              view.concentrationLevel
                ? t("portfolio.concentration", {
                    value: CONCENTRATION_LEVEL_KEY[view.concentrationLevel]
                      ? t(CONCENTRATION_LEVEL_KEY[view.concentrationLevel]!)
                      : view.concentrationLevel,
                  })
                : null,
              /* Holding Coverage Truth v1: a row of em dashes and a row
                 saying "reduce" look equally like a verdict. They are not.
                 This says, once, that the blank rows are Atlas's reach and
                 not Atlas's opinion; the Case itself says which kind of gap
                 it is. Counted from the backend's own coverage level -- no
                 reason is inferred here. */
              uncoveredHoldingCount > 0
                ? t("coverage.notAnalysed.hint")
                : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </Text>
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
/** Portfolio Control Room, Phase J. One honest em dash plus a screen-
 * reader-only word, used for every unknown in the table. Never a
 * neutral-looking middle value: a holding Atlas has not assessed must
 * not read as an average one. */
function NotAssessedCell({ t }: { t: (key: TranslationKey, params?: Record<string, string | number>) => string }) {
  return (
    <Text as="span" color="tertiary">
      <span aria-hidden="true">{"\u2014"}</span>
      <VisuallyHidden>{t("portfolio.holdingsTable.notAssessed")}</VisuallyHidden>
    </Text>
  );
}
/**
 * One holding = one row (Portfolio Holdings Cockpit v1).
 *
 * The row is a scanning unit, not a card: every cell states one
 * already-computed conclusion in one or two lines, and links to the
 * Investment Case chapter that explains it. No cell explains itself in
 * place, and nothing here is computed, averaged or ranked -- the two
 * ratings it shows are the Investment Case's own
 * `deriveCompanyRating`/`deriveInvestmentRating` applied to the same
 * inputs, so a holding reads the same numbers on both screens.
 *
 * Unknown is never rendered as bad. A category with no verdict is
 * excluded from a rating rather than scored zero; a rating with no real
 * input at all renders the em-dash, never "0/10" or "Weak".
 */
/** Two lines in one cell, with no gap token between them: a row that
 * must stay around 48px cannot afford `Stack`'s smallest gap, and the
 * secondary line is already distinguished by colour. */
const STACKED_CELL_STYLE: CSSProperties = { display: "grid", lineHeight: 1.2, fontSize: "13px" };

/** The secondary line of a stacked cell: the tier word, the category
 * name, the absolute value. Smaller and quieter than the line above it,
 * because the line above is what the reader is scanning for. */
const SECONDARY_LINE_STYLE: CSSProperties = { fontSize: "11px", lineHeight: 1.2 };

function HoldingsTableRow({
  holding,
  isUnresolvedInCockpit,
  analysis,
  fitRating,
  thisCaseCreateStatus,
  openInvestmentCase,
  simulated,
  simulationUsesValue,
  availableToInvest,
  onEditPosition,
  onResetPosition,
  cellStyle,
  t,
}: {
  holding: HoldingView;
  isUnresolvedInCockpit: boolean;
  /** The whole cockpit row for this holding, or `undefined` while the
   * cockpit fetch is still in flight -- in which case every analytical
   * cell reads as not-yet-assessed rather than as a negative verdict. */
  analysis: PortfolioCockpitHoldingView | undefined;
  fitRating: FitRating | undefined;
  thisCaseCreateStatus: CaseCreateStatus;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  /** This holding's position in the hypothetical portfolio. Always
   * present for a real holding; `undefined` only while the portfolio is
   * still loading, in which case the row shows its persisted position
   * and offers no controls. */
  simulated: HypotheticalHolding | undefined;
  simulationUsesValue: boolean;
  /** Unallocated capital available to fund an increase right now. The
   * `+` control disables at zero rather than letting the model silently
   * clamp an edit the investor asked for. */
  availableToInvest: number;
  onEditPosition: (key: string, value: number, baseValue: number) => void;
  onResetPosition: (key: string) => void;
  cellStyle: CSSProperties;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const isCreating = thisCaseCreateStatus.kind === "creating";

  /** Alpha Integration Fix (One Product Pass): a Holdings row opens the
   * real Investment Case directly. Clicking the row itself is the
   * general case -- "explain this holding" -- and lands on the
   * conclusion; a specific cell lands on the chapter for that
   * dimension. */
  function handleRowActivate() {
    if (isCreating) return;
    openInvestmentCase(holding.ticker, holding.caseId);
  }

  /* Both new cockpit fields are read as optional, the same way the
     recommendation-reasoning contract reads every optional collection:
     a payload written before the field existed is a legacy payload, not
     a crash, and an absent vector must read as "not assessed" rather
     than as a rating of zero. */
  const businessRating = analysis ? deriveCompanyRating(analysis.businessCategories ?? []) : null;
  const investmentRating = analysis ? deriveInvestmentRating(analysis.decisionSupport.level) : null;
  const risk = analysis?.riskProjection;
  const valuationStatus = analysis?.valuation.status;
  const forward = analysis?.forwardEvidence ?? null;
  /* Coverage is not a column of its own in v1 -- it would crowd out a
     more decision-useful dimension. It surfaces only as an exception:
     when Atlas could not evaluate much, the Atlas cell says so beneath
     the action, and the full picture is in the Case's Evidence
     chapter. A normal, fully-evaluated holding stays quiet. */
  const hasLimitedEvidence =
    analysis !== undefined &&
    (analysis.analysisCoverage.level === "partial_coverage" ||
      analysis.analysisCoverage.level === "no_coverage");

  /** A cell that names a conclusion and links to the chapter explaining
   * it. A real anchor, so it is keyboard reachable, focusable and
   * openable in a new tab; `stopPropagation` keeps it from also firing
   * the row's own conclusion navigation. */
  function LinkedCell({ column, children }: { column: CockpitColumnKey; children: ReactNode }) {
    const href = cockpitCellHref(holding.caseId, column);
    if (!href) return <>{children}</>;
    return (
      <RouterLink
        to={href}
        state={{ origin: "portfolio", ticker: holding.ticker }}
        aria-label={t(COCKPIT_COLUMN_LINK_LABEL_KEY[column], { ticker: holding.ticker })}
        onClick={(event) => event.stopPropagation()}
        style={{ color: "inherit", textDecoration: "none" }}
      >
        {children}
      </RouterLink>
    );
  }

  /** Score over tier, two quiet lines. The tier word carries the
   * meaning for a reader who does not want to read numbers; the score
   * carries the comparison for one scanning down the column. */
  function RatingCell({ rating }: { rating: AtlasRating | null }) {
    if (rating === null || rating.score === null) return <NotAssessedCell t={t} />;
    return (
      <div style={STACKED_CELL_STYLE}>
        <Text as="span" style={{ fontWeight: 600 }}>
          {rating.score.toFixed(1)}
        </Text>
        <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
          {t(RATING_TIER_LABEL_KEY[rating.tier])}
        </Text>
      </div>
    );
  }

  return (
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
      className={styles.row}
      style={{ cursor: isCreating ? "default" : "pointer" }}
    >
      {/* Holding. The ticker is the scan key; the exceptions that used
          to take a line each (opening, reconciled, unresolved) are
          quiet secondary text and only when they apply. */}
      <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)" }}>
        <div style={STACKED_CELL_STYLE}>
          <Text as="span" style={{ fontWeight: 600 }}>
            {holding.ticker}
          </Text>
          {isCreating && (
            <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
              {t("portfolio.holdings.opening")}
            </Text>
          )}
          {!isCreating && holding.reconciliationStatus === "UPDATED" && (
            <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
              {t("portfolio.holdings.updatedAutomatically")}
            </Text>
          )}
          {!isCreating && isUnresolvedInCockpit && (
            <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
              {t("portfolio.cockpit.unresolved")}
            </Text>
          )}
        </div>
      </td>

      {/* Position. Weight is the comparable figure, so it leads; the
          absolute value is secondary and renders only for a portfolio
          that actually has one. */}
      {/* Position. Unchanged, this reads exactly as it did before the
          simulation layer existed. Changed, it states the persisted
          figure and the hypothetical one together -- the investor has
          to be able to see what they started from, or "what if" has no
          anchor. */}
      <td style={{ ...cellStyle, textAlign: "right" }}>
        <div style={STACKED_CELL_STYLE}>
          <Text as="span" style={{ fontWeight: 600 }}>
            {simulated?.isChanged ? (
              <>
                <Text as="span" color="tertiary" style={{ fontWeight: 400 }}>
                  {formatPercentPoints(simulated.baseWeightPercent)}
                </Text>
                {" → "}
                {formatPercentPoints(simulated.hypotheticalWeightPercent)}
              </>
            ) : (
              formatPercentPoints(simulated ? simulated.hypotheticalWeightPercent : holding.weightPercent)
            )}
          </Text>
          {simulationUsesValue && holding.valueAbsolute !== null && (
            <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
              {simulated?.isChanged
                ? `${formatCurrency(simulated.baseValue)} → ${formatCurrency(simulated.hypotheticalValue)}`
                : formatCurrency(simulated ? simulated.hypotheticalValue : holding.valueAbsolute)}
            </Text>
          )}
        </div>
      </td>

      {/* Atlas view -- the one cell that is allowed to shout. It reads
          `decision_support`, Atlas's own authoritative evidence-support
          state, and never infers an action from fit, risk, valuation or
          a score. */}
      <td style={cellStyle}>
        <LinkedCell column="atlas">
          <div style={STACKED_CELL_STYLE}>
            {analysis ? (
              <StatusBadge
                label={t(DECISION_SUPPORT_BADGE_KEY[analysis.decisionSupport.level])}
                tone={DECISION_SUPPORT_TONE[analysis.decisionSupport.level]}
              />
            ) : (
              <NotAssessedCell t={t} />
            )}
            {hasLimitedEvidence && (
              <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
                {t("portfolio.cockpitTable.limitedEvidence")}
              </Text>
            )}
          </div>
        </LinkedCell>
      </td>

      {/* Business -- how strong the company is. Deliberately a different
          question from Investment beside it, from a different source:
          this averages the business-category vector, that reads the
          evidence-support state. They are never collapsed. */}
      <td style={cellStyle}>
        <LinkedCell column="business">
          <RatingCell rating={businessRating} />
        </LinkedCell>
      </td>

      {/* Investment -- how attractive the security is to buy today. */}
      <td style={cellStyle}>
        <LinkedCell column="investment">
          <RatingCell rating={investmentRating} />
        </LinkedCell>
      </td>

      {/* Risk. `RiskProjection` is the single highest-severity risk
          *category* plus its status -- never an aggregate score, and
          never merged with valuation risk, which is one of the
          categories it selects among. */}
      <td style={cellStyle}>
        <LinkedCell column="risk">
          {risk && risk.status !== "insufficient_input" ? (
            <div style={STACKED_CELL_STYLE}>
              <Text as="span" style={{ fontWeight: 600 }}>
                {t(RISK_STATUS_KEY[risk.status])}
              </Text>
              <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
                {t(RISK_CATEGORY_KEY[risk.category])}
              </Text>
            </div>
          ) : (
            <NotAssessedCell t={t} />
          )}
        </LinkedCell>
      </td>

      {/* Valuation -- the FCF-yield conclusion against the company's own
          history. No sensitivity range here: it is conditional
          arithmetic, not a valuation verdict, and the Case subordinates
          it for exactly that reason. */}
      <td style={cellStyle}>
        <LinkedCell column="valuation">
          {valuationStatus && valuationStatus !== "insufficient_input" ? (
            <Text as="span">{t(VALUATION_STATUS_KEY[valuationStatus])}</Text>
          ) : (
            <NotAssessedCell t={t} />
          )}
        </LinkedCell>
      </td>

      {/* Forward. Counts of verified forward evidence, never a forecast
          and never a polarity -- raised, lowered and reaffirmed all
          count the same. Only 1 of 25 current holdings has any, so the
          honest normal state here is the em-dash. */}
      <td style={cellStyle}>
        <LinkedCell column="forward">
          {forward && forward.guidanceCount + forward.contractedVolumeCount > 0 ? (
            <div style={STACKED_CELL_STYLE}>
              <Text as="span">{t("portfolio.cockpitTable.forward.verified")}</Text>
              <Text as="span" color="tertiary" style={SECONDARY_LINE_STYLE}>
                {t(
                  forward.guidanceCount === 1
                    ? "portfolio.cockpitTable.forward.countOne"
                    : "portfolio.cockpitTable.forward.countOther",
                  { count: forward.guidanceCount },
                )}
              </Text>
            </div>
          ) : (
            <NoneCell t={t} />
          )}
        </LinkedCell>
      </td>

      {/* Portfolio Fit's own distilled overall verdict, verbatim.
          `unavailable` is one of its real members -- a disclosed
          "not evaluated", never a neutral-looking middle score. */}
      <td style={cellStyle}>
        <LinkedCell column="fit">
          {fitRating ? <FitBadge rating={fitRating} /> : <NotAssessedCell t={t} />}
        </LinkedCell>
      </td>

      {/* Simulation controls. Hypothetical only: none of these calls a
          portfolio endpoint, records a trade or writes Decision Memory.
          `stopPropagation` keeps a control from also opening the
          Investment Case the row itself links to. */}
      <td style={cellStyle} onClick={(event) => event.stopPropagation()}>
        {simulated && (
          <Inline gap="metadata" style={{ gap: "2px" }} align="center">
            {/* The unit is on the control, not only in its accessible
                name. A bare "−" reads as "one share" -- and Atlas holds
                no share counts for any of these holdings, so that would
                be the one interpretation the data cannot support.
                "−10%" says what the click actually does: move the
                position by a tenth of its *persisted* size. */}
            <SimulationButton
              label={t("portfolio.simulation.stepDown")}
              title={t("portfolio.simulation.reduceLabel", { ticker: holding.ticker })}
              disabled={simulated.hypotheticalValue <= 0}
              onClick={() =>
                onEditPosition(
                  simulated.key,
                  simulated.hypotheticalValue - editStep(simulated.baseValue),
                  simulated.baseValue,
                )
              }
            />
            <SimulationButton
              label={t("portfolio.simulation.stepUp")}
              title={t("portfolio.simulation.increaseLabel", { ticker: holding.ticker })}
              /* Fully invested means nothing to invest with until
                 something is reduced. Disabling says so plainly rather
                 than accepting the click and quietly clamping it. */
              disabled={availableToInvest <= 0}
              onClick={() =>
                onEditPosition(
                  simulated.key,
                  simulated.hypotheticalValue + editStep(simulated.baseValue),
                  simulated.baseValue,
                )
              }
            />
            {simulated.isChanged && (
              <SimulationButton
                label={t("portfolio.simulation.restoreGlyph")}
                title={t("portfolio.simulation.restoreLabel", { ticker: holding.ticker })}
                onClick={() => onResetPosition(simulated.key)}
              />
            )}
          </Inline>
        )}
      </td>
    </tr>
  );
}

/** One compact simulation control. A real `<button>` with a real
 * accessible name -- the glyph alone ("−", "+", "↺") means nothing to a
 * screen reader, and the name states both the holding and the operation
 * so a row of three controls is unambiguous when heard in sequence. */
function SimulationButton({
  label,
  title,
  disabled = false,
  onClick,
}: {
  label: string;
  title: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={title}
      title={title}
      disabled={disabled}
      onClick={onClick}
      style={{
        font: "inherit",
        lineHeight: 1,
        padding: "2px 6px",
        cursor: disabled ? "default" : "pointer",
        background: "transparent",
        color: disabled ? "var(--color-text-tertiary)" : "var(--color-text-secondary)",
        border: "var(--width-border-hairline) solid var(--color-border-hairline)",
        borderRadius: "var(--radius-card)",
        opacity: disabled ? 0.45 : 1,
      }}
    >
      {label}
    </button>
  );
}

/** The quiet em-dash. Used where Atlas holds nothing at all for a
 * dimension -- distinct from `NotAssessedCell`, which says Atlas looked
 * and could not conclude. Neither is ever a low score. */
function NoneCell({ t }: { t: (key: TranslationKey) => string }) {
  return (
    <Text as="span" color="tertiary" aria-label={t("portfolio.cockpitTable.notAssessed")}>
      {t("portfolio.cockpitTable.none")}
    </Text>
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
