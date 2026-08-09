import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  derivePortfolioActions,
  type ActionSeverity,
  type PortfolioAction,
} from "../portfolio/derivePortfolioActions";

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

type EvidenceCoverageLevel = "not_applicable" | "none" | "partial" | "full";

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

const CONFIDENCE_KEY: Record<EvidenceCoverageLevel, TranslationKey> = {
  not_applicable: "portfolio.intelligence.confidence.not_applicable",
  none: "portfolio.intelligence.confidence.none",
  partial: "portfolio.intelligence.confidence.partial",
  full: "portfolio.intelligence.confidence.full",
};

const KEY_FINDING_KEY: Record<KeyFindingKind, TranslationKey> = {
  high_concentration: "portfolio.intelligence.keyFindings.high_concentration",
  elevated_concentration: "portfolio.intelligence.keyFindings.elevated_concentration",
  large_unallocated: "portfolio.intelligence.keyFindings.large_unallocated",
  multiple_missing_cases: "portfolio.intelligence.keyFindings.multiple_missing_cases",
  multiple_stale_cases: "portfolio.intelligence.keyFindings.multiple_stale_cases",
  multiple_evidence_gaps: "portfolio.intelligence.keyFindings.multiple_evidence_gaps",
};

/**
 * Action Center (ATLAS UI Sprint) — ticker-free reason phrasings for
 * `AttentionCategory` (the same backend enum `ReviewQueueItem
 * .topCategory` already carries): Action Center's own title line
 * already names the ticker ("Review {ticker}"), so this surface needs
 * the reason on its own, without repeating it a second time in the
 * same sentence.
 */
const ACTION_CENTER_REASON_KEY: Record<AttentionCategory, TranslationKey> = {
  MISSING_CASE: "portfolio.actionCenter.reason.missingCase",
  DECISION_WITHOUT_OUTCOME: "portfolio.actionCenter.reason.decisionWithoutOutcome",
  OUTCOME_WITHOUT_EXECUTION: "portfolio.actionCenter.reason.outcomeWithoutExecution",
  AWAITING_RECONCILIATION: "portfolio.actionCenter.reason.awaitingReconciliation",
  VERY_OLD_CASE: "portfolio.actionCenter.reason.veryOldCase",
  OBSERVATION_WITHOUT_DECISION: "portfolio.actionCenter.reason.observationWithoutDecision",
};

const SEVERITY_EMOJI: Record<ActionSeverity, string> = { highest: "🔴", high: "🟠", medium: "🟡" };
const SEVERITY_LABEL_KEY: Record<ActionSeverity, TranslationKey> = {
  highest: "portfolio.actionCenter.severity.highest",
  high: "portfolio.actionCenter.severity.high",
  medium: "portfolio.actionCenter.severity.medium",
};

const MAX_ACTIONS_PER_SEVERITY = 3;
const MAX_KEY_FINDING_TICKERS_SHOWN = 5;

/**
 * ATLAS-028 Portfolio Cockpit -- one canonical, portfolio-scoped per-
 * holding analysis, projected from `CanonicalAnalysis`
 * (`atlas/alpha/portfolio_cockpit/`). Every value below comes straight
 * from `GET /alpha-portfolio/cockpit`; this page computes nothing of
 * its own beyond translating enum values -- the same "no domain logic
 * in the UI" discipline `PortfolioOverview` above already follows.
 * Portfolio Cockpit is the overview; a holding's own
 * Investment Case (one click away via `caseId`) is the depth.
 */
type CockpitConvictionLevel = "very_high" | "high" | "moderate" | "low" | "insufficient_evidence";
type CockpitValuationStatus = "not_evaluated" | "insufficient_input" | "undervalued" | "fairly_valued" | "expensive";
type CockpitRiskCategory = "business_risk" | "financial_risk" | "valuation_risk" | "thesis_risk";
type CockpitRiskStatus = "not_evaluated" | "insufficient_input" | "low" | "moderate" | "high";
type CockpitBusinessStatus = "not_evaluated" | "insufficient_input" | "weak" | "moderate" | "strong";
type CockpitReviewPriority = "none" | "standard_review" | "evidence_review" | "priority_review";
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

interface PortfolioCockpitHoldingView {
  ticker: string;
  caseId: string;
  weightPercent: number;
  valueAbsolute: number | null;
  reconciliationStatus: "NONE" | "UPDATED" | "AWAITING_RECONCILIATION";
  conviction: CockpitConvictionView;
  valuation: CockpitValuationView;
  business: CockpitBusinessSummaryView;
  riskProjection: CockpitRiskProjectionView;
  confidence: EvidenceCoverageLevel;
  isThesisStale: boolean;
  attention: CockpitAttentionView;
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

const CONVICTION_LEVEL_KEY: Record<CockpitConvictionLevel, TranslationKey> = {
  very_high: "portfolio.cockpit.conviction.very_high",
  high: "portfolio.cockpit.conviction.high",
  moderate: "portfolio.cockpit.conviction.moderate",
  low: "portfolio.cockpit.conviction.low",
  insufficient_evidence: "portfolio.cockpit.conviction.insufficient_evidence",
};

const VALUATION_STATUS_KEY: Record<CockpitValuationStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.valuation.not_evaluated",
  insufficient_input: "portfolio.cockpit.valuation.insufficient_input",
  undervalued: "portfolio.cockpit.valuation.undervalued",
  fairly_valued: "portfolio.cockpit.valuation.fairly_valued",
  expensive: "portfolio.cockpit.valuation.expensive",
};

const RISK_STATUS_KEY: Record<CockpitRiskStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.risk.status.not_evaluated",
  insufficient_input: "portfolio.cockpit.risk.status.insufficient_input",
  low: "portfolio.cockpit.risk.status.low",
  moderate: "portfolio.cockpit.risk.status.moderate",
  high: "portfolio.cockpit.risk.status.high",
};

const RISK_CATEGORY_KEY: Record<CockpitRiskCategory, TranslationKey> = {
  business_risk: "portfolio.cockpit.risk.category.business_risk",
  financial_risk: "portfolio.cockpit.risk.category.financial_risk",
  valuation_risk: "portfolio.cockpit.risk.category.valuation_risk",
  thesis_risk: "portfolio.cockpit.risk.category.thesis_risk",
};

const BUSINESS_STATUS_KEY: Record<CockpitBusinessStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.business.not_evaluated",
  insufficient_input: "portfolio.cockpit.business.insufficient_input",
  weak: "portfolio.cockpit.business.weak",
  moderate: "portfolio.cockpit.business.moderate",
  strong: "portfolio.cockpit.business.strong",
};

const REVIEW_PRIORITY_KEY: Record<CockpitReviewPriority, TranslationKey> = {
  none: "portfolio.cockpit.review.none",
  standard_review: "portfolio.cockpit.review.standard_review",
  evidence_review: "portfolio.cockpit.review.evidence_review",
  priority_review: "portfolio.cockpit.review.priority_review",
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
            <PortfolioOverview
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

            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>{t("portfolio.holdings.heading")}</Heading>
                {!status.view.hasAbsoluteValues && (
                  <Text color="secondary">{t("portfolio.holdings.percentOnly")}</Text>
                )}
                {status.view.hasAbsoluteValues && status.view.totalValue !== null && (
                  <Text color="secondary">
                    {t("portfolio.holdings.totalValue", { value: status.view.totalValue })}
                  </Text>
                )}

                {status.view.holdings.map((holding) => {
                  const thisCaseCreateStatus: CaseCreateStatus =
                    caseCreateStatus[holding.ticker] ?? { kind: "idle" };
                  const thisReconcileStatus: ReconcileStatus =
                    reconcileStatus[holding.ticker] ?? { kind: "idle" };
                  const cockpitHolding =
                    cockpit.kind === "loaded"
                      ? cockpit.report.holdings.find((h) => h.ticker === holding.ticker)
                      : undefined;
                  const isUnresolvedInCockpit =
                    cockpit.kind === "loaded" &&
                    cockpit.report.unresolvedHoldings.some((h) => h.ticker === holding.ticker);

                  return (
                    <div key={holding.ticker}>
                      <Text>{holding.ticker}</Text>
                      <Text color="secondary" as="p">
                        {holding.weightPercent}%
                        {holding.valueAbsolute !== null ? ` — ${holding.valueAbsolute}` : ""}
                      </Text>
                      {cockpitHolding && <PortfolioCockpitHoldingBadges holding={cockpitHolding} t={t} />}
                      {isUnresolvedInCockpit && (
                        <Text color="tertiary" as="p">
                          {t("portfolio.cockpit.unresolved")}
                        </Text>
                      )}
                      {holding.reconciliationStatus === "UPDATED" && (
                        <Text color="secondary" as="p">
                          {t("portfolio.holdings.updatedAutomatically")}
                        </Text>
                      )}
                      {holding.reconciliationStatus === "AWAITING_RECONCILIATION" && (
                        <Stack gap="inter-section">
                          <Text color="tertiary" as="p">
                            {t("portfolio.holdings.awaitingReconciliation")}
                          </Text>
                          <Text as="label">
                            {t("portfolio.holdings.newWeightLabel")}
                            <br />
                            <input
                              value={reconcileWeightInputs[holding.ticker] ?? ""}
                              onChange={(event) =>
                                setReconcileWeightInputs((current) => ({
                                  ...current,
                                  [holding.ticker]: event.target.value,
                                }))
                              }
                            />
                          </Text>
                          <Button
                            variant="tertiary"
                            onClick={() => submitUpdateHoldingWeight(holding.ticker)}
                            disabled={thisReconcileStatus.kind === "submitting"}
                          >
                            {thisReconcileStatus.kind === "submitting"
                              ? t("portfolio.holdings.updating")
                              : t("portfolio.holdings.updateButton")}
                          </Button>
                          {thisReconcileStatus.kind === "error" && (
                            <Text color="tertiary" role="alert">
                              {thisReconcileStatus.message}
                            </Text>
                          )}
                        </Stack>
                      )}
                      <Button
                        variant="tertiary"
                        onClick={() => openInvestmentCase(holding.ticker, holding.caseId)}
                        disabled={thisCaseCreateStatus.kind === "creating"}
                      >
                        {thisCaseCreateStatus.kind === "creating"
                          ? t("portfolio.holdings.opening")
                          : holding.caseId
                            ? t("portfolio.cockpit.viewCaseButton")
                            : t("portfolio.holdings.openCaseButton")}
                      </Button>
                      {thisCaseCreateStatus.kind === "error" && (
                        <Text color="tertiary" role="alert">
                          {t("portfolio.holdings.openCaseError")}
                        </Text>
                      )}
                      <Divider tone="hairline" />
                    </div>
                  );
                })}

                {status.view.cashWeightPercent !== null && (
                  <Text color="secondary">
                    {t("portfolio.cashLabel", { percent: status.view.cashWeightPercent })}
                    {status.view.cashValueAbsolute !== null
                      ? ` — ${status.view.cashValueAbsolute}`
                      : ""}
                  </Text>
                )}
                {unallocatedPercent !== null && unallocatedPercent > UNALLOCATED_TOLERANCE && (
                  <Text color="secondary">
                    {t("portfolio.unallocated", {
                      percent: Math.round(unallocatedPercent * 100) / 100,
                    })}
                  </Text>
                )}
                {status.view.concentrationLevel && (
                  <Text color="secondary">
                    {t("portfolio.concentration", {
                      value: CONCENTRATION_LEVEL_KEY[status.view.concentrationLevel]
                        ? t(CONCENTRATION_LEVEL_KEY[status.view.concentrationLevel]!)
                        : status.view.concentrationLevel,
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
          </Stack>
        )}
      </Stack>
    </Container>
  );
}

/**
 * ATLAS-028 Portfolio Cockpit -- one compact, scan-friendly analytical
 * row per holding: Conviction, Valuation, Risk (highest-severity
 * projection), Business (Growth/Capital Allocation), Evidence
 * confidence, and Review priority. A dedicated Portfolio-page-local
 * treatment, not a new Foundation-wide primitive (per this sprint's
 * confirmed scope) -- built from the same "Field: value" `Inline` style
 * `PortfolioSummaryCard` already uses just below.
 * Review priority uses `color="tertiary"` (this codebase's existing
 * attention/alert color) whenever a holding needs more than a standard
 * review, so it reads at a glance without a new color token.
 */
function PortfolioCockpitHoldingBadges({
  holding,
  t,
}: {
  holding: PortfolioCockpitHoldingView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const needsElevatedReview =
    holding.attention.priority === "evidence_review" || holding.attention.priority === "priority_review";

  const analysisLine = [
    `${t("portfolio.cockpit.conviction.label")}: ${t(CONVICTION_LEVEL_KEY[holding.conviction.level])}`,
    `${t("portfolio.cockpit.valuation.label")}: ${t(VALUATION_STATUS_KEY[holding.valuation.status])}`,
    `${t("portfolio.cockpit.risk.label")}: ${t(RISK_CATEGORY_KEY[holding.riskProjection.category])} — ${t(
      RISK_STATUS_KEY[holding.riskProjection.status],
    )}`,
  ].join("   ·   ");

  const businessLine = [
    `${t("portfolio.cockpit.business.growthLabel")}: ${t(BUSINESS_STATUS_KEY[holding.business.growth])}`,
    `${t("portfolio.cockpit.business.capitalAllocationLabel")}: ${t(
      BUSINESS_STATUS_KEY[holding.business.capitalAllocation],
    )}`,
    `${t("portfolio.cockpit.evidenceLabel")}: ${t(CONFIDENCE_KEY[holding.confidence])}`,
  ].join("   ·   ");

  return (
    <Stack gap="metadata">
      <Text color="secondary" as="p">
        {analysisLine}
      </Text>
      <Text color="secondary" as="p">
        {businessLine}
      </Text>
      <Text color={needsElevatedReview ? "tertiary" : "secondary"} as="p">
        {t("portfolio.cockpit.review.label")}: {t(REVIEW_PRIORITY_KEY[holding.attention.priority])}
        {holding.isThesisStale ? `   ·   ${t("portfolio.cockpit.thesisStale")}` : ""}
      </Text>
    </Stack>
  );
}

/**
 * ATLAS UI Sprint (Portfolio Action Center) -- replaces the previous
 * `PortfolioIntelligenceCards`/`PortfolioIntelligenceSections` pair
 * (ATLAS-015/016) with a hierarchy led by "what should I work on
 * first?" rather than a flat sequence of independent status cards.
 * Every value still comes straight from the existing
 * `PortfolioStatusView` (`GET /alpha-portfolio/status`) and
 * `PortfolioIntelligenceView` (`GET /alpha-portfolio/intelligence`) --
 * nothing here computes a new fact; `derivePortfolioActions`
 * (`frontend/src/portfolio`) only groups and ranks facts that already
 * exist, the same "no domain logic in the UI" discipline this page has
 * followed since ATLAS-015. `statusReport`/`intelligenceReport` are
 * each independently nullable (still loading, or that one fetch
 * failed) -- Action Center renders whatever subset of its three real
 * sources is actually available rather than an all-or-nothing gate,
 * matching every other section's existing graceful-degradation
 * behavior on this page.
 *
 * Order: Portfolio Summary (statistics, compact) -> Action Center
 * (action) -> Portfolio Health (health) -> Key Findings (decision
 * support, condensed) -> Review Queue (secondary browsing list) ->
 * Portfolio Fit (statistics, not yet available). This is the
 * "Action -> Decision support -> Health -> Statistics" order the
 * sprint asked for, with Portfolio Summary kept first only because it
 * is the one card every other section's own numbers refer back to.
 */
function PortfolioOverview({
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
  const summary = statusReport?.summary ?? null;
  const health = statusReport?.health ?? null;

  return (
    <Stack gap="inter-section">
      {summary && <PortfolioSummaryCard summary={summary} t={t} />}

      <ActionCenterCard
        statusReport={statusReport}
        intelligenceReport={intelligenceReport}
        openInvestmentCase={openInvestmentCase}
        t={t}
      />

      {health && <PortfolioHealthCard health={health} t={t} />}

      {intelligenceReport && <KeyFindingsCard findings={intelligenceReport.keyFindings} t={t} />}

      {statusReport && <ReviewQueueCard reviewQueue={statusReport.reviewQueue} t={t} />}

      {intelligenceReport && !intelligenceReport.portfolioFit.available && (
        <Text color="tertiary" as="p">
          {t("portfolio.intelligence.portfolioFit.heading")}:{" "}
          {t("portfolio.intelligence.portfolioFit.notYetAvailable")}
        </Text>
      )}
    </Stack>
  );
}

/** Portfolio Summary -- unchanged content, kept as the one compact
 * statistics card at the very top (per the sprint's own "keep this
 * compact, one card" instruction). */
function PortfolioSummaryCard({
  summary,
  t,
}: {
  summary: PortfolioSummaryMetrics;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.summary.heading")}</Heading>
        <Inline gap="row" wrap>
          <Text color="secondary" as="p">
            {t("portfolio.summary.holdings")}: {summary.holdingsCount}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.largestPosition")}:{" "}
            {summary.largestPositionTicker
              ? `${summary.largestPositionTicker} (${summary.largestPositionWeightPercent}%)`
              : t("portfolio.summary.noLargestPosition")}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.investmentCases")}: {summary.numberOfInvestmentCases}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.openDecisions")}: {summary.openDecisions}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.pendingOutcomes")}: {summary.pendingOutcomes}
          </Text>
          <Text color="secondary" as="p">
            {t("portfolio.summary.pendingExecutions")}: {summary.pendingExecutions}
          </Text>
          {summary.concentrationLevel && (
            <Text color="secondary" as="p">
              {t("portfolio.summary.concentration")}:{" "}
              {CONCENTRATION_LEVEL_KEY[summary.concentrationLevel]
                ? t(CONCENTRATION_LEVEL_KEY[summary.concentrationLevel]!)
                : summary.concentrationLevel}
            </Text>
          )}
          {summary.unallocatedPercent !== null && (
            <Text color="secondary" as="p">
              {t("portfolio.summary.unallocated")}: {summary.unallocatedPercent}%
            </Text>
          )}
        </Inline>
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
  let title: string;
  let reason: string;
  switch (action.kind) {
    case "workflow":
      title = t("portfolio.actionCenter.reviewTitle", { ticker: action.ticker ?? "" });
      reason = t(ACTION_CENTER_REASON_KEY[action.reasonCategory!], { days: action.ageDays ?? 0 });
      break;
    case "evidence":
      title = t("portfolio.actionCenter.completeEvidenceTitle", { ticker: action.ticker ?? "" });
      reason = t("portfolio.actionCenter.evidenceReason");
      break;
    case "concentration":
      title = t("portfolio.actionCenter.concentrationTitle", { ticker: action.ticker ?? "" });
      reason = t(KEY_FINDING_KEY[action.concentrationFindingKind!], { tickers: action.ticker ?? "" });
      break;
    case "allocation":
      title = t("portfolio.actionCenter.allocationTitle");
      reason = t("portfolio.actionCenter.allocationReason", { percent: action.unallocatedPercent ?? 0 });
      break;
  }

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

/** Portfolio Health -- unchanged content, unchanged position relative
 * to Action Center (immediately below it, per the sprint's own
 * hierarchy). */
function PortfolioHealthCard({
  health,
  t,
}: {
  health: PortfolioHealthView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.health.heading")}</Heading>
        <Text color="secondary" as="p">
          {t("portfolio.health.coverage", {
            withCase: health.holdingsWithCaseCount,
            total: health.holdingsCount,
          })}
        </Text>
        <Text color="secondary" as="p">
          {health.mostRecentDecisionAt
            ? t("portfolio.health.freshness", { date: health.mostRecentDecisionAt })
            : t("portfolio.health.noDecisions")}
        </Text>
        <Text color="secondary" as="p">
          {t("portfolio.health.outstandingItems")}: {health.outstandingWorkflowItems}
        </Text>
        {health.allocatedPercent !== null && (
          <Text color="secondary" as="p">
            {t("portfolio.health.completeness")}: {health.allocatedPercent}%
          </Text>
        )}
        <Text color="secondary" as="p">
          {t("portfolio.health.unknownInstruments")}:{" "}
          {health.unknownInstrumentTickers.length > 0
            ? health.unknownInstrumentTickers.join(", ")
            : t("portfolio.health.noUnknownInstruments")}
        </Text>
      </Stack>
    </Surface>
  );
}

/**
 * Key Findings, condensed -- only the three aggregate/statistical
 * findings (`multiple_missing_cases`/`multiple_stale_cases`
 * /`multiple_evidence_gaps`) render here; `large_unallocated` and the
 * two concentration findings are already surfaced as real actions in
 * Action Center above when present, so repeating them here again would
 * be exactly the duplication the sprint asked to remove. Each finding
 * is one headline (a count, no ticker list inline) plus a capped,
 * expandable ticker list -- "Show 'View all' rather than printing
 * every ticker inline," per the sprint's own instruction.
 */
function KeyFindingsCard({
  findings,
  t,
}: {
  findings: KeyFindingView[];
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const relevant = findings.filter(
    (finding) =>
      finding.kind === "multiple_missing_cases" ||
      finding.kind === "multiple_stale_cases" ||
      finding.kind === "multiple_evidence_gaps",
  );

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.intelligence.keyFindings.heading")}</Heading>
        {relevant.length === 0 && <Text color="secondary">{t("portfolio.intelligence.keyFindings.empty")}</Text>}
        {relevant.map((finding, index) => (
          <KeyFindingRow key={index} finding={finding} t={t} />
        ))}
      </Stack>
    </Surface>
  );
}

const KEY_FINDING_HEADLINE_KEY: Record<
  "multiple_missing_cases" | "multiple_stale_cases" | "multiple_evidence_gaps",
  TranslationKey
> = {
  multiple_missing_cases: "portfolio.intelligence.keyFindings.headline.multiple_missing_cases",
  multiple_stale_cases: "portfolio.intelligence.keyFindings.headline.multiple_stale_cases",
  multiple_evidence_gaps: "portfolio.intelligence.keyFindings.headline.multiple_evidence_gaps",
};

function KeyFindingRow({
  finding,
  t,
}: {
  finding: KeyFindingView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const [expanded, setExpanded] = useState(false);
  const headlineKey = KEY_FINDING_HEADLINE_KEY[finding.kind as keyof typeof KEY_FINDING_HEADLINE_KEY];
  const visibleTickers = expanded ? finding.tickers : finding.tickers.slice(0, MAX_KEY_FINDING_TICKERS_SHOWN);
  const hasMore = finding.tickers.length > MAX_KEY_FINDING_TICKERS_SHOWN;

  return (
    <Stack gap="metadata">
      <Text as="p">{t(headlineKey, { count: finding.count })}</Text>
      {finding.tickers.length > 0 && (
        <Text color="secondary" as="p">
          {t("portfolio.intelligence.keyFindings.affectedHoldingsLabel")}: {visibleTickers.join(", ")}
          {!expanded && hasMore ? "…" : ""}
        </Text>
      )}
      {hasMore && (
        <div>
          <Button variant="tertiary" onClick={() => setExpanded((current) => !current)}>
            {expanded
              ? t("portfolio.intelligence.keyFindings.showLess")
              : t("portfolio.intelligence.keyFindings.viewAll")}
          </Button>
        </div>
      )}
    </Stack>
  );
}

/** Review Queue -- unchanged content and behavior, kept as a secondary,
 * browsable section beneath Key Findings (per the sprint's own "keep
 * as a secondary section" instruction). Already deduplicated per
 * ticker by the backend (`ReviewQueueItem`, one row per holding with a
 * combined reason count) -- nothing to further condense here. */
function ReviewQueueCard({
  reviewQueue,
  t,
}: {
  reviewQueue: ReviewQueueItemView[];
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("portfolio.reviewQueue.heading")}</Heading>
        {reviewQueue.length === 0 && <Text color="secondary">{t("portfolio.reviewQueue.empty")}</Text>}
        {reviewQueue.map((item) => (
          <Inline key={item.ticker} gap="row" align="center">
            {item.caseId ? (
              <RouterLink to={`/investment-case/${item.caseId}`}>
                {t("portfolio.reviewQueue.item", { ticker: item.ticker })}
              </RouterLink>
            ) : (
              <Text>{t("portfolio.reviewQueue.item", { ticker: item.ticker })}</Text>
            )}
            <Text color="tertiary">{t("portfolio.reviewQueue.reasonCount", { count: item.reasonCount })}</Text>
          </Inline>
        ))}
      </Stack>
    </Surface>
  );
}
