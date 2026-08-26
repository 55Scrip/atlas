import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, StatusBadge, StatusText, Surface, Text, VisuallyHidden } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  deriveActivity,
  sortActivity,
  formatRelativeTime,
  type DecisionRecord,
  type OutcomeRecord,
  type TradeLogEntry,
  type ActivityEvent,
} from "../activity/deriveActivity";
import {
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  ANALYSIS_COVERAGE_TONE,
  type AnalysisCoverageLevel,
  type ConvictionLevel,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type PriorityLevel,
  type ReviewPriority,
} from "../status/statusTone";
import type { StatusTone } from "../foundation";
import type { AnalysisRiskStatus } from "../changeIntelligence/describeChange";
import { FitBadge } from "../portfolioFit/FitBadge";
import { fetchPortfolioFitForHoldings, type PortfolioFitAssessmentView, type FitRating } from "../portfolioFit/portfolioFitApi";
import { fetchStanceForHoldings, type TickerStanceView } from "../stance/stanceApi";
import { StanceBadge } from "../stance/StanceBadge";
import type { StanceLevel } from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { AgendaItemRow } from "../dailyBriefAgenda/AgendaItemRow";
import { PriorityBadge } from "../dailyBriefAgenda/PriorityBadge";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { MonitoringFreshnessNote } from "../monitoring/MonitoringFreshnessNote";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { PortfolioSharedWeakPointsSection } from "../evidenceGraph/PortfolioSharedWeakPointsSection";
import { invalidateAlphaPortfolio, setAlphaPortfolioData, useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { PortfolioActionDistribution } from "../investmentDecision/PortfolioActionDistribution";
import {
  fetchPortfolioActionDistribution,
  type PortfolioActionDistributionView,
} from "../investmentDecision/investmentDecisionApi";
import { PortfolioConvictionBreakdown } from "../recommendationConviction/PortfolioConvictionBreakdown";
import {
  fetchPortfolioConvictionBreakdown,
  type PortfolioConvictionBreakdownView,
} from "../recommendationConviction/recommendationConvictionApi";
import { PortfolioDecisionPathBreakdown } from "../decisionPath/PortfolioDecisionPathBreakdown";
import {
  fetchPortfolioDecisionPathBreakdown,
  type PortfolioDecisionPathBreakdownView,
} from "../decisionPath/decisionPathApi";
import { PortfolioOpportunityCostBreakdown } from "../opportunityCost/PortfolioOpportunityCostBreakdown";
import {
  fetchPortfolioOpportunityCostBreakdown,
  type PortfolioOpportunityCostBreakdownView,
} from "../opportunityCost/opportunityCostApi";
import { PortfolioDecisionMemoryBreakdown } from "../decisionMemory/PortfolioDecisionMemoryBreakdown";
import {
  fetchPortfolioDecisionMemoryBreakdown,
  type PortfolioDecisionMemoryBreakdownView,
} from "../decisionMemory/decisionMemoryApi";
import { PortfolioDecisionExplanationBreakdown } from "../decisionExplanation/PortfolioDecisionExplanationBreakdown";
import {
  fetchPortfolioDecisionExplanationBreakdown,
  type PortfolioDecisionExplanationBreakdownView,
} from "../decisionExplanation/decisionExplanationApi";
import { PortfolioReliabilityBreakdown } from "../decisionReliability/PortfolioReliabilityBreakdown";
import { PortfolioSynthesisBreakdown } from "../portfolioDecision/PortfolioSynthesisBreakdown";
import {
  fetchPortfolioSynthesisBreakdown,
  type PortfolioSynthesisBreakdownView,
} from "../portfolioDecision/portfolioDecisionApi";
import {
  fetchPortfolioReliabilityBreakdown,
  type PortfolioReliabilityBreakdownView,
} from "../decisionReliability/decisionReliabilityApi";
import {
  fetchPortfolioSharedWeakPoints,
  type PortfolioSharedWeakPointsView,
} from "../evidenceGraph/portfolioSharedWeakPointsApi";
import { fetchMonitoringStatus, type MonitoringOperationalStatusView } from "../monitoring/monitoringApi";
import { sortHoldings, type HoldingSortKey } from "../portfolio/sortHoldings";

/** Product Sprint 8 (Portfolio Excellence, Deliverable 4 -- Unify
 * Attention Surfaces): Portfolio used to run two independent, competing
 * "what matters" computations -- this same shared `/api/daily-brief
 * -agenda` fetch (filtered to `group === "portfolio"`) shown as "Today's
 * Agenda", and a separate client-side derivation (`derivePortfolioActions`,
 * predating the Agenda) shown as "Needs Your Attention". The two could
 * legitimately disagree about the same ticker, since the older
 * derivation had no Portfolio Fit/Case Condition/Assumption input at
 * all. That gap is now closed: the one real signal the Agenda engine
 * didn't yet cover (a missing-evidence gap) was added to the shared
 * backend engine itself (`atlas/alpha/daily_brief_agenda/engine.py`'s
 * `evidence_gap_signal`) rather than kept as a second, competing
 * frontend computation. This fetch is now Portfolio's one and only
 * attention source -- `derivePortfolioActions.ts`/`describePortfolioAction.ts`
 * and the "Needs Your Attention" section they powered are deleted, not
 * left dormant. */
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
/** Holdings table Coverage column (Portfolio Workspace v1) -- the
 * approved frame shows a binary Covered/Not Covered display, but the
 * real `AnalysisCoverageLevel` has three honest states. Collapsing
 * `partial_coverage` into "Covered" would misrepresent real data, so
 * it gets its own distinct label ("Partial") rather than being folded
 * into either binary state -- a deliberate, documented deviation from
 * the frame's own two-state display, not a Figma-fidelity gap. */
const COVERAGE_DISPLAY_KEY: Record<AnalysisCoverageLevel, TranslationKey> = {
  substantial_coverage: "portfolio.holdingsTable.coverage.substantial_coverage",
  partial_coverage: "portfolio.holdingsTable.coverage.partial_coverage",
  no_coverage: "portfolio.holdingsTable.coverage.no_coverage",
};

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

/** Recent Activity (Portfolio Workspace v1) -- reuses the same three
 * real endpoints `HistoryPage.tsx`/`DashboardPage.tsx` already fetch
 * (`/api/decisions`, `/api/outcomes`, `/api/alpha-portfolio/trade-log`)
 * and the shared `deriveActivity` cross-reference, rather than
 * inventing a second "what happened" derivation. A failure here never
 * blocks the rest of the page -- the section simply doesn't render. */
type RecentActivityFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; decisions: DecisionRecord[]; outcomes: OutcomeRecord[]; trades: TradeLogEntry[] };

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
  const [recentActivity, setRecentActivity] = useState<RecentActivityFetchStatus>({ kind: "loading" });
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
  const [reconcileWeightInputs, setReconcileWeightInputs] = useState<Record<string, string>>({});
  const [reconcileStatus, setReconcileStatus] = useState<Record<string, ReconcileStatus>>({});
  /** Holdings Table (Portfolio Workspace v3) -- at most one row's inline
   * reconciliation form is expanded at a time ("Details on Demand"),
   * instead of every awaiting-reconciliation holding permanently
   * showing its own form inline as before. */
  const [expandedReconcileTicker, setExpandedReconcileTicker] = useState<string | null>(null);

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

  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefAgenda(controller.signal)
      .then((agenda) => setDailyBriefAgenda({ kind: "loaded", items: agenda.items.filter((item) => item.group === "portfolio") }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDailyBriefAgenda({ kind: "error" });
      });
    return () => controller.abort();
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

  /** Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
   * Understanding, Deliverable 7). */
  const [sharedWeakPoints, setSharedWeakPoints] = useState<PortfolioSharedWeakPointsView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioSharedWeakPoints(controller.signal)
      .then((points) => setSharedWeakPoints(points))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 1 (Investment Decision Synthesis,
   * Deliverable 7). */
  const [actionDistribution, setActionDistribution] = useState<PortfolioActionDistributionView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioActionDistribution(controller.signal)
      .then((distribution) => setActionDistribution(distribution))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 2 (Recommendation Strength &
   * Conviction, Deliverable 7). Same pattern as `actionDistribution`
   * above. */
  const [convictionBreakdown, setConvictionBreakdown] = useState<PortfolioConvictionBreakdownView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioConvictionBreakdown(controller.signal)
      .then((breakdown) => setConvictionBreakdown(breakdown))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 3 (Decision Path & Required
   * Progress, Deliverable 7). Same pattern as `convictionBreakdown`
   * above. */
  const [decisionPathBreakdown, setDecisionPathBreakdown] = useState<PortfolioDecisionPathBreakdownView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioDecisionPathBreakdown(controller.signal)
      .then((breakdown) => setDecisionPathBreakdown(breakdown))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 4 (Decision Alternatives &
   * Opportunity Cost, Deliverable 7). Same pattern as
   * `decisionPathBreakdown` above. */
  const [opportunityCostBreakdown, setOpportunityCostBreakdown] = useState<PortfolioOpportunityCostBreakdownView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioOpportunityCostBreakdown(controller.signal)
      .then((breakdown) => setOpportunityCostBreakdown(breakdown))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 5 (Decision Memory, Deliverable 7).
   * Same pattern as `opportunityCostBreakdown` above. */
  const [decisionMemoryBreakdown, setDecisionMemoryBreakdown] = useState<PortfolioDecisionMemoryBreakdownView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioDecisionMemoryBreakdown(controller.signal)
      .then((breakdown) => setDecisionMemoryBreakdown(breakdown))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 6 (Decision Explanation &
   * Traceability, Deliverable 7). Same pattern as
   * `decisionMemoryBreakdown` above. */
  const [decisionExplanationBreakdown, setDecisionExplanationBreakdown] = useState<PortfolioDecisionExplanationBreakdownView | null>(
    null,
  );
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioDecisionExplanationBreakdown(controller.signal)
      .then((breakdown) => setDecisionExplanationBreakdown(breakdown))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 7 (Decision Reliability, Deliverable
   * 8). Same pattern as `decisionExplanationBreakdown` above. */
  const [decisionReliabilityBreakdown, setDecisionReliabilityBreakdown] = useState<PortfolioReliabilityBreakdownView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioReliabilityBreakdown(controller.signal)
      .then((breakdown) => setDecisionReliabilityBreakdown(breakdown))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis,
   * Deliverable 8). Same pattern as `decisionReliabilityBreakdown`
   * above. */
  const [portfolioSynthesisBreakdown, setPortfolioSynthesisBreakdown] = useState<PortfolioSynthesisBreakdownView | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioSynthesisBreakdown(controller.signal)
      .then((breakdown) => setPortfolioSynthesisBreakdown(breakdown))
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

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      fetch("/api/decisions", { signal: controller.signal }).then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<DecisionRecord[]>;
      }),
      fetch("/api/outcomes", { signal: controller.signal }).then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<OutcomeRecord[]>;
      }),
      fetch("/api/alpha-portfolio/trade-log", { signal: controller.signal }).then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<TradeLogEntry[]>;
      }),
    ])
      .then(([decisions, outcomes, trades]) => setRecentActivity({ kind: "loaded", decisions, outcomes, trades }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setRecentActivity({ kind: "error" });
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

  function submitUpdateHoldingWeight(ticker: string) {
    const raw = reconcileWeightInputs[ticker] ?? "";
    const weightPercent = Number.parseFloat(raw);
    if (raw.trim() === "" || Number.isNaN(weightPercent)) {
      setReconcileStatus((current) => ({
        ...current,
        [ticker]: { kind: "error", message: t("portfolio.holdings.errors.invalidPercentage") },
      }));
      return;
    }

    setReconcileStatus((current) => ({ ...current, [ticker]: { kind: "submitting" } }));
    fetch("/api/alpha-portfolio/reconcile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "UPDATE_HOLDING_WEIGHT", ticker, weightPercent }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setReconcileStatus((current) => ({
            ...current,
            [ticker]: { kind: "error", message: body.detail ?? t("common.invalidInput") },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const view = (await response.json()) as PortfolioView;
        setAlphaPortfolioData(view);
        setReconcileStatus((current) => ({ ...current, [ticker]: { kind: "idle" } }));
      })
      .catch((error: unknown) => {
        setReconcileStatus((current) => ({
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

  /** Product Sprint 8 (Portfolio Excellence, Deliverable 13 -- Daily
   * Brief Integration): the one priority-by-ticker map, built once from
   * the same shared Agenda fetch every attention-aware element on this
   * page reads from -- the Holdings Table's own Attention column, its
   * default sort, and the Pulse card's critical-item count all resolve
   * through this same map, so a holding can never be shown as Critical
   * in one place and Normal in another using separate logic. */
  const agendaItems = dailyBriefAgenda.kind === "loaded" ? dailyBriefAgenda.items : [];
  const priorityByTicker = new Map<string, PriorityLevel>();
  for (const item of agendaItems) {
    if (item.ticker) priorityByTicker.set(item.ticker, item.priority);
  }
  const criticalAgendaCount = agendaItems.filter((item) => item.priority === "critical").length;

  /** Same reasoning, for Portfolio Fit -- one ticker->assessment map,
   * shared by the Holdings Table's Fit column/sort and the Weakest
   * Holdings section below, both reading the one already-sorted
   * `/api/portfolio-fit/holdings` fetch. */
  const fitAssessments = portfolioFitHoldings.kind === "loaded" ? portfolioFitHoldings.assessments : [];
  const fitByTicker = new Map<string, PortfolioFitAssessmentView>();
  for (const assessment of fitAssessments) {
    fitByTicker.set(assessment.ticker, assessment);
  }

  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 6) -- one ticker->Stance map, the same
   * "single shared fetch, no divergent copies" pattern `fitByTicker`/
   * `priorityByTicker` above already establish, feeding the Holdings
   * Table's own Recommendation column and sort. */
  const stanceEntries = stanceHoldings.kind === "loaded" ? stanceHoldings.entries : [];
  const stanceByTicker = new Map<string, StanceLevel>();
  for (const entry of stanceEntries) {
    stanceByTicker.set(entry.ticker, entry.stance.level);
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <PortfolioPageHeader monitoringStatus={monitoringStatus} t={t} />

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
            {/* Implementation Sprint B2 (Hero Reordering): Decision
                First's own step 1 -- Atlas's conclusion, before any
                supporting data. */}
            <PortfolioOverallConclusion status={dailyBriefAgenda} t={t} />

            {status.view.awaitingReconciliation && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Text color="tertiary" role="status">
                    {t("portfolio.awaitingBanner.title")}
                  </Text>
                  <Text color="secondary">{t("portfolio.awaitingBanner.body")}</Text>
                  {!showReplaceForm && (
                    <div>
                      <Button variant="tertiary" onClick={openReplaceForm}>
                        {t("portfolio.replaceAllocationButton")}
                      </Button>
                    </div>
                  )}
                </Stack>
              </Surface>
            )}

            {showReplaceForm && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Heading level={2}>{t("portfolio.replaceForm.heading")}</Heading>
                  {replaceRows.map((row, index) => (
                    <Stack key={index} gap="inter-section">
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
                      <Divider tone="hairline" />
                    </Stack>
                  ))}
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
                        : t("portfolio.replaceForm.saveButton")}
                    </Button>{" "}
                    <Button variant="tertiary" onClick={() => setShowReplaceForm(false)}>
                      {t("common.cancel")}
                    </Button>
                  </div>
                </Stack>
              </Surface>
            )}

            {/* Deliverable 2, step 2: Attention Required -- the one
                shared `/api/daily-brief-agenda` fetch Daily Brief itself
                reads, filtered to this portfolio's own items. This is
                now Portfolio's *only* attention surface (Deliverable 4)
                -- the former, separately-derived "Needs Your Attention"
                section is gone; see this file's own module docstring. */}
            <AttentionRequiredSection status={dailyBriefAgenda} navigate={navigate} t={t} />

            {/* Pulse Simplification (live-verification follow-up):
                the one Decision Layer signal that answers "what
                should I do next" -- named, compact, right after
                Attention Required rather than buried at the very top
                mixed in among eight other widgets. */}
            <DecisionStatusSection actionDistribution={actionDistribution} opportunityCostBreakdown={opportunityCostBreakdown} t={t} />

            {/* Pulse Simplification: everything else that used to
                render unlabeled at the top of Portfolio -- real
                context, but "why", not "what to do" -- now lives
                behind one collapsed, per-widget-labeled detail. */}
            <DecisionLayerDetailSection
              convictionBreakdown={convictionBreakdown}
              decisionPathBreakdown={decisionPathBreakdown}
              decisionMemoryBreakdown={decisionMemoryBreakdown}
              decisionExplanationBreakdown={decisionExplanationBreakdown}
              decisionReliabilityBreakdown={decisionReliabilityBreakdown}
              portfolioSynthesisBreakdown={portfolioSynthesisBreakdown}
              sharedWeakPoints={sharedWeakPoints}
              t={t}
            />

            {/* Implementation Sprint B2 (Hero Reordering): Decision
                First's own step 4 -- Portfolio health, moved down from
                its former hero position (it used to render first, ahead
                of Atlas's own conclusion -- exactly the "raw stats
                before the opinion" ordering this sprint exists to fix).
                Unchanged data, unchanged component. */}
            <PortfolioPulse
              view={status.view}
              largestHolding={largestHolding}
              coveredCount={coveredCount}
              criticalAgendaCount={criticalAgendaCount}
              t={t}
            />

            {/* Deliverable 2, step 3: Holdings -- what do I own, in
                detail, ordered so what matters is on top by default. */}
            <Inline gap="inter-section" wrap align="start">
              <div style={{ flex: "3 1 480px", minWidth: 0 }}>
                <HoldingsTable
                  view={status.view}
                  cockpit={cockpit}
                  priorityByTicker={priorityByTicker}
                  fitByTicker={fitByTicker}
                  stanceByTicker={stanceByTicker}
                  caseCreateStatus={caseCreateStatus}
                  openInvestmentCase={openInvestmentCase}
                  expandedReconcileTicker={expandedReconcileTicker}
                  setExpandedReconcileTicker={setExpandedReconcileTicker}
                  reconcileWeightInputs={reconcileWeightInputs}
                  setReconcileWeightInputs={setReconcileWeightInputs}
                  reconcileStatus={reconcileStatus}
                  submitUpdateHoldingWeight={submitUpdateHoldingWeight}
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

            {/* Deliverable 2, step 5: Portfolio Fit -- best/worst fit
                today and improved/worsened, all from the one already-
                sorted `/api/portfolio-fit/holdings` fetch, the same
                engine Investment Case and Discovery read. */}
            <PortfolioFitOverviewSection status={portfolioFitHoldings} onOpenCase={openInvestmentCase} t={t} />

            {/* Deliverable 10 -- "where is capital least compelling?",
                reusing only Portfolio Fit and Decision Support, both
                already fetched above. Never a sell list. */}
            <WeakestHoldingsSection
              holdings={status.view.holdings}
              cockpit={cockpit}
              fitByTicker={fitByTicker}
              openInvestmentCase={openInvestmentCase}
              navigate={navigate}
              t={t}
            />

            {/* Deliverable 2, step 6 / Deliverable 11: Watchlist
                relationship -- entry points only, no duplicated
                Watchlist functionality on this page. */}
            <WatchlistRelationshipSection t={t} />

            <RecentActivitySection
              recentActivity={recentActivity}
              holdings={status.view.holdings}
              openInvestmentCase={openInvestmentCase}
              t={t}
            />
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
 * single-row title+stats layout. */
function PageTitle({ t }: { t: (key: TranslationKey) => string }) {
  return (
    <Inline gap="row" align="baseline" wrap>
      <Heading level={3} style={PAGE_TITLE_STYLE}>
        {t("portfolio.title")}
      </Heading>
      <RouterLink to="/portfolio/import" style={ACCENT_LINK_STYLE}>
        {t("portfolioImport.title")}
      </RouterLink>
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
  t,
}: {
  monitoringStatus: MonitoringOperationalStatusView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Stack gap="metadata">
      <PageTitle t={t} />
      {monitoringStatus && <MonitoringFreshnessNote status={monitoringStatus} t={t} />}
      {monitoringStatus && <ScopeFreshnessSummaryNote summary={monitoringStatus.portfolioFreshness} t={t} />}
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
 * -- the top-of-page status line: total value, holdings count, cash,
 * largest position, concentration, Atlas coverage, and a critical-item
 * pill sourced from the shared Daily Brief Agenda (Deliverable 13) --
 * never a second, independently-derived attention count. Every value
 * here is either read verbatim off the already-fetched `PortfolioView`
 * (cash, concentration) or a plain, undisputed derivation over it
 * (largest position = max-by-weight, computed once in `PortfolioPage`
 * and shared with the sidebar below rather than recomputed here). No
 * health score, grade, or synthetic risk score -- only real counts and
 * real values, honestly disclosed as unavailable where they are.
 * "Covered" is defined as any holding whose real `AnalysisCoverageLevel`
 * is not `no_coverage` -- a holding the cockpit hasn't resolved at all
 * does not count as covered either. Sector Allocation has no real
 * per-holding source anywhere in this codebase (grepped: no `sector`
 * field exists on any company/holding model) and is deliberately not
 * rendered here or anywhere else on this page.
 *
 * Pulse Simplification (live-verification follow-up): the ten Decision
 * Layer "portfolio breakdown" widgets (Deliverable 7/8 of eight
 * separate Decision Layer sprints, each individually correct as "one
 * compact summary line") used to all render here, stacked above this
 * card, before an investor had even seen what they own -- an
 * unlabeled wall of jargon-y counts nobody looked at in aggregate.
 * They are now split two ways and rendered as siblings, after this
 * card and Attention Required: the two that actually answer "what
 * should I do next" (Action Distribution, Opportunity Cost) live in
 * the small, named `DecisionStatusSection`; the rest (context that
 * explains *why*, not *what to do*) live behind one collapsed
 * `DecisionLayerDetailSection`, each under its own label. This
 * component itself only ever renders the real Pulse status line.
 */
function PortfolioPulse({
  view,
  largestHolding,
  coveredCount,
  criticalAgendaCount,
  t,
}: {
  view: PortfolioView;
  largestHolding: HoldingView | null;
  coveredCount: number | null;
  criticalAgendaCount: number;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const cashDisplay =
    view.cashValueAbsolute !== null
      ? view.cashValueAbsolute
      : view.cashWeightPercent !== null
        ? `${view.cashWeightPercent}%`
        : t("portfolio.header.notAvailable");

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
            <Label>{t("portfolio.pulse.holdingsLabel")}</Label>
            <Text as="span">{t("portfolio.pulse.holdingsCount", { count: view.numberOfHoldings })}</Text>
          </Stack>
          <Stack gap="metadata">
            <Label>{t("portfolio.pulse.cashLabel")}</Label>
            <Text as="span">{cashDisplay}</Text>
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
            <Label>{t("portfolio.pulse.concentrationLabel")}</Label>
            <Text as="span">
              {view.concentrationLevel && CONCENTRATION_LEVEL_KEY[view.concentrationLevel]
                ? t(CONCENTRATION_LEVEL_KEY[view.concentrationLevel]!)
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
          {criticalAgendaCount > 0 && (
            <StatusBadge label={t("portfolio.pulse.criticalPill", { count: criticalAgendaCount })} tone="critical" />
          )}
        </Inline>
      </Surface>
    </Stack>
  );
}

/**
 * Pulse Simplification (live-verification follow-up) -- the one Decision
 * Layer signal that actually answers "what should I do next" at a
 * portfolio level: Action Distribution (buy/add/hold/reduce/exit/wait
 * counts) and Opportunity Cost (capital-competition counts), named and
 * shown together, never mixed in among the other eight Decision Layer
 * widgets that only explain *why* (those live in
 * `DecisionLayerDetailSection` below). Neither underlying breakdown
 * component's own semantics change here -- both are reused verbatim,
 * this only adds a heading and decides where they render. Renders
 * nothing at all when both are genuinely empty, matching every
 * Decision Layer widget's own "no real signal, no line" convention.
 */
function DecisionStatusSection({
  actionDistribution,
  opportunityCostBreakdown,
  t,
}: {
  actionDistribution: PortfolioActionDistributionView | null;
  opportunityCostBreakdown: PortfolioOpportunityCostBreakdownView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const actionTotal = actionDistribution
    ? actionDistribution.buy.length +
      actionDistribution.add.length +
      actionDistribution.hold.length +
      actionDistribution.reduce.length +
      actionDistribution.exit.length +
      actionDistribution.wait.length +
      actionDistribution.noDecision.length
    : 0;
  const opportunityTotal = opportunityCostBreakdown
    ? opportunityCostBreakdown.holdingsCompetingForCapital.length +
      opportunityCostBreakdown.watchlistCompetingWithHoldings.length +
      opportunityCostBreakdown.waitingPreferable.length +
      opportunityCostBreakdown.noActionAppropriate.length
    : 0;
  if (actionTotal === 0 && opportunityTotal === 0) return null;

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("portfolio.decisionStatus.heading")}</Heading>
      {actionDistribution && <PortfolioActionDistribution distribution={actionDistribution} t={t} />}
      {opportunityCostBreakdown && <PortfolioOpportunityCostBreakdown breakdown={opportunityCostBreakdown} t={t} />}
    </Stack>
  );
}

/**
 * Pulse Simplification (live-verification follow-up) -- everywhere else
 * eight Decision Layer sprints each added their own "one compact
 * summary line" to the top of Portfolio (Recommendation Conviction,
 * Decision Path, Decision Memory, Decision Explanation, Decision
 * Reliability, Portfolio Synthesis, Evidence Graph Shared Weak Points),
 * plus Decision Readiness -- removed as a Portfolio Pulse row entirely,
 * not moved here, since its own information already lives on the
 * Holdings table's own Beslutsstöd/Uppmärksamhet columns and Attention
 * Required. Each was individually correct by its own sprint's stated
 * goal; stacked unlabeled at the very top of the page they read as
 * noise nobody could attribute to a system. None of that is a bug in
 * any one widget, so none of their own components or backend semantics
 * change here -- this only decides *where* they render (behind one
 * collapsed detail, reusing the exact `ExpandableDetail` primitive
 * `PortfolioSharedWeakPointsSection` already used) and adds one short
 * label per widget so a reader can tell which real Atlas system each
 * line came from -- the one thing none of the ten original lines did
 * for themselves. Decision Memory and Decision Explanation are kept as
 * two separate labeled entries, not merged, even though they answer a
 * similar "what changed" question -- a deliberate product decision,
 * not an oversight (see this file's own git history).
 */
function DecisionLayerDetailSection({
  convictionBreakdown,
  decisionPathBreakdown,
  decisionMemoryBreakdown,
  decisionExplanationBreakdown,
  decisionReliabilityBreakdown,
  portfolioSynthesisBreakdown,
  sharedWeakPoints,
  t,
}: {
  convictionBreakdown: PortfolioConvictionBreakdownView | null;
  decisionPathBreakdown: PortfolioDecisionPathBreakdownView | null;
  decisionMemoryBreakdown: PortfolioDecisionMemoryBreakdownView | null;
  decisionExplanationBreakdown: PortfolioDecisionExplanationBreakdownView | null;
  decisionReliabilityBreakdown: PortfolioReliabilityBreakdownView | null;
  portfolioSynthesisBreakdown: PortfolioSynthesisBreakdownView | null;
  sharedWeakPoints: PortfolioSharedWeakPointsView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const convictionTotal = convictionBreakdown
    ? convictionBreakdown.highestConviction.length +
      convictionBreakdown.lowestConviction.length +
      convictionBreakdown.evidenceLimited.length +
      convictionBreakdown.operationallyBlocked.length
    : 0;
  const decisionPathTotal = decisionPathBreakdown
    ? decisionPathBreakdown.closestToInvestable.length +
      decisionPathBreakdown.operationallyBlocked.length +
      decisionPathBreakdown.requiringMoreEvidence.length +
      decisionPathBreakdown.requiringDependencyResolution.length
    : 0;
  const decisionMemoryTotal = decisionMemoryBreakdown
    ? decisionMemoryBreakdown.recentlyChanged.length +
      decisionMemoryBreakdown.stable.length +
      decisionMemoryBreakdown.recentlyStrengthened.length +
      decisionMemoryBreakdown.recentlyWeakened.length
    : 0;
  const decisionExplanationTotal = decisionExplanationBreakdown
    ? decisionExplanationBreakdown.recentlyChanged.length +
      decisionExplanationBreakdown.newSupportingFindings.length +
      decisionExplanationBreakdown.resolvedBlockers.length +
      decisionExplanationBreakdown.recentlyStrengthened.length
    : 0;
  const decisionReliabilityTotal = decisionReliabilityBreakdown
    ? decisionReliabilityBreakdown.mostReliable.length +
      decisionReliabilityBreakdown.leastReliable.length +
      decisionReliabilityBreakdown.recentlyImproved.length +
      decisionReliabilityBreakdown.recentlyWeakened.length
    : 0;
  const portfolioSynthesisTotal = portfolioSynthesisBreakdown
    ? portfolioSynthesisBreakdown.supportsPortfolio.length +
      portfolioSynthesisBreakdown.highestCapitalCompetition.length +
      portfolioSynthesisBreakdown.conflictsWithPortfolio.length +
      portfolioSynthesisBreakdown.neutral.length
    : 0;
  const sharedWeakPointsTotal = sharedWeakPoints
    ? sharedWeakPoints.sharedWeakAssumptions.length + sharedWeakPoints.sharedConditions.length + sharedWeakPoints.sharedMissingEvidence.length
    : 0;
  const total =
    convictionTotal +
    decisionPathTotal +
    decisionMemoryTotal +
    decisionExplanationTotal +
    decisionReliabilityTotal +
    portfolioSynthesisTotal +
    sharedWeakPointsTotal;
  if (total === 0) return null;

  return (
    <ExpandableDetail summaryLabel={t("portfolio.decisionLayerDetail.summaryLabel")}>
      <Stack gap="inter-section">
        {convictionTotal > 0 && (
          <Stack gap="metadata">
            <Label>{t("portfolio.decisionLayerDetail.label.conviction")}</Label>
            <PortfolioConvictionBreakdown breakdown={convictionBreakdown!} t={t} />
          </Stack>
        )}
        {decisionPathTotal > 0 && (
          <Stack gap="metadata">
            <Label>{t("portfolio.decisionLayerDetail.label.decisionPath")}</Label>
            <PortfolioDecisionPathBreakdown breakdown={decisionPathBreakdown!} t={t} />
          </Stack>
        )}
        {decisionMemoryTotal > 0 && (
          <Stack gap="metadata">
            <Label>{t("portfolio.decisionLayerDetail.label.decisionMemory")}</Label>
            <PortfolioDecisionMemoryBreakdown breakdown={decisionMemoryBreakdown!} t={t} />
          </Stack>
        )}
        {decisionExplanationTotal > 0 && (
          <Stack gap="metadata">
            <Label>{t("portfolio.decisionLayerDetail.label.decisionExplanation")}</Label>
            <PortfolioDecisionExplanationBreakdown breakdown={decisionExplanationBreakdown!} t={t} />
          </Stack>
        )}
        {decisionReliabilityTotal > 0 && (
          <Stack gap="metadata">
            <Label>{t("portfolio.decisionLayerDetail.label.decisionReliability")}</Label>
            <PortfolioReliabilityBreakdown breakdown={decisionReliabilityBreakdown!} t={t} />
          </Stack>
        )}
        {portfolioSynthesisTotal > 0 && (
          <Stack gap="metadata">
            <Label>{t("portfolio.decisionLayerDetail.label.portfolioSynthesis")}</Label>
            <PortfolioSynthesisBreakdown breakdown={portfolioSynthesisBreakdown!} t={t} />
          </Stack>
        )}
        {sharedWeakPointsTotal > 0 && <PortfolioSharedWeakPointsSection points={sharedWeakPoints!} t={t} />}
      </Stack>
    </ExpandableDetail>
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

/**
 * Recent Activity (Portfolio Workspace v1) -- reuses `deriveActivity`
 * unfiltered, then shows the most recent few, newest first, matching
 * the approved frame's own bulleted "You recorded... / Atlas
 * update..." pattern as closely as real data allows. Atlas-authored
 * "coverage expanded" events have no real source anywhere (no
 * coverage-change history is persisted) and are never fabricated here
 * -- only real Decision/Outcome/Trade events, exactly as
 * `deriveActivity` already produces for History and Dashboard.
 */
const RECENT_ACTIVITY_COUNT = 4;

function RecentActivitySection({
  recentActivity,
  holdings,
  openInvestmentCase,
  t,
}: {
  recentActivity: RecentActivityFetchStatus;
  holdings: HoldingView[];
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (recentActivity.kind !== "loaded") return null;

  const holdingsLite = holdings.map((h) => ({
    ticker: h.ticker,
    caseId: h.caseId,
    reconciliationStatus: h.reconciliationStatus,
  }));
  const events = sortActivity(
    deriveActivity(recentActivity.decisions, recentActivity.outcomes, recentActivity.trades, holdingsLite),
    "newest",
  ).slice(0, RECENT_ACTIVITY_COUNT);

  return (
    <Stack gap="metadata">
      <Label>{t("portfolio.recentActivity.heading")}</Label>
      {events.length === 0 && <Text color="tertiary">{t("portfolio.recentActivity.empty")}</Text>}
      <Stack gap="row">
        {events.map((event) => (
          <RecentActivityRow
            key={`${event.kind}-${event.id}`}
            event={event}
            openInvestmentCase={openInvestmentCase}
            t={t}
          />
        ))}
      </Stack>
    </Stack>
  );
}

function RecentActivityRow({
  event,
  openInvestmentCase,
  t,
}: {
  event: ActivityEvent;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Link
      href="#"
      style={{ color: "var(--color-text-secondary)", textDecoration: "none" }}
      onClick={(clickEvent) => {
        clickEvent.preventDefault();
        openInvestmentCase(event.security, event.caseId);
      }}
    >
      {event.security} — {event.summary} · {formatRelativeTime(event.date, t)}
    </Link>
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
/** Product Sprint 8 (Portfolio Excellence, Deliverable 4) -- Portfolio's
 * one and only attention surface, renders the same `AgendaItemRow`
 * Daily Brief itself uses, for the items already filtered to
 * `group === "portfolio"`. A capped, collapsible list rather than every
 * item at once -- a busy portfolio's full agenda (including its
 * Watchlist items) still belongs on Daily Brief itself; this is the
 * portfolio-scoped subset, not a second full copy. `onOpenHolding` also
 * carries the real `AgendaItemView` through router state so the
 * per-holding detail page (`/portfolio/holding/:ticker`) can show the
 * exact same "why" text this row already showed, never a second,
 * independently-worded reason. */
const AGENDA_INITIAL_COUNT = 4;

/** Implementation Sprint B2 (Hero Reordering) -- Decision First's own
 * step 1 for Portfolio: one sentence, before anything else, reusing
 * the exact same `dailyBriefAgenda` fetch `AttentionRequiredSection`
 * already reads immediately below it (the portfolio-scoped subset,
 * already computed, never a second count derived independently -- the
 * two can never disagree about how many items there are). Renders
 * nothing while loading/erroring; `AttentionRequiredSection` already
 * owns disclosing those states with its own heading, so this line
 * would otherwise show and then immediately get replaced, a flash of
 * text no real reader benefits from. */
function PortfolioOverallConclusion({
  status,
  t,
}: {
  status: DailyBriefAgendaFetchStatus;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (status.kind !== "loaded") return null;
  const count = status.items.length;
  return (
    <Text as="p" style={{ fontFamily: "var(--type-family-prose)", fontSize: "var(--type-size-h5)", lineHeight: 1.6 }}>
      {count === 0
        ? t("portfolio.overallConclusion.noIssues")
        : t(count === 1 ? "portfolio.overallConclusion.attentionCountOne" : "portfolio.overallConclusion.attentionCountOther", {
            count,
          })}
    </Text>
  );
}

function AttentionRequiredSection({
  status,
  navigate,
  t,
}: {
  status: DailyBriefAgendaFetchStatus;
  navigate: ReturnType<typeof useNavigate>;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const [expanded, setExpanded] = useState(false);

  if (status.kind === "loading") {
    return (
      <Text role="status" aria-live="polite">
        {t("common.loading")}
      </Text>
    );
  }
  if (status.kind === "error" || status.items.length === 0) {
    return (
      <Stack gap="metadata">
        <Heading level={2}>{t("portfolio.attentionRequired.heading")}</Heading>
        <Text color="tertiary">{t("dailyBriefAgenda.empty.noItems")}</Text>
      </Stack>
    );
  }

  const visible = expanded ? status.items : status.items.slice(0, AGENDA_INITIAL_COUNT);
  const hiddenCount = status.items.length - visible.length;

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("portfolio.attentionRequired.heading")}</Heading>
      <Stack gap="inter-section">
        {visible.map((item) => (
          <AgendaItemRow
            key={item.id}
            item={item}
            onOpenInvestmentCase={(caseId, ticker) => navigate(`/investment-case/${caseId}`, { state: { origin: "portfolio", ticker } })}
            onOpenCandidate={(ticker) => navigate(`/discovery/candidate/${encodeURIComponent(ticker)}`)}
            onCompare={(ticker) => navigate(`/discovery/compare?a=${encodeURIComponent(ticker)}`)}
            onOpenHolding={(ticker) => navigate(`/portfolio/holding/${encodeURIComponent(ticker)}`, { state: { agendaItem: item } })}
            /* Internal Alpha Stabilization: this was a dead no-op click
               (`() => {}`) -- `AgendaItemRow` offers "Go to Portfolio"
               for a portfolio-level item with no ticker (e.g. large
               unallocated capital), and on every other page that's a
               real navigation to `/portfolio`. Already being on
               Portfolio, the honest equivalent is scrolling to the
               Portfolio Status / Allocation content at the top of this
               same page, not a link that visibly does nothing. */
            onGoToPortfolio={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          />
        ))}
      </Stack>
      {hiddenCount > 0 && (
        <Link href="#" style={{ color: "var(--global-color-accent)" }} onClick={(event) => { event.preventDefault(); setExpanded(true); }}>
          {t("portfolio.attention.viewAll")}
        </Link>
      )}
      {expanded && status.items.length > AGENDA_INITIAL_COUNT && (
        <Link href="#" style={{ color: "var(--global-color-accent)" }} onClick={(event) => { event.preventDefault(); setExpanded(false); }}>
          {t("portfolio.attention.viewFewer")}
        </Link>
      )}
    </Stack>
  );
}

/** Deliverable 7 (Portfolio Fit Engine) -- groups the same, already-
 * loaded `assessments` list four ways: Best Fit Today (top of the
 * server's best-first order), Weakest Fit Today (bottom of it),
 * Improved and Worsened (`.trend`, sourced from the existing Change
 * Intelligence signal, computed by the backend, never a client-side
 * recomputation). A holding appearing in none of the four groups
 * (rated `neutral`/`unavailable` fit with an `unchanged`/`unavailable`
 * trend) simply does not appear here -- this section highlights the
 * holdings worth a second look, not a full re-listing of the Holdings
 * Table below it. */
const FIT_OVERVIEW_GROUP_SIZE = 3;

function PortfolioFitOverviewSection({
  status,
  onOpenCase,
  t,
}: {
  status: PortfolioFitFetchStatus;
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
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
        <Heading level={2}>{t("portfolioFit.portfolioSection.heading")}</Heading>
        <Text color="tertiary">{t("portfolioFit.portfolioSection.empty")}</Text>
      </Stack>
    );
  }

  const evaluated = status.assessments.filter((a) => a.overall !== "unavailable");
  const bestFit = evaluated.slice(0, FIT_OVERVIEW_GROUP_SIZE);
  const weakestFit = [...evaluated].reverse().slice(0, FIT_OVERVIEW_GROUP_SIZE).filter((a) => !bestFit.includes(a));
  const improved = status.assessments.filter((a) => a.trend === "improving");
  const worsened = status.assessments.filter((a) => a.trend === "declining");

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("portfolioFit.portfolioSection.heading")}</Heading>
      <Inline gap="inter-section" wrap align="start">
        <FitGroupColumn heading={t("portfolioFit.portfolioSection.bestFit")} assessments={bestFit} onOpenCase={onOpenCase} t={t} />
        <FitGroupColumn heading={t("portfolioFit.portfolioSection.weakestFit")} assessments={weakestFit} onOpenCase={onOpenCase} t={t} />
        <FitGroupColumn heading={t("portfolioFit.portfolioSection.improved")} assessments={improved} onOpenCase={onOpenCase} t={t} />
        <FitGroupColumn heading={t("portfolioFit.portfolioSection.worsened")} assessments={worsened} onOpenCase={onOpenCase} t={t} />
      </Inline>
    </Stack>
  );
}

function FitGroupColumn({
  heading,
  assessments,
  onOpenCase,
  t,
}: {
  heading: string;
  assessments: PortfolioFitAssessmentView[];
  onOpenCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (assessments.length === 0) return null;
  return (
    <Stack gap="metadata" style={{ flex: "1 1 200px", minWidth: 0 }}>
      <Label>{heading}</Label>
      {assessments.map((assessment) => (
        <Link
          key={assessment.caseId}
          href="#"
          style={{ color: "var(--color-text-primary)", textDecoration: "none", display: "block" }}
          onClick={(event) => {
            event.preventDefault();
            onOpenCase(assessment.ticker, assessment.caseId);
          }}
        >
          <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
            <Text as="span" color="secondary">
              {assessment.ticker}
            </Text>
            <FitBadge rating={assessment.overall} />
          </Inline>
        </Link>
      ))}
    </Stack>
  );
}

const HOLDING_SORT_KEYS: HoldingSortKey[] = ["attention", "weight", "fit", "coverage", "stance", "alphabetical"];

const HOLDING_SORT_LABEL_KEY: Record<HoldingSortKey, TranslationKey> = {
  attention: "portfolio.holdingsTable.sort.attention",
  weight: "portfolio.holdingsTable.sort.weight",
  fit: "portfolio.holdingsTable.sort.fit",
  coverage: "coverage.portfolio.sortLabel",
  stance: "stance.portfolio.sortLabel",
  alphabetical: "portfolio.holdingsTable.sort.alphabetical",
};

function HoldingsTable({
  view,
  cockpit,
  priorityByTicker,
  fitByTicker,
  stanceByTicker,
  caseCreateStatus,
  openInvestmentCase,
  expandedReconcileTicker,
  setExpandedReconcileTicker,
  reconcileWeightInputs,
  setReconcileWeightInputs,
  reconcileStatus,
  submitUpdateHoldingWeight,
  t,
}: {
  view: PortfolioView;
  cockpit: PortfolioCockpitFetchStatus;
  priorityByTicker: Map<string, PriorityLevel>;
  fitByTicker: Map<string, PortfolioFitAssessmentView>;
  stanceByTicker: Map<string, StanceLevel>;
  caseCreateStatus: Record<string, CaseCreateStatus>;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  expandedReconcileTicker: string | null;
  setExpandedReconcileTicker: (ticker: string | null) => void;
  reconcileWeightInputs: Record<string, string>;
  setReconcileWeightInputs: (updater: (current: Record<string, string>) => Record<string, string>) => void;
  reconcileStatus: Record<string, ReconcileStatus>;
  submitUpdateHoldingWeight: (ticker: string) => void;
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
  /** Deliverable 6 (Holding Ordering) -- defaults to "attention" so the
   * portfolio is useful immediately; the other three are cheap client-
   * side re-sorts over data already on the page, no new fetch. */
  const [sortKey, setSortKey] = useState<HoldingSortKey>("attention");
  const fitRatingByTicker = new Map<string, FitRating>();
  for (const [ticker, assessment] of fitByTicker) {
    fitRatingByTicker.set(ticker, assessment.overall);
  }
  /** Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine,
   * Deliverable 6): the "coverage" sort key reuses `cockpit`'s own
   * already-fetched per-holding `analysisCoverage.level` -- no new
   * fetch, matching `fitRatingByTicker`'s own pattern above. */
  const coverageByTicker = new Map<string, AnalysisCoverageLevel>();
  if (cockpit.kind === "loaded") {
    for (const holding of cockpit.report.holdings) {
      coverageByTicker.set(holding.ticker, holding.analysisCoverage.level);
    }
  }
  const orderedHoldings = sortHoldings(
    view.holdings,
    sortKey,
    priorityByTicker,
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
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.tickerHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.valueHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.shareHeader")}</th>
                {/* Internal Alpha Stabilization: was the full "Portfolio
                    Fit" section heading, verbatim -- a visibly longer,
                    differently-registered label than every neighboring
                    single-word column header, and a literal duplicate of
                    the section heading rendered lower on this same page.
                    `fitHeader` ("Fit") already existed for exactly this
                    column but had gone unused since an earlier table
                    redesign; revived rather than adding a new key. */}
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.fitHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.decisionSupportHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.attentionHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.coverageHeader")}</th>
                <th style={headerCellStyle}>{t("stance.portfolio.columnLabel")}</th>
              </tr>
            </thead>
            <tbody>
              {visibleHoldings.map((holding) => {
                const cockpitHolding =
                  cockpit.kind === "loaded"
                    ? cockpit.report.holdings.find((h) => h.ticker === holding.ticker)
                    : undefined;
                const isUnresolvedInCockpit =
                  cockpit.kind === "loaded" &&
                  cockpit.report.unresolvedHoldings.some((h) => h.ticker === holding.ticker);

                return (
                  <HoldingsTableRow
                    key={holding.ticker}
                    holding={holding}
                    cockpitHolding={cockpitHolding}
                    isUnresolvedInCockpit={isUnresolvedInCockpit}
                    fitAssessment={fitByTicker.get(holding.ticker)}
                    stanceLevel={stanceByTicker.get(holding.ticker)}
                    priority={priorityByTicker.get(holding.ticker)}
                    thisCaseCreateStatus={caseCreateStatus[holding.ticker] ?? { kind: "idle" }}
                    thisReconcileStatus={reconcileStatus[holding.ticker] ?? { kind: "idle" }}
                    openInvestmentCase={openInvestmentCase}
                    isReconcileExpanded={expandedReconcileTicker === holding.ticker}
                    onToggleReconcile={() =>
                      setExpandedReconcileTicker(expandedReconcileTicker === holding.ticker ? null : holding.ticker)
                    }
                    reconcileWeightInput={reconcileWeightInputs[holding.ticker] ?? ""}
                    onReconcileWeightInputChange={(value) =>
                      setReconcileWeightInputs((current) => ({ ...current, [holding.ticker]: value }))
                    }
                    submitUpdateHoldingWeight={submitUpdateHoldingWeight}
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
 * One dense, clickable row. `role="button"`/`tabIndex`/`onKeyDown` make
 * the whole row a keyboard-operable navigation target (Enter/Space open
 * the Investment Case) rather than requiring a separate visible button
 * per row -- consistent with "the user should never feel they are
 * leaving the Portfolio workspace" and this sprint's density goal. The
 * inline Reconcile toggle stops event propagation so clicking it never
 * also triggers row navigation.
 */
function HoldingsTableRow({
  holding,
  cockpitHolding,
  isUnresolvedInCockpit,
  fitAssessment,
  stanceLevel,
  priority,
  thisCaseCreateStatus,
  thisReconcileStatus,
  openInvestmentCase,
  isReconcileExpanded,
  onToggleReconcile,
  reconcileWeightInput,
  onReconcileWeightInputChange,
  submitUpdateHoldingWeight,
  cellStyle,
  t,
}: {
  holding: HoldingView;
  cockpitHolding: PortfolioCockpitHoldingView | undefined;
  isUnresolvedInCockpit: boolean;
  fitAssessment: PortfolioFitAssessmentView | undefined;
  stanceLevel: StanceLevel | undefined;
  priority: PriorityLevel | undefined;
  thisCaseCreateStatus: CaseCreateStatus;
  thisReconcileStatus: ReconcileStatus;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  isReconcileExpanded: boolean;
  onToggleReconcile: () => void;
  reconcileWeightInput: string;
  onReconcileWeightInputChange: (value: string) => void;
  submitUpdateHoldingWeight: (ticker: string) => void;
  cellStyle: CSSProperties;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const isCreating = thisCaseCreateStatus.kind === "creating";
  const isAwaitingReconciliation = holding.reconciliationStatus === "AWAITING_RECONCILIATION";
  const navigate = useNavigate();

  /** Company Workspace v1 -- Holdings rows now open the Company
   * Workspace first (Portfolio -> Company -> Investment Case), rather
   * than jumping straight to Investment Case as before. A holding with
   * no Case yet still needs `openInvestmentCase`'s own create-then-open
   * flow, since Company Workspace has nothing to resolve without a
   * `caseId` -- only an already-cased holding routes through Company
   * Workspace. */
  function handleRowActivate() {
    if (isCreating) return;
    if (holding.caseId) {
      navigate(`/company/${encodeURIComponent(holding.ticker)}`);
      return;
    }
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
            <Text as="span">{holding.ticker}</Text>
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
                  onToggleReconcile();
                }}
              >
                {isReconcileExpanded ? t("common.cancel") : t("portfolio.holdingsTable.reconcileToggle")}
              </Link>
            )}
          </Inline>
        </td>
        <td style={cellStyle}>{holding.valueAbsolute !== null ? holding.valueAbsolute : "—"}</td>
        <td style={cellStyle}>{holding.weightPercent}%</td>
        <td style={cellStyle}>
          {fitAssessment ? (
            <FitBadge rating={fitAssessment.overall} />
          ) : (
            <Text color="tertiary" as="span">
              {t("portfolio.header.notAvailable")}
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(DECISION_SUPPORT_BADGE_KEY[cockpitHolding.decisionSupport.level])}
              tone={DECISION_SUPPORT_TONE[cockpitHolding.decisionSupport.level]}
            />
          ) : (
            <Text color="tertiary" as="span">
              {t("portfolio.holdingsTable.coverage.new")}
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {priority ? (
            <PriorityBadge priority={priority} />
          ) : (
            <Text color="tertiary" as="span">
              {t("portfolio.holdingsTable.attention.none")}
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusText
              label={t(COVERAGE_DISPLAY_KEY[cockpitHolding.analysisCoverage.level])}
              tone={ANALYSIS_COVERAGE_TONE[cockpitHolding.analysisCoverage.level]}
            />
          ) : (
            <StatusText label={t("portfolio.holdingsTable.coverage.new")} />
          )}
        </td>
        <td style={cellStyle}>
          {stanceLevel ? (
            <StanceBadge level={stanceLevel} />
          ) : (
            <Text color="tertiary" as="span">
              {t("portfolio.holdingsTable.coverage.new")}
            </Text>
          )}
        </td>
      </tr>
      {isReconcileExpanded && (
        <tr>
          <td colSpan={8} style={cellStyle}>
            <Stack gap="inter-section">
              <Text color="tertiary" as="p">
                {t("portfolio.holdings.awaitingReconciliation")}
              </Text>
              <Text as="label">
                {t("portfolio.holdings.newWeightLabel")}
                <br />
                <input
                  value={reconcileWeightInput}
                  onChange={(event) => onReconcileWeightInputChange(event.target.value)}
                />
              </Text>
              <div>
                <Button
                  variant="tertiary"
                  onClick={() => submitUpdateHoldingWeight(holding.ticker)}
                  disabled={thisReconcileStatus.kind === "submitting"}
                >
                  {thisReconcileStatus.kind === "submitting"
                    ? t("portfolio.holdings.updating")
                    : t("portfolio.holdings.updateButton")}
                </Button>
              </div>
              {thisReconcileStatus.kind === "error" && (
                <Text color="tertiary" role="alert">
                  {thisReconcileStatus.message}
                </Text>
              )}
            </Stack>
          </td>
        </tr>
      )}
    </>
  );
}

/**
 * Weakest Holdings / Capital Competition (Product Sprint 8, Deliverable
 * 10) -- answers "where in my portfolio is capital currently least
 * compelling?" using only two already-fetched, real signals: Portfolio
 * Fit (`weak`/`poor`) and Decision Support (`reduction_supported`/
 * `exit_supported` -- both real, existing evidence-support states, the
 * same seven-member enum Investment Case's own Decision Support badge
 * already uses). A holding qualifies if either signal flags it; neither
 * signal is a sell recommendation on its own, and this section never
 * computes a new one -- it only surfaces the two real signals side by
 * side per holding and offers investigation, never action ("Review
 * position" / "Compare alternatives" / "Open Investment Case"), per
 * this deliverable's own explicit "not automatically a Sell list" rule.
 * Capped and ordered by weight desc, so the largest capital-competition
 * candidate is the one most worth a look first.
 */
const WEAK_FIT_RATINGS: FitRating[] = ["weak", "poor"];
const WEAK_DECISION_SUPPORT: DecisionSupportLevel[] = ["reduction_supported", "exit_supported"];
const WEAKEST_HOLDINGS_CAP = 6;

function WeakestHoldingsSection({
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
      const weakFit = fit && WEAK_FIT_RATINGS.includes(fit.overall) ? fit : null;
      const weakDecisionSupport =
        cockpitHolding && WEAK_DECISION_SUPPORT.includes(cockpitHolding.decisionSupport.level)
          ? cockpitHolding.decisionSupport
          : null;
      if (!weakFit && !weakDecisionSupport) return null;
      return { holding, cockpitHolding, weakFit, weakDecisionSupport };
    })
    .filter((c): c is NonNullable<typeof c> => c !== null)
    .sort((a, b) => b.holding.weightPercent - a.holding.weightPercent)
    .slice(0, WEAKEST_HOLDINGS_CAP);

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("portfolio.weakestHoldings.heading")}</Heading>
      <Text color="tertiary" as="p">
        {t("portfolio.weakestHoldings.subheading")}
      </Text>
      {candidates.length === 0 && <Text color="secondary">{t("portfolio.weakestHoldings.empty")}</Text>}
      <Stack gap="row">
        {candidates.map(({ holding, weakFit, weakDecisionSupport }) => (
          <Surface tier="primary" key={holding.ticker}>
            <Stack gap="metadata">
              <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
                <Text as="span" style={{ fontWeight: 600 }}>
                  {holding.ticker}
                </Text>
                <Text as="span" color="secondary">
                  {holding.weightPercent}%
                </Text>
              </Inline>
              <Inline gap="row" wrap>
                {weakFit && <FitBadge rating={weakFit.overall} />}
                {weakDecisionSupport && (
                  <StatusBadge
                    label={t(DECISION_SUPPORT_BADGE_KEY[weakDecisionSupport.level])}
                    tone={DECISION_SUPPORT_TONE[weakDecisionSupport.level]}
                  />
                )}
              </Inline>
              <Inline gap="row" wrap>
                <Link
                  href="#"
                  style={{ color: "var(--global-color-accent)" }}
                  onClick={(event) => {
                    event.preventDefault();
                    navigate(`/portfolio/holding/${encodeURIComponent(holding.ticker)}`);
                  }}
                >
                  {t("portfolio.weakestHoldings.reviewPosition")} →
                </Link>
                <Link
                  href="#"
                  style={{ color: "var(--global-color-accent)" }}
                  onClick={(event) => {
                    event.preventDefault();
                    navigate(`/discovery/compare?a=${encodeURIComponent(holding.ticker)}`);
                  }}
                >
                  {t("portfolio.weakestHoldings.compareAlternatives")} →
                </Link>
                {holding.caseId && (
                  <Link
                    href="#"
                    style={{ color: "var(--global-color-accent)" }}
                    onClick={(event) => {
                      event.preventDefault();
                      openInvestmentCase(holding.ticker, holding.caseId);
                    }}
                  >
                    {t("dailyBriefAgenda.action.openInvestmentCase")} →
                  </Link>
                )}
              </Inline>
            </Stack>
          </Surface>
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
 * in the Weakest Holdings section above and every Holdings Table row,
 * both reusing the same existing Compare route.
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
