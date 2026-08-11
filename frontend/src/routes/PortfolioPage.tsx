import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  derivePortfolioActions,
  type ActionSeverity,
  type PortfolioAction,
} from "../portfolio/derivePortfolioActions";
import {
  ANALYSIS_COVERAGE_LEVEL_KEY,
  ANALYSIS_COVERAGE_TONE,
  CONFIDENCE_KEY,
  CONFIDENCE_TONE,
  CONVICTION_LEVEL_KEY,
  CONVICTION_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  REVIEW_PRIORITY_KEY,
  REVIEW_PRIORITY_TONE,
  RISK_STATUS_TONE,
  type AnalysisCoverageLevel,
  type ConvictionLevel,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type ReviewPriority,
} from "../status/statusTone";
import { RISK_STATUS_KEY, type AnalysisRiskStatus } from "../changeIntelligence/describeChange";
import { describePortfolioAction, SEVERITY_EMOJI, SEVERITY_LABEL_KEY } from "../portfolio/describePortfolioAction";

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

/**
 * Holdings Table (Portfolio Workspace v3) -- the same 🔴/🟠/🟡 vocabulary
 * Today's Priorities already established, reused for row Status rather
 * than inventing a second color language. `standard_review` and `none`
 * both read as "nothing urgent" at a glance -- Atlas draws attention
 * only to what actually needs it, never grades a holding as
 * additionally "good."
 */
const REVIEW_PRIORITY_EMOJI: Record<CockpitReviewPriority, string> = {
  priority_review: "🔴",
  evidence_review: "🟠",
  standard_review: "🟡",
  none: "",
};

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

const UNALLOCATED_TOLERANCE = 0.01;

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

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("portfolio.title")}</Heading>

        <div>
          <RouterLink to="/portfolio/import">{t("portfolioImport.title")}</RouterLink>
        </div>

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
              <RouterLink to="/welcome">{t("portfolio.setupLink")}</RouterLink>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length === 0 && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>{t("portfolio.empty.title")}</Text>
              {status.view.objective && (
                <Text color="secondary">
                  {t("portfolio.empty.objective", { value: status.view.objective })}
                </Text>
              )}
              {status.view.horizon && (
                <Text color="secondary">
                  {t("portfolio.empty.horizon", { value: status.view.horizon })}
                </Text>
              )}
              <Text color="secondary">{t("portfolio.empty.explanation")}</Text>
              <div>
                <Button variant="tertiary" onClick={() => openInvestmentCase("__new__", null)}>
                  {t("portfolio.openNewCase")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0 && (
          <Stack gap="inter-section">
            <PortfolioSummaryBar
              view={status.view}
              statusReport={
                portfolioStatus.kind === "loaded" && portfolioStatus.report.exists ? portfolioStatus.report : null
              }
              t={t}
            />

            <ActionCenterCard
              statusReport={
                portfolioStatus.kind === "loaded" && portfolioStatus.report.exists ? portfolioStatus.report : null
              }
              intelligenceReport={
                portfolioIntelligence.kind === "loaded" && portfolioIntelligence.report.exists
                  ? portfolioIntelligence.report
                  : null
              }
              openInvestmentCase={openInvestmentCase}
              t={t}
            />

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
          </Stack>
        )}
      </Stack>
    </Container>
  );
}

/**
 * Portfolio Summary (Portfolio Workspace v3) -- compact by design, per
 * this sprint's explicit "very compact... no large cards" instruction:
 * exactly the four figures the sprint's own example names (Holdings,
 * Cash, Holdings requiring attention, Overall portfolio health), each
 * read verbatim from data this page already fetches. "Holdings
 * requiring attention" reuses `reviewQueue.length` -- the same already-
 * deduplicated-per-ticker count Today's Priorities is built from, never
 * a second count computed a different way. "Overall portfolio health"
 * reuses the existing `PortfolioHealthMetrics.holdings_with_case_count`
 * coverage figure rather than synthesizing a new Good/Bad score Atlas
 * doesn't compute anywhere -- a literal, already-real fact standing in
 * for the sprint's more general phrase. Unallocated%/Concentration (on
 * the previous, larger summary card) move to the Holdings table below,
 * where they sit next to the holdings they describe; Investment
 * Cases/Open Decisions/Pending Outcomes/Pending Executions are no
 * longer repeated here since Today's Priorities and the Holdings table
 * now surface that same information as concrete, actionable rows
 * instead of an abstract count.
 *
 * One additional, conditional line: `health.unknownInstrumentTickers`
 * (a real, already-fetched data-quality signal -- tickers whose format
 * looked structurally wrong at import) is not folded into any of the
 * four figures above, since it isn't a count of holdings *needing
 * review* so much as a warning that Atlas may have misread an
 * instrument entirely. It renders only when that array is non-empty --
 * compact, low-noise, no separate card -- and stays silent otherwise.
 */
function PortfolioSummaryBar({
  view,
  statusReport,
  t,
}: {
  view: PortfolioView;
  statusReport: PortfolioStatusView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const needsAttention = statusReport?.reviewQueue.length ?? null;
  const health = statusReport?.health ?? null;

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.summary.heading")}</Heading>
        <Inline gap="row" wrap>
          <Text color="secondary" as="p">
            {t("portfolio.summary.holdings")}: {view.numberOfHoldings}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.cash")}:{" "}
            {view.cashWeightPercent !== null ? `${view.cashWeightPercent}%` : t("portfolio.summary.noLargestPosition")}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.needsAttention")}:{" "}
            {needsAttention !== null ? needsAttention : t("portfolio.summary.noLargestPosition")}
          </Text>
          {health && (
            <Text color="secondary" as="p">
              {t("portfolio.summary.health")}:{" "}
              {t("portfolio.health.coverage", { withCase: health.holdingsWithCaseCount, total: health.holdingsCount })}
            </Text>
          )}
        </Inline>
        {health && health.unknownInstrumentTickers.length > 0 && (
          <Text color="tertiary" as="p">
            {t("portfolio.summary.unknownInstrumentsWarning", { count: health.unknownInstrumentTickers.length })}
          </Text>
        )}
      </Stack>
    </Surface>
  );
}

/**
 * Action Center -- the page's own answer to "what should I work on
 * first?", replacing the four previously-separate, overlapping lists
 * (Needs Attention, Consider, Risk Signals, Missing Evidence) that
 * could each name the same holding independently. Groups already-
 * fetched `reviewQueue`/`missingEvidence`/`keyFindings` via
 * `derivePortfolioActions` into a deduplicated, three-tier, capped list
 * -- "surface only the highest-value actions," per the sprint's own
 * rule, not everything Atlas knows.
 */
function ActionCenterCard({
  statusReport,
  intelligenceReport,
  openInvestmentCase,
  t,
}: {
  statusReport: PortfolioStatusView | null;
  intelligenceReport: PortfolioIntelligenceView | null;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const allActions = derivePortfolioActions(
    statusReport?.reviewQueue ?? [],
    intelligenceReport?.missingEvidence.map((item) => ({ ticker: item.ticker, caseId: item.caseId })) ?? [],
    intelligenceReport?.keyFindings ?? [],
    statusReport?.summary?.unallocatedPercent ?? null,
    statusReport?.attentionItems.map((item) => ({
      ticker: item.ticker,
      category: item.category,
      ageDays: item.ageDays,
    })) ?? [],
  );

  // Capped *per severity tier*, not with one flat cap across all of
  // them -- a portfolio with two dozen High-priority evidence gaps
  // would otherwise crowd out every Medium-priority (e.g. portfolio
  // allocation) action entirely, even though both tiers are real and
  // both are meant to stay visible per the sprint's own three-tier
  // example.
  const grouped: Record<ActionSeverity, PortfolioAction[]> = { highest: [], high: [], medium: [] };
  for (const action of allActions) {
    if (grouped[action.severity].length < MAX_ACTIONS_PER_SEVERITY) {
      grouped[action.severity].push(action);
    }
  }
  const actions = [...grouped.highest, ...grouped.high, ...grouped.medium];

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.actionCenter.heading")}</Heading>
        {actions.length === 0 && <Text color="secondary">{t("portfolio.actionCenter.empty")}</Text>}
        {(["highest", "high", "medium"] as const).map(
          (severity) =>
            grouped[severity].length > 0 && (
              <Stack key={severity} gap="intra-section">
                <Heading level={3}>
                  {SEVERITY_EMOJI[severity]} {t(SEVERITY_LABEL_KEY[severity])}
                </Heading>
                {grouped[severity].map((action) => (
                  <ActionCenterRow
                    key={action.id}
                    action={action}
                    openInvestmentCase={openInvestmentCase}
                    t={t}
                  />
                ))}
              </Stack>
            ),
        )}
      </Stack>
    </Surface>
  );
}

function ActionCenterRow({
  action,
  openInvestmentCase,
  t,
}: {
  action: PortfolioAction;
  openInvestmentCase: (ticker: string, existingCaseId: string | null) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const { title, reason } = describePortfolioAction(action, t);

  return (
    <Stack gap="metadata">
      <Text as="p">{title}</Text>
      <Text color="secondary" as="p">
        {reason}
      </Text>
      {action.itemCount > 0 && (
        <Text color="tertiary" as="p">
          {t("portfolio.actionCenter.itemCount", { count: action.itemCount })}
        </Text>
      )}
      {action.ticker && (
        <div>
          <Button variant="primary" onClick={() => openInvestmentCase(action.ticker!, action.caseId)}>
            {action.caseId ? t("portfolio.actionCenter.reviewButton") : t("portfolio.actionCenter.openCaseButton")}
          </Button>
        </div>
      )}
      <Divider tone="hairline" />
    </Stack>
  );
}

/**
 * Holdings Table (Portfolio Workspace v3) -- the dominant, primary
 * workspace of the page, immediately following Today's Priorities per
 * this sprint's explicit new hierarchy. Columns follow the sprint's own
 * suggested list (Status, Ticker, Weight, Conviction, Evidence,
 * [Priority], [Thesis]) with two deliberate, explicitly-justified
 * substitutions for the last two:
 *
 * - **"Priority" stays "Priority," and a new "Action" column was added
 *   alongside it (Workspace Migration Phase 1, Migration Review §11.1),
 *   not a replacement.** The two answer different questions: Priority
 *   (`HoldingAttention.priority`, none/standard/evidence/priority
 *   review) is "how urgently should I look at this," Action
 *   (`atlas.alpha.decision_support`'s evidence-support badge, backed by
 *   the real `ComputedDirectionalRecommendation`/`RecommendationWithheld`
 *   union) is "what does current evidence say about this position."
 *   Never an imperative Buy/Add/Trim command (Decision Log #1) -- the
 *   badge is always one of the seven `DecisionSupportLevel` states.
 * - **"Thesis" instead of "Last updated."** No per-holding timestamp is
 *   exposed by any endpoint this page fetches (`generatedAt` on the
 *   Cockpit report is portfolio-wide, not per row) -- fabricating one
 *   would violate this sprint's own "reuse existing data" constraint.
 *   `isThesisStale` is the real, already-computed per-holding freshness
 *   signal this data actually has, so that's what's shown.
 *
 * Valuation/Risk/Growth/Capital Allocation (shown on the pre-v3 page)
 * are dropped from the row, not lost: they already render in full on
 * the Investment Case page (`investmentCase.analysis.*`), one click
 * away -- the "Portfolio is overview, Investment Case is depth"
 * principle this codebase has followed since ATLAS-028, and this
 * sprint's own "Details on Demand" principle names directly.
 *
 * **Row click is plain route navigation, not a true overlay.** Clicking
 * a row (or pressing Enter/Space on it) calls the same
 * `openInvestmentCase` this page has always used -- a `navigate()` to
 * `/investment-case/:id` with `state: { origin: "portfolio" }`, giving a
 * "← Back to Portfolio" link on the Case page. That is real continuity
 * (the investor can always get back), but it is NOT the same thing as
 * Portfolio → Investment Case being a contextual overlay/workspace: a
 * full route change unmounts this page, so scroll position, any
 * expanded reconciliation row, and the Today's Discussions ask-input
 * state are all lost on return. Making Investment Case open as a true
 * overlay so that closing it restores this exact Portfolio state is
 * explicit, planned follow-up work for a future "Investment Case
 * Workspace" sprint -- out of scope here; routing is deliberately
 * unchanged in this sprint.
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
    padding: "var(--space-row) var(--space-metadata)",
    textAlign: "left",
    borderBottom: `var(--width-border-hairline) solid var(--color-border-hairline)`,
    fontFamily: "var(--type-family-prose)",
    fontSize: "var(--type-body-min-size)",
  };
  const headerCellStyle: CSSProperties = {
    ...cellStyle,
    color: "var(--color-text-tertiary)",
    fontFamily: "var(--type-family-metadata)",
    fontWeight: 500,
    borderBottom: `var(--width-border-standard) solid var(--color-border-standard)`,
  };

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.holdings.heading")}</Heading>
        {!view.hasAbsoluteValues && <Text color="secondary">{t("portfolio.holdings.percentOnly")}</Text>}
        {view.hasAbsoluteValues && view.totalValue !== null && (
          <Text color="secondary">{t("portfolio.holdings.totalValue", { value: view.totalValue })}</Text>
        )}

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.statusHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.tickerHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.weightHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.analysisCoverageHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.convictionHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.evidenceHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.riskHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.priorityHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.thesisHeader")}</th>
                <th style={headerCellStyle}>{t("portfolio.holdingsTable.actionHeader")}</th>
              </tr>
            </thead>
            <tbody>
              {view.holdings.map((holding) => {
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

        {unallocatedPercent !== null && unallocatedPercent > UNALLOCATED_TOLERANCE && (
          <Text color="secondary">
            {t("portfolio.unallocated", { percent: Math.round(unallocatedPercent * 100) / 100 })}
          </Text>
        )}
        {view.concentrationLevel && (
          <Text color="secondary">
            {t("portfolio.concentration", {
              value: CONCENTRATION_LEVEL_KEY[view.concentrationLevel]
                ? t(CONCENTRATION_LEVEL_KEY[view.concentrationLevel]!)
                : view.concentrationLevel,
            })}
          </Text>
        )}

        <div>
          <Button variant="tertiary" onClick={() => openInvestmentCase("__new__", null)}>
            {t("portfolio.openNewCase")}
          </Button>
        </div>
      </Stack>
    </Surface>
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

  function handleRowActivate() {
    if (isCreating) return;
    openInvestmentCase(holding.ticker, holding.caseId);
  }

  return (
    <>
      <tr
        role="button"
        tabIndex={0}
        aria-label={
          holding.caseId ? t("portfolio.cockpit.viewCaseButton") : t("portfolio.holdings.openCaseButton")
        }
        onClick={handleRowActivate}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            handleRowActivate();
          }
        }}
        style={{ cursor: isCreating ? "default" : "pointer" }}
      >
        <td style={cellStyle}>
          {cockpitHolding ? (
            <Text as="span">{REVIEW_PRIORITY_EMOJI[cockpitHolding.attention.priority]}</Text>
          ) : (
            <Text as="span" color="tertiary">
              —
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          <Stack gap="metadata">
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
              <div>
                <Button
                  variant="tertiary"
                  onClick={(event) => {
                    event.stopPropagation();
                    onToggleReconcile();
                  }}
                >
                  {isReconcileExpanded ? t("common.cancel") : t("portfolio.holdingsTable.reconcileToggle")}
                </Button>
              </div>
            )}
          </Stack>
        </td>
        <td style={cellStyle}>
          <Text as="span">
            {holding.weightPercent}%{holding.valueAbsolute !== null ? ` — ${holding.valueAbsolute}` : ""}
          </Text>
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(ANALYSIS_COVERAGE_LEVEL_KEY[cockpitHolding.analysisCoverage.level])}
              tone={ANALYSIS_COVERAGE_TONE[cockpitHolding.analysisCoverage.level]}
            />
          ) : (
            <Text as="span" color="tertiary">
              —
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(CONVICTION_LEVEL_KEY[cockpitHolding.conviction.level])}
              tone={CONVICTION_TONE[cockpitHolding.conviction.level]}
            />
          ) : (
            <Text as="span" color="tertiary">
              —
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(CONFIDENCE_KEY[cockpitHolding.confidence])}
              tone={CONFIDENCE_TONE[cockpitHolding.confidence]}
            />
          ) : (
            <Text as="span" color="tertiary">
              —
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(RISK_STATUS_KEY[cockpitHolding.riskProjection.status])}
              tone={RISK_STATUS_TONE[cockpitHolding.riskProjection.status]}
            />
          ) : (
            <Text as="span" color="tertiary">
              —
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(REVIEW_PRIORITY_KEY[cockpitHolding.attention.priority])}
              tone={REVIEW_PRIORITY_TONE[cockpitHolding.attention.priority]}
            />
          ) : (
            <Text as="span" color="tertiary">
              —
            </Text>
          )}
        </td>
        <td style={cellStyle}>
          <Text as="span" color={cockpitHolding?.isThesisStale ? "tertiary" : "primary"}>
            {cockpitHolding
              ? cockpitHolding.isThesisStale
                ? t("portfolio.holdingsTable.thesisStale")
                : t("portfolio.holdingsTable.thesisFresh")
              : "—"}
          </Text>
        </td>
        <td style={cellStyle}>
          {cockpitHolding ? (
            <StatusBadge
              label={t(DECISION_SUPPORT_BADGE_KEY[cockpitHolding.decisionSupport.level])}
              tone={DECISION_SUPPORT_TONE[cockpitHolding.decisionSupport.level]}
            />
          ) : (
            <Text as="span" color="tertiary">
              —
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
