import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Label, Link, Stack, StatusBadge, StatusText, Surface, Text, VisuallyHidden } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  derivePortfolioActions,
  type PortfolioAction,
} from "../portfolio/derivePortfolioActions";
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
  CONVICTION_LEVEL_KEY,
  CONVICTION_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  RISK_STATUS_TONE,
  ANALYSIS_COVERAGE_TONE,
  type AnalysisCoverageLevel,
  type ConvictionLevel,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type ReviewPriority,
} from "../status/statusTone";
import type { StatusTone } from "../foundation";
import { RISK_STATUS_KEY, type AnalysisRiskStatus } from "../changeIntelligence/describeChange";
import { describePortfolioAction, SEVERITY_EMOJI } from "../portfolio/describePortfolioAction";

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

/** Holdings table Review Status column -- derived from the real
 * `ReviewPriority` enum already computed server-side
 * (`PortfolioHoldingAnalysisView.attention.priority`), never a second
 * client-side judgment. */
function reviewStatusKeyFor(priority: ReviewPriority): TranslationKey {
  return priority === "priority_review" || priority === "evidence_review"
    ? "portfolio.holdingsTable.reviewStatus.needsReview"
    : "portfolio.holdingsTable.reviewStatus.reviewed";
}

function reviewStatusToneFor(priority: ReviewPriority): StatusTone {
  return priority === "priority_review" || priority === "evidence_review" ? "caution" : "positive";
}

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
 * ATLAS-015 Portfolio Status — a workflow-completeness summary, not an
 * analysis: every field here is a count or verbatim value already
 * present in Alpha/Core data (see `atlas/alpha/portfolio_status
 * /service.py`). `category`/`topCategory` are internal enum values, the
 * same "raw English on the wire, translated only at display time"
 * pattern `decisionType`/`transactionType` already use elsewhere.
 */
type AttentionCategory =
  | "MISSING_CASE"
  | "DECISION_WITHOUT_OUTCOME"
  | "OUTCOME_WITHOUT_EXECUTION"
  | "AWAITING_RECONCILIATION"
  | "VERY_OLD_CASE"
  | "OBSERVATION_WITHOUT_DECISION";

interface PortfolioSummaryMetrics {
  holdingsCount: number;
  largestPositionTicker: string | null;
  largestPositionWeightPercent: number | null;
  numberOfInvestmentCases: number;
  openDecisions: number;
  pendingOutcomes: number;
  pendingExecutions: number;
  concentrationLevel: string | null;
  unallocatedPercent: number | null;
}

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

interface PortfolioHealthView {
  holdingsWithCaseCount: number;
  holdingsCount: number;
  mostRecentDecisionAt: string | null;
  outstandingWorkflowItems: number;
  allocatedPercent: number | null;
  unknownInstrumentTickers: string[];
}

interface PortfolioStatusView {
  exists: boolean;
  summary: PortfolioSummaryMetrics | null;
  attentionItems: AttentionItemView[];
  reviewQueue: ReviewQueueItemView[];
  health: PortfolioHealthView | null;
}

/**
 * ATLAS-016 Portfolio Intelligence -- consumes the canonical Decision
 * Engine pipeline plus `PortfolioStatusService` (see
 * `atlas/alpha/portfolio_intelligence/service.py`). Every `kind` value
 * is raw English on the wire, translated only at display time by this
 * component -- the same `category`/`concentrationLevel` pattern already
 * used above. Nothing here is computed in the browser.
 */
type KeyFindingKind =
  | "high_concentration"
  | "elevated_concentration"
  | "large_unallocated"
  | "multiple_missing_cases"
  | "multiple_stale_cases"
  | "multiple_evidence_gaps";

type ConsiderKind =
  | "open_investment_case"
  | "gather_evidence"
  | "review_thesis"
  | "update_case"
  | "review_concentration";

type RiskSignalKind =
  | "high_concentration"
  | "missing_case"
  | "missing_evidence"
  | "awaiting_reconciliation"
  | "stale_review";

type EvidenceGapKind =
  | "no_evidence_recorded"
  | "observation_without_evidence"
  | "decision_without_linked_observation";

interface KeyFindingView {
  kind: KeyFindingKind;
  count: number;
  tickers: string[];
}

interface ConsiderItemView {
  kind: ConsiderKind;
  ticker: string;
  caseId: string | null;
  confidence: EvidenceCoverageLevel;
  relatedHoldings: string[];
  evidenceGapCount: number | null;
  ageDays: number | null;
  weightPercent: number | null;
  pendingItemCount: number | null;
}

interface RiskSignalView {
  kind: RiskSignalKind;
  ticker: string;
  caseId: string | null;
  ageDays: number | null;
}

interface MissingEvidenceItemView {
  ticker: string;
  caseId: string;
  gapKind: EvidenceGapKind;
  reference: string | null;
}

/** Figma-fidelity rebuild -- the Key Findings panel's enum-to-copy map.
 * `describePortfolioAction.ts`'s own concentration-action reason points
 * at the same two `portfolio.intelligence.keyFindings.*` translation
 * keys directly (that module can't import this route file), so both
 * surfaces render identical concentration wording without a route-to-
 * shared-module dependency inversion. */
const KEY_FINDING_KEY: Record<KeyFindingKind, TranslationKey> = {
  high_concentration: "portfolio.intelligence.keyFindings.high_concentration",
  elevated_concentration: "portfolio.intelligence.keyFindings.elevated_concentration",
  large_unallocated: "portfolio.intelligence.keyFindings.large_unallocated",
  multiple_missing_cases: "portfolio.intelligence.keyFindings.multiple_missing_cases",
  multiple_stale_cases: "portfolio.intelligence.keyFindings.multiple_stale_cases",
  multiple_evidence_gaps: "portfolio.intelligence.keyFindings.multiple_evidence_gaps",
};

/** Figma-fidelity rebuild -- ticker-bearing reason phrasings for the
 * Risk Signals panel, the same real `RiskSignalKind` enum
 * `/alpha-portfolio/intelligence` already returns. */
const RISK_SIGNAL_KEY: Record<RiskSignalKind, TranslationKey> = {
  high_concentration: "portfolio.riskSignals.high_concentration",
  missing_case: "portfolio.riskSignals.missing_case",
  missing_evidence: "portfolio.riskSignals.missing_evidence",
  awaiting_reconciliation: "portfolio.riskSignals.awaiting_reconciliation",
  stale_review: "portfolio.riskSignals.stale_review",
};

interface PortfolioFitStatusView {
  available: boolean;
  reason: string | null;
}

interface PortfolioIntelligenceView {
  exists: boolean;
  overview: PortfolioSummaryMetrics | null;
  cashWeightPercent: number | null;
  cashValueAbsolute: number | null;
  keyFindings: KeyFindingView[];
  considerItems: ConsiderItemView[];
  riskSignals: RiskSignalView[];
  missingEvidence: MissingEvidenceItemView[];
  portfolioFit: PortfolioFitStatusView;
}


/**
 * Portfolio Workspace v3: lowered from 3 (ATLAS UI Sprint) to 2 per
 * this sprint's explicit "small, actionable list" / "understand in
 * less than ten seconds" requirement -- its own worked example shows
 * exactly one item per severity tier. Still capped *per tier*, not with
 * one flat cap across all three, for the same reason established
 * previously: a portfolio with many High-priority evidence gaps must
 * never crowd the Medium tier (e.g. portfolio allocation) out entirely.
 */
const MAX_ACTIONS_PER_SEVERITY = 2;

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

/** Fetched independently from `PortfolioView` -- a failure here never
 *  blocks Holdings from rendering; the Intelligence cards just don't
 *  appear (see the render logic below). */
type PortfolioStatusFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: PortfolioStatusView };

/** Same independent-fetch pattern as `PortfolioStatusFetchStatus` --
 *  ATLAS-016's sections simply don't render on failure. */
type PortfolioIntelligenceFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: PortfolioIntelligenceView };

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

/** Visual Fidelity Pass -- Figma's own navigation links ("Import
 * Portfolio", "View All Holdings") render in the accent color, not the
 * Foundation `Link` component's default tertiary gray. Scoped to this
 * page's `RouterLink` usages only (the shared `Link`/`Link.module.css`
 * default is left alone -- out of scope for this pass). */
const ACCENT_LINK_STYLE: CSSProperties = {
  color: "var(--global-color-accent)",
  textDecoration: "none",
  fontSize: "var(--type-body-min-size)",
};

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
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatusFetchStatus>({ kind: "loading" });
  const [portfolioIntelligence, setPortfolioIntelligence] = useState<PortfolioIntelligenceFetchStatus>({
    kind: "loading",
  });
  const [cockpit, setCockpit] = useState<PortfolioCockpitFetchStatus>({ kind: "loading" });
  const [recentActivity, setRecentActivity] = useState<RecentActivityFetchStatus>({ kind: "loading" });
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

    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<PortfolioView>;
      })
      .then((view) => setStatus({ kind: "loaded", view }))
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

    fetch("/api/alpha-portfolio/status", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
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
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<PortfolioIntelligenceView>;
      })
      .then((report) => setPortfolioIntelligence({ kind: "loaded", report }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioIntelligence({ kind: "error" });
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
      navigate(`/investment-case/${existingCaseId}`, { state: { origin: "portfolio" } });
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
            navigate(`/investment-case/${linked.caseId}`, { state: { origin: "portfolio" } });
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
        setStatus({ kind: "loaded", view });
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
        setStatus({ kind: "loaded", view });
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

  const resolvedStatusReport =
    portfolioStatus.kind === "loaded" && portfolioStatus.report.exists ? portfolioStatus.report : null;
  const resolvedIntelligenceReport =
    portfolioIntelligence.kind === "loaded" && portfolioIntelligence.report.exists
      ? portfolioIntelligence.report
      : null;

  /** Portfolio Workspace v1 -- computed once here and shared by the
   * Pulse card's attention count and the Needs Your Attention list
   * below, so the two numbers can never drift apart the way two
   * independent computations over the same signals could. */
  const allActions = derivePortfolioActions(
    resolvedStatusReport?.reviewQueue ?? [],
    resolvedIntelligenceReport?.missingEvidence.map((item) => ({ ticker: item.ticker, caseId: item.caseId })) ?? [],
    resolvedIntelligenceReport?.keyFindings ?? [],
    resolvedStatusReport?.summary?.unallocatedPercent ?? null,
    resolvedStatusReport?.attentionItems.map((item) => ({
      ticker: item.ticker,
      category: item.category,
      ageDays: item.ageDays,
    })) ?? [],
  );

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        {!(status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0) && (
          <PageTitle t={t} />
        )}

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
            <PortfolioPulse view={status.view} cockpit={cockpit} attentionCount={allActions.length} t={t} />

            <NeedsYourAttention actions={allActions} openInvestmentCase={openInvestmentCase} t={t} />

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

            <Inline gap="inter-section" wrap align="start">
              <div style={{ flex: "3 1 480px", minWidth: 0 }}>
                <HoldingsTable
                  view={status.view}
                  cockpit={cockpit}
                  unallocatedPercent={unallocatedPercent}
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
              <div style={{ flex: "1 1 260px", minWidth: 0 }}>
                <PortfolioSidebar view={status.view} cockpit={cockpit} t={t} />
              </div>
            </Inline>

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
 * Portfolio Pulse (Portfolio Workspace v1, replaces `PortfolioHeaderBar`)
 * -- the approved `portfolio-workspace` frame's stat row: total value,
 * holdings count, Atlas coverage ("X of Y covered"), and the attention
 * pill. "Covered" is defined as any holding whose real
 * `AnalysisCoverageLevel` is not `no_coverage` -- a holding the cockpit
 * hasn't resolved at all does not count as covered either. Sector
 * Allocation has no real per-holding source anywhere in this codebase
 * (grepped: no `sector` field exists on any company/holding model) and
 * is deliberately not rendered here, matching the precedent already
 * set by `PortfolioIntelligencePanels`'s own docstring for the exact
 * same situation -- never the fabricated allocation Figma shows.
 */
function PortfolioPulse({
  view,
  cockpit,
  attentionCount,
  t,
}: {
  view: PortfolioView;
  cockpit: PortfolioCockpitFetchStatus;
  attentionCount: number;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const coveredCount =
    cockpit.kind === "loaded"
      ? cockpit.report.holdings.filter((h) => h.analysisCoverage.level !== "no_coverage").length
      : null;

  return (
    <Stack gap="metadata">
      <Inline gap="row" align="baseline" wrap>
        <Heading level={3} style={PAGE_TITLE_STYLE}>
          {t("portfolio.title")}
        </Heading>
        <RouterLink to="/portfolio/import" style={ACCENT_LINK_STYLE}>
          {t("portfolioImport.title")}
        </RouterLink>
      </Inline>
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
            <Label>{t("portfolio.pulse.coverageLabel")}</Label>
            <Text as="span">
              {coveredCount !== null
                ? t("portfolio.pulse.coverageValue", { covered: coveredCount, total: view.numberOfHoldings })
                : t("portfolio.header.notAvailable")}
            </Text>
          </Stack>
          {attentionCount > 0 && (
            <StatusBadge label={t("portfolio.pulse.attentionPill", { count: attentionCount })} tone="caution" />
          )}
        </Inline>
      </Surface>
    </Stack>
  );
}

const PRIORITY_STRIP_INITIAL_COUNT = 4;

/**
 * Figma-fidelity rebuild -- a single dense, wrapped line (dot + title +
 * reason per item, line-wrap doing the separating) plus a "View all N"
 * expand toggle, replacing the previous grouped-by-severity-tier
 * stacked cards: the approved Figma screen shows one flat, ordered
 * list, never three headed groups. `derivePortfolioActions` already
 * returns actions most-severe-first, so slicing its output is the
 * entire "which N to show" decision -- no new ranking logic. Each item
 * with a real ticker is itself the click target (Figma shows no
 * separate per-item button in the strip, only "View all N"); items
 * with no ticker (the portfolio-level allocation action) render as
 * plain text, matching Figma's own last strip item.
 */
const ATTENTION_INITIAL_COUNT = 2;

/**
 * Needs Your Attention (Portfolio Workspace v1, replaces `PriorityStrip`)
 * -- card-row list matching the approved frame: ticker + title + reason
 * + chevron, each row linking to the new per-holding attention detail
 * page (`/portfolio/holding/:ticker`) rather than straight into the
 * Investment Case, since the approved flow is List -> Attention Detail
 * -> Record a Decision -> Investment Case. Items with no ticker (the
 * portfolio-level allocation action) render as plain text, matching
 * the same convention the old strip already used. Reuses
 * `derivePortfolioActions`'s own severity ordering unchanged -- no new
 * ranking logic.
 */
function NeedsYourAttention({
  actions,
  openInvestmentCase,
  t,
}: {
  actions: PortfolioAction[];
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const [expanded, setExpanded] = useState(false);

  if (actions.length === 0) {
    return (
      <Stack gap="metadata">
        <Label>{t("portfolio.attention.heading")}</Label>
        <Text color="secondary">{t("portfolio.attention.empty")}</Text>
      </Stack>
    );
  }

  const visible = expanded ? actions : actions.slice(0, ATTENTION_INITIAL_COUNT);
  const hiddenCount = actions.length - visible.length;

  return (
    <Stack gap="metadata">
      <Label>{t("portfolio.attention.heading")}</Label>
      <Stack gap="row">
        {visible.map((action) => (
          <NeedsYourAttentionRow key={action.id} action={action} openInvestmentCase={openInvestmentCase} t={t} />
        ))}
      </Stack>
      {hiddenCount > 0 && (
        <Link
          href="#"
          style={{ color: "var(--global-color-accent)" }}
          onClick={(event) => {
            event.preventDefault();
            setExpanded(true);
          }}
        >
          {t("portfolio.attention.viewAll")}
        </Link>
      )}
      {expanded && actions.length > ATTENTION_INITIAL_COUNT && (
        <Link
          href="#"
          style={{ color: "var(--global-color-accent)" }}
          onClick={(event) => {
            event.preventDefault();
            setExpanded(false);
          }}
        >
          {t("portfolio.attention.viewFewer")}
        </Link>
      )}
    </Stack>
  );
}

function NeedsYourAttentionRow({
  action,
  openInvestmentCase,
  t,
}: {
  action: PortfolioAction;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const navigate = useNavigate();
  const { title, reason } = describePortfolioAction(action, t);

  if (!action.ticker) {
    return (
      <Surface tier="primary">
        <Text as="span" color="secondary">
          {SEVERITY_EMOJI[action.severity]} {title} — {reason}
        </Text>
      </Surface>
    );
  }

  const ticker = action.ticker;

  return (
    <Surface tier="primary" bordered style={{ cursor: "pointer" }}>
      <div
        role="button"
        tabIndex={0}
        aria-label={t("portfolio.attention.rowAriaLabel", { ticker, reason })}
        onClick={() => navigate(`/portfolio/holding/${encodeURIComponent(ticker)}`, { state: { action } })}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            navigate(`/portfolio/holding/${encodeURIComponent(ticker)}`, { state: { action } });
          }
        }}
      >
        <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
          <Stack gap="metadata">
            <Text as="span" style={{ fontWeight: 600 }}>
              {SEVERITY_EMOJI[action.severity]} {ticker}
            </Text>
            <Text as="span" color="secondary">
              {reason}
            </Text>
          </Stack>
          <Text as="span" color="tertiary">
            ›
          </Text>
        </Inline>
      </div>
    </Surface>
  );
}

/**
 * Concentration Summary + Atlas Coverage sidebar (Portfolio Workspace
 * v1). Top-N by weight is real and already fully computable from
 * `view.holdings`, already fetched -- no new endpoint. Sector
 * Allocation is deliberately not rendered (see `PortfolioPulse`'s own
 * docstring); a short, honest note explains why rather than silently
 * omitting the section, matching this page's established "explain the
 * gap" convention for every other missing value.
 */
const CONCENTRATION_TOP_N = 3;

function PortfolioSidebar({
  view,
  cockpit,
  t,
}: {
  view: PortfolioView;
  cockpit: PortfolioCockpitFetchStatus;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const topHoldings = [...view.holdings].sort((a, b) => b.weightPercent - a.weightPercent).slice(0, CONCENTRATION_TOP_N);
  const topWeightSum = Math.round(topHoldings.reduce((sum, h) => sum + h.weightPercent, 0) * 10) / 10;
  const coveredCount =
    cockpit.kind === "loaded"
      ? cockpit.report.holdings.filter((h) => h.analysisCoverage.level !== "no_coverage").length
      : null;

  return (
    <Stack gap="inter-section">
      <Surface tier="primary">
        <Stack gap="metadata">
          <Label>{t("portfolio.concentrationSummary.heading")}</Label>
          <Text color="secondary" as="p">
            {t("portfolio.concentrationSummary.subheading", { count: topHoldings.length, percent: topWeightSum })}
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
function HoldingsTable({
  view,
  cockpit,
  unallocatedPercent,
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
  unallocatedPercent: number | null;
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
  const visibleHoldings = showAllHoldings ? view.holdings : view.holdings.slice(0, HOLDINGS_PAGE_SIZE);

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

      <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.tickerHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.valueHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.shareHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.coverageHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.reviewStatusHeader")}</th>
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
          {cockpitHolding ? (
            <StatusText
              label={t(reviewStatusKeyFor(cockpitHolding.attention.priority))}
              tone={reviewStatusToneFor(cockpitHolding.attention.priority)}
            />
          ) : (
            <StatusText label={t("portfolio.holdingsTable.reviewStatus.new")} />
          )}
        </td>
      </tr>
      {isReconcileExpanded && (
        <tr>
          <td colSpan={5} style={cellStyle}>
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
 * Figma-fidelity rebuild -- the honest substitute for the approved
 * screen's "Structural Profile" / "Risk & Execution Guide" two-column
 * block. That block's free-prose buckets (Strengths/Weaknesses/Key
 * Drivers, Diversification/Biggest Risks/Recommended Change) imply a
 * portfolio-level narrative-synthesis capability that does not exist --
 * no module in this codebase generates prose judgments like "Strong
 * tech allocation with high-conviction MSFT and AMZN positions." Per
 * the corrected migration principle's priority order (truthful
 * presentation first, minimal-neutral second, omission last), this
 * renders the same two-column position and the same real underlying
 * data (`KeyFindingView[]`/`RiskSignalView[]`/missing-evidence count,
 * all already fetched from `/alpha-portfolio/intelligence`) as two
 * structured, honestly-labeled lists instead -- never the fabricated
 * prose Figma shows.
 */
function PortfolioIntelligencePanels({
  statusReport,
  intelligenceReport,
  t,
}: {
  statusReport: PortfolioStatusView | null;
  intelligenceReport: PortfolioIntelligenceView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const keyFindings = intelligenceReport?.keyFindings ?? [];
  // `missing_evidence` signals are one-per-holding and would flood this
  // panel with a redundant "X has missing evidence" line per ticker --
  // the aggregate `missingEvidenceCount` line below already states that
  // fact once, honestly and completely. Only the other four kinds (each
  // genuinely rare, never one-per-holding) render individually.
  const riskSignals = (intelligenceReport?.riskSignals ?? []).filter((signal) => signal.kind !== "missing_evidence");
  const missingEvidenceCount = intelligenceReport?.missingEvidence.length ?? 0;

  if (!statusReport && !intelligenceReport) return null;

  return (
    <Inline gap="inter-section" wrap>
      <div style={{ flex: "1 1 320px", minWidth: 0 }}>
        <Stack gap="metadata">
          <Label>{t("portfolio.keyFindingsPanel.heading")}</Label>
          {keyFindings.length === 0 && <Text color="tertiary">{t("portfolio.keyFindingsPanel.empty")}</Text>}
          {keyFindings.map((finding, index) => (
            <Text as="p" color="secondary" key={index}>
              {t(KEY_FINDING_KEY[finding.kind], { count: finding.count, tickers: finding.tickers.join(", ") })}
            </Text>
          ))}
        </Stack>
      </div>
      <div style={{ flex: "1 1 320px", minWidth: 0 }}>
        <Stack gap="metadata">
          <Label>{t("portfolio.riskSignalsPanel.heading")}</Label>
          {riskSignals.length === 0 && missingEvidenceCount === 0 && (
            <Text color="tertiary">{t("portfolio.riskSignalsPanel.empty")}</Text>
          )}
          {riskSignals.map((signal, index) => (
            <Text as="p" color="secondary" key={index}>
              {t(RISK_SIGNAL_KEY[signal.kind], { ticker: signal.ticker })}
            </Text>
          ))}
          {missingEvidenceCount > 0 && (
            <Text as="p" color="secondary">
              {t("portfolio.riskSignalsPanel.missingEvidenceCount", { count: missingEvidenceCount })}
            </Text>
          )}
        </Stack>
      </div>
    </Inline>
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
