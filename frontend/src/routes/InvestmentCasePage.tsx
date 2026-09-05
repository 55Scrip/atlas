import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link as RouterLink, useLocation, useParams } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, StatusBadge, StatusText, Surface, Text, VisuallyHidden } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  deriveActivity,
  deriveOutstandingWork,
  formatRelativeTime,
  sortActivity,
  type HoldingLite,
  type TradeLogEntry,
} from "../activity/deriveActivity";
import {
  BUSINESS_STATUS_TONE,
  CONFIDENCE_KEY,
  CONVICTION_LEVEL_KEY,
  CONVICTION_REASON_KEY,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_STATEMENT_KEY,
  DECISION_SUPPORT_TONE,
  DATA_FRESHNESS_STATUS_KEY,
  DATA_FRESHNESS_STATUS_TONE,
  FIT_RATING_KEY,
  MONITORING_STATUS_KEY,
  MONITORING_STATUS_TONE,
  RISK_STATUS_TONE,
  VALUATION_STATUS_TONE,
  type ChangeTriggerKind,
  type ConvictionLevel,
  type ConvictionReasonCode,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type MissingEvaluationCategory,
  type OutlookRecommendationRelationship,
  type ValuationSupportGapKind,
  type ValuationSupportStatus,
} from "../status/statusTone";
import { PortfolioFitSection } from "../portfolioFit/PortfolioFitSection";
import { EvidenceGraphSection } from "../evidenceGraph/EvidenceGraphSection";
import { fetchEvidenceGraph, type EvidenceGraphView } from "../evidenceGraph/evidenceGraphApi";
import { DecisionReadinessSection } from "../decisionReadiness/DecisionReadinessSection";
import {
  fetchDecisionReadiness,
  fetchDecisionReadinessChange,
  type DecisionReadinessChangeView,
  type DecisionReadinessView,
} from "../decisionReadiness/decisionReadinessApi";
import { fetchPortfolioFitForCase, type PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { InvestmentDecisionSection } from "../investmentDecision/InvestmentDecisionSection";
import {
  fetchInvestmentDecision,
  fetchInvestmentDecisionChange,
  type DecisionChangeView,
  type InvestmentDecisionView,
} from "../investmentDecision/investmentDecisionApi";
import { RecommendationConvictionSection } from "../recommendationConviction/RecommendationConvictionSection";
import {
  fetchRecommendationConviction,
  fetchRecommendationConvictionChange,
  type ConvictionChangeView,
  type RecommendationConvictionView,
} from "../recommendationConviction/recommendationConvictionApi";
import { DecisionPathSection } from "../decisionPath/DecisionPathSection";
import {
  fetchDecisionPath,
  fetchDecisionPathChange,
  type DecisionPathChangeView,
  type DecisionPathView,
} from "../decisionPath/decisionPathApi";
import { OpportunityCostSection } from "../opportunityCost/OpportunityCostSection";
import { type OpportunityCostChangeView, type OpportunityCostView } from "../opportunityCost/opportunityCostApi";
import { DecisionMemorySection } from "../decisionMemory/DecisionMemorySection";
import { type DecisionMemoryView } from "../decisionMemory/decisionMemoryApi";
import { DecisionExplanationSection } from "../decisionExplanation/DecisionExplanationSection";
import { type DecisionExplanationView } from "../decisionExplanation/decisionExplanationApi";
import { DecisionReliabilitySection } from "../decisionReliability/DecisionReliabilitySection";
import { fetchDecisionReliability, type DecisionReliabilityView } from "../decisionReliability/decisionReliabilityApi";
import { PortfolioDecisionSection } from "../portfolioDecision/PortfolioDecisionSection";
import { type PortfolioDecisionView } from "../portfolioDecision/portfolioDecisionApi";
import { fetchInvestmentCaseDecisionLayerBundle } from "../investmentCase/decisionLayerBundleApi";
import { addTickerToWatchlist, useAlphaWatchlist, type WatchlistEntryView } from "../discovery/watchlistActions";
import { invalidateAlphaPortfolio, useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { ALPHA_PLACEHOLDER_USER_ID } from "../decisionWorkspace/alphaUser";
import { fetchDailyBriefChangeLog, markDailyBriefChangesSeen } from "../dailyBriefAgenda/dailyBriefChangeLogApi";
import { StartDecisionSection } from "../decisionWorkspace/StartDecisionSection";
import {
  BUSINESS_CATEGORY_KEY,
  BUSINESS_DATA_GAP_KEY,
  BUSINESS_STATUS_KEY,
  CHANGE_DIRECTION_SYMBOL,
  describeChange,
  dimensionLabel,
  HIGHLIGHT_KIND_KEY,
  humanize,
  OPEN_QUESTION_ORIGIN_KEY,
  RISK_CATEGORY_KEY,
  RISK_DATA_GAP_KEY,
  RISK_STATUS_KEY,
  THESIS_IMPACT_KEY,
  VALUATION_DATA_GAP_KEY,
  VALUATION_STATUS_KEY,
  type AnalysisBusinessCategory,
  type AnalysisBusinessStatus,
  type AnalysisChangeCategory,
  type AnalysisChangeDirection,
  type AnalysisHighlightKind,
  type AnalysisOpenQuestionOrigin,
  type AnalysisRiskCategory,
  type AnalysisRiskStatus,
  type AnalysisThesisImpact,
  type AnalysisValuationStatus,
  type BusinessDataGapKind,
  type ChangeFindingView,
  type RiskDataGapKind,
  type Translate,
  type ValuationDataGapKind,
} from "../changeIntelligence/describeChange";
import {
  deriveLimitingFactors,
  deriveOutstandingIssues,
  type LimitingFactor,
  type OutstandingIssueKind,
  type OutstandingWorkKind,
  type RecommendationDriverKind,
} from "../investmentCase/deriveExecutiveSummary";
import { LimitingFactorsCard } from "../investmentCase/LimitingFactorsCard";
import { ValuationSupportCard } from "../investmentCase/ValuationSupportCard";
import {
  FinancialsTable,
  formatFinancialValue,
  formatShareCount,
  type FinancialPeriodView,
} from "../investmentCase/FinancialsTable";
import { HeroCard, HERO_WHY_KEY, type HeroAnalysisInput } from "../investmentCase/HeroCard";
import { deriveHeroTension } from "../investmentCase/deriveHeroNarrative";
import {
  deriveCompanyRating,
  deriveEvidenceRating,
  deriveHorizon,
  deriveInvestmentRating,
  derivePortfolioRating,
  deriveRisk,
  deriveUpside,
} from "../investmentCase/atlasRatingModel";
import { SevenCategoriesSection, CaseDnaLine, type SevenCategoriesInput } from "../investmentCase/SevenCategoriesSection";
import { AtlasDecisionSummary } from "../investmentCase/AtlasDecisionSummary";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { AtlasOutlookSection, type OutlookView } from "../investmentCase/AtlasOutlookSection";
import { InvestmentArgumentSection } from "../investmentCase/InvestmentArgumentSection";
import {
  AtlasReasoningSection,
  capFacts,
  isReadableFact,
  type AtlasReasoningInput,
  type ReasoningFacts,
} from "../investmentCase/AtlasReasoningSection";
import { CompanyHealthAssessmentSection, type CompanyHealthCardInput } from "../investmentCase/CompanyHealthAssessmentSection";
import { InterpretedFinancialEvidenceSection } from "../investmentCase/InterpretedFinancialEvidenceSection";
import { WhatChangedSection } from "../investmentCase/WhatChangedSection";
import { CoveragePanel } from "../coverage/CoveragePanel";
import type { CoverageAssessmentView } from "../coverage/coverageApi";
import { KnowledgeCoveragePanel } from "../knowledgeCoverage/KnowledgeCoveragePanel";
import type { InvestmentCaseKnowledgeCoverageView } from "../knowledgeCoverage/knowledgeCoverageApi";
import type { StanceView } from "../stance/stanceApi";
import { ExplanationPanel } from "../explainability/ExplanationPanel";
import type { ExplanationView } from "../explainability/explainabilityApi";
import { EvidenceQualityPanel } from "../evidenceQuality/EvidenceQualityPanel";
import type { EvidenceQualityReportView } from "../evidenceQuality/evidenceQualityApi";
import { EvidenceTimelinePanel } from "../evidenceTimeline/EvidenceTimelinePanel";
import type { EvidenceHistoryView } from "../evidenceTimeline/evidenceTimelineApi";
import { MaterialityPanel } from "../materiality/MaterialityPanel";
import type { MaterialityAssessmentView } from "../materiality/materialityApi";
import { ManagementIntelligencePanel } from "../investmentCase/ManagementIntelligencePanel";
import type {
  ExecutiveChangeIntelligenceView,
  ExecutiveCompensationIntelligenceView,
  ExecutiveTrackRecordIntelligenceView,
  GovernanceIntelligenceView,
  InsiderAlignmentIntelligenceView,
  OwnershipIntelligenceView,
  RegulatoryFilingView,
} from "../investmentCase/managementIntelligenceApi";
import { RegulatoryIntelligencePanel } from "../investmentCase/RegulatoryIntelligencePanel";
import type { LegalProceedingsIntelligenceView, RiskFactorIntelligenceView } from "../investmentCase/regulatoryIntelligenceApi";

/** Renders a bounded enum value's real copy; falls back to `humanize()`
 * only for a value the map doesn't (yet) cover, mirroring the
 * `OPEN_QUESTION_ORIGIN_KEY` fallback pattern already used above. */
function describeGapKind<K extends string>(value: string, map: Record<K, TranslationKey>, t: Translate): string {
  return value in map ? t(map[value as K]) : humanize(value);
}

interface CaseSummary {
  caseId: string;
  recordedAt: string;
}

type CaseStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; case: CaseSummary };

/**
 * The same shape `PortfolioPage.tsx` already fetches from
 * `GET /api/alpha-portfolio` — a second, independent fetch of the one
 * existing Alpha portfolio endpoint, not a new backend capability. This
 * page reuses it to find which holding (if any) links to this Case
 * (`holding.caseId`), which is the only source of company identity —
 * `Case` itself carries none (`atlas/core/domain/case/entity.py`: "no
 * further lifecycle, status, title, description, or content is
 * canonically forced").
 */
interface AlphaHoldingView extends HoldingLite {
  weightPercent: number;
  valueAbsolute: number | null;
}

interface AlphaPortfolioView {
  exists: boolean;
  hasAbsoluteValues: boolean;
  holdings: AlphaHoldingView[];
  cashWeightPercent: number | null;
  cashValueAbsolute: number | null;
  concentrationLevel: string | null;
}

type AlphaPortfolioStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: AlphaPortfolioView };

type TradeLogFetchStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; trades: TradeLogEntry[] };

/** Product Sprint 10 (Navigation & Workflow Excellence, Deliverable 4/5):
 * this page previously had no way to tell whether the ticker it's
 * showing is already on the Watchlist, so a case for a ticker that is
 * neither held nor watched had no "Add to Watchlist" affordance at all
 * -- an isolated island reachable only by leaving and using Discovery's
 * own Search flow. Reuses the exact same `/api/alpha-watchlist` wrapper
 * Discovery/Watchlist already use (`watchlistActions.ts`). */
type WatchlistFetchStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; entries: WatchlistEntryView[] };

/**
 * Shared shape for every "fetch the full list, scoped to this Case"
 * status (Observation, Evidence, Knowledge Reference, Reasoning Trace,
 * Judgment, Decision, Outcome all used seven byte-identical copies of
 * this same three-variant union before Integration Sprint 1 — collapsed
 * into one type here; no behavior changes, since all seven copies were
 * already structurally identical).
 */
type ListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

/**
 * Fetches the full, case-scoped list for one domain object type and
 * mirrors it into local state — the one fetch shape every section on
 * this page shares (Observation, Evidence, Knowledge Reference,
 * Reasoning Trace, Judgment, Decision, Outcome). Before Integration
 * Sprint 1, each section repeated this same effect body inline; this
 * hook replaces all seven copies with one, with no change in behavior:
 * same AbortController-per-effect cleanup, same loading/ready/error
 * transitions, same "ignore AbortError" catch.
 */
function useApiList<T>(
  url: string,
  caseId: string | undefined,
  setRecords: (records: T[]) => void,
  setStatus: (status: ListStatus) => void,
  unknownErrorMessage: string,
) {
  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setStatus({ kind: "loading" });

    fetch(url, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<T[]>;
      })
      .then((records) => {
        setRecords(records);
        setStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : unknownErrorMessage,
        });
      });

    return () => controller.abort();
  }, [url, caseId, setRecords, setStatus, unknownErrorMessage]);
}

/**
 * Deletes one record by id and mirrors the removal into local state —
 * the one delete shape every deletable section on this page shares
 * (Evidence, Knowledge Reference, Reasoning Trace, Judgment; Decision
 * and Outcome have no delete capability at all, per their own governing
 * design, so neither calls this). Before Integration Sprint 1, each
 * section repeated this same function body inline; this helper replaces
 * all four copies with one, with no change in behavior: same
 * deleting/idle/error transitions, same "404 counts as already gone"
 * tolerance.
 */
function deleteRecord<T>(
  url: string,
  id: string,
  matchesId: (record: T) => boolean,
  setRecords: (updater: (current: T[]) => T[]) => void,
  setDeleteStatus: (
    updater: (
      current: Record<string, "idle" | "deleting" | "error">,
    ) => Record<string, "idle" | "deleting" | "error">,
  ) => void,
  onSuccess?: () => void,
) {
  setDeleteStatus((current) => ({ ...current, [id]: "deleting" }));

  fetch(url, { method: "DELETE" })
    .then((response) => {
      if (!response.ok && response.status !== 404) {
        throw new Error(`Backend responded with ${response.status}`);
      }
      setRecords((current) => current.filter((record) => !matchesId(record)));
      setDeleteStatus((current) => ({ ...current, [id]: "idle" }));
      onSuccess?.();
    })
    .catch(() => {
      setDeleteStatus((current) => ({ ...current, [id]: "error" }));
    });
}

/** The most recent of a set of ISO timestamps, or `null` if there are none. */
function latestTimestamp(timestamps: string[]): string | null {
  if (timestamps.length === 0) return null;
  return timestamps.reduce((latest, current) =>
    new Date(current).getTime() > new Date(latest).getTime() ? current : latest,
  );
}

interface ObservationRecord {
  observationId: string;
  caseId: string;
  subject: string;
  statement: string;
  observedAt: string;
}

type ObservationCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; observation: ObservationRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface EvidenceRecord {
  evidenceId: string;
  observationId: string;
  statement: string;
  direction: string;
  source: string | null;
  observedAt: string;
}

type EvidenceCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; evidence: EvidenceRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface EvidenceFormInput {
  summary: string;
  source: string;
  direction: "SUPPORTS" | "CHALLENGES";
}

/** Visual Fidelity Pass -- the approved screen's bottom tab bar is
 * plain text (active = primary color + a hairline underline, inactive
 * = tertiary color), not a row of bordered/filled buttons. A bare
 * `<button>` reset to look like text, not a new interaction pattern --
 * still a real, keyboard-operable button underneath. */
function TabLabel({
  active,
  onClick,
  id,
  controls,
  children,
}: {
  active: boolean;
  onClick: () => void;
  id: string;
  controls: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      id={id}
      aria-selected={active}
      aria-controls={controls}
      onClick={onClick}
      style={{
        background: "none",
        border: "none",
        borderBottom: active ? "2px solid var(--global-color-accent)" : "2px solid transparent",
        padding: "0 0 var(--space-metadata) 0",
        margin: 0,
        cursor: "pointer",
        fontFamily: "var(--type-family-prose)",
        fontSize: "var(--type-body-min-size)",
        color: active ? "var(--color-text-primary)" : "var(--color-text-tertiary)",
      }}
    >
      {children}
    </button>
  );
}

const EMPTY_EVIDENCE_FORM: EvidenceFormInput = { summary: "", source: "", direction: "SUPPORTS" };

interface KnowledgeReferenceTarget {
  targetType: string;
  targetId: string;
}

interface KnowledgeReferenceRecord {
  knowledgeReferenceId: string;
  caseId: string;
  target: KnowledgeReferenceTarget;
  recordedAt: string;
}

type KnowledgeReferenceCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; knowledgeReference: KnowledgeReferenceRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface ReasoningTraceSupport {
  targetType: string;
  targetId: string;
}

interface ReasoningTraceRecord {
  reasoningTraceId: string;
  caseId: string;
  supports: ReasoningTraceSupport[];
  recordedAt: string;
}

type ReasoningTraceCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; reasoningTrace: ReasoningTraceRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface JudgmentSubject {
  targetType: string;
  targetId: string;
}

interface JudgmentRecord {
  judgmentId: string;
  caseId: string;
  characterization: string;
  subject: JudgmentSubject | null;
  recordedAt: string;
}

type JudgmentCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; judgment: JudgmentRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface DecisionRecord {
  id: string;
  caseId: string;
  userId: string;
  decisionType: string;
  subject: string;
  reason: string;
  confidence: number;
  decidedAt: string;
  recordedAt: string;
  source: string;
  observationId: string | null;
}

type DecisionCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; decision: DecisionRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface DecisionFormInput {
  decisionType: "BUY" | "SELL" | "HOLD" | "WATCH" | "PASS";
  subject: string;
  reason: string;
  confidence: string;
}

const EMPTY_DECISION_FORM: DecisionFormInput = {
  decisionType: "BUY",
  subject: "",
  reason: "",
  confidence: "50",
};

/**
 * `decisionType` / `transactionType` are internal enum values, read and
 * sent verbatim to preserve the English-only domain vocabulary (per the
 * localization architecture) — this maps them to translated words only
 * where they're displayed or chosen, never in the request/response body.
 */
const DECISION_TYPE_KEY: Record<string, TranslationKey> = {
  BUY: "investmentCase.decision.typeBuy",
  SELL: "investmentCase.decision.typeSell",
  HOLD: "investmentCase.decision.typeHold",
  WATCH: "investmentCase.decision.typeWatch",
  PASS: "investmentCase.decision.typePass",
};

/**
 * The four decision actions this sprint's spec requires (Add / Trim /
 * Remove / Leave as is) all resolve to one of the five existing
 * `DecisionType` values — no new enum member, no partial/full
 * distinction at the Decision layer. "Trim" and "Remove" both record a
 * SELL: the difference between reducing and exiting a position is
 * captured later, honestly, in the Outcome's own recorded quantity —
 * not invented here as a Decision-level concept that doesn't exist.
 */
type PositionAction = "ADD" | "TRIM" | "REMOVE" | "LEAVE_AS_IS";

const ACTION_DECISION_TYPE: Record<PositionAction, DecisionFormInput["decisionType"]> = {
  ADD: "BUY",
  TRIM: "SELL",
  REMOVE: "SELL",
  LEAVE_AS_IS: "HOLD",
};

const ACTION_LABEL_KEY: Record<PositionAction, TranslationKey> = {
  ADD: "investmentCase.actions.addToPosition",
  TRIM: "investmentCase.actions.trimPosition",
  REMOVE: "investmentCase.actions.removePosition",
  LEAVE_AS_IS: "investmentCase.actions.leaveAsIs",
};

/**
 * Fixed key into `decisionForm`/`decisionCreateStatus` for the new,
 * top-level decision-action entry point — distinct from any real
 * Observation id (always a UUID), so the two entry points' form state
 * can never collide.
 */
const CASE_LEVEL_DECISION_KEY = "__case_level_decision__";

// `ALPHA_PLACEHOLDER_USER_ID` moved to `../decisionWorkspace/alphaUser`
// (Product Sprint 12) so `StartDecisionSection.tsx` can reuse the exact
// same constant without a circular import between the two modules.

interface OutcomeRecord {
  id: string;
  caseId: string;
  decisionId: string;
  statement: string;
  note: string | null;
  occurredAt: string;
  recordedAt: string;
}

type OutcomeCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; outcome: OutcomeRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface OutcomeFormInput {
  decisionId: string;
  statement: string;
  note: string;
  isExternalTrade: boolean;
  security: string;
  // ADD behaves like BUY; EXIT removes the holding outright rather
  // than reducing it (ATLAS-014) -- see `atlas/alpha/portfolio
  // /service.py::TransactionType`.
  transactionType: "BUY" | "SELL" | "ADD" | "EXIT";
  quantity: string;
  executionPrice: string;
  fees: string;
  executedAt: string;
}

const EMPTY_OUTCOME_FORM: OutcomeFormInput = {
  decisionId: "",
  statement: "",
  note: "",
  isExternalTrade: false,
  security: "",
  transactionType: "BUY",
  quantity: "",
  executionPrice: "",
  fees: "",
  executedAt: "",
};

/**
 * Pre-selects the transaction-type dropdown when the execution-report
 * form first opens — the dropdown remains fully editable, this only
 * changes the initial value. `TRIM` and `REMOVE` both record a SELL
 * Decision (`ACTION_DECISION_TYPE`), but the execution they're actually
 * reporting differs — TRIM reduces the holding, REMOVE closes it — so
 * this maps from the position action itself, not from the resulting
 * Decision type.
 */
const POSITION_ACTION_TRANSACTION_TYPE: Record<PositionAction, OutcomeFormInput["transactionType"]> = {
  ADD: "ADD",
  TRIM: "SELL",
  REMOVE: "EXIT",
  LEAVE_AS_IS: "BUY",
};

/** Same pre-selection for the per-Observation report form, which has no
 *  position-action context -- only the Decision's own BUY/SELL type. */
function defaultTransactionTypeForDecisionType(
  decisionType: string | undefined,
): OutcomeFormInput["transactionType"] {
  return decisionType === "SELL" ? "SELL" : "BUY";
}

/**
 * Alpha Sprint 1B: after Outcome is recorded exactly as today (unchanged
 * request/response shape -- Outcome itself is never modified), an
 * "external trade" toggle on the same form additionally calls
 * `POST /alpha-portfolio/apply-trade` with the newly-created Outcome's
 * own id, entirely as a follow-on step. Keyed by observationId, the
 * same pattern every other section on this page already uses.
 */
type TradeApplyStatus =
  | { kind: "idle" }
  | { kind: "applying" }
  | { kind: "updated" }
  | { kind: "awaiting-reconciliation" }
  | { kind: "error"; message: string };

/**
 * ATLAS-029 Canonical Investment Case -- a renderer of `CanonicalAnalysis`
 * (via `InvestmentCaseCompositionService.build`), never a second
 * reasoning engine. Every field here comes straight from
 * `GET /api/cases/{caseId}/analysis` (`atlas/alpha/investment_case/`);
 * this page computes nothing analytical of its own beyond translating
 * enum values and formatting dates -- the same discipline
 * `PortfolioCockpitHoldingBadges` (`PortfolioPage.tsx`) already follows.
 * Every `kind`/`status`/`coverage`/`reason` value is raw English on the
 * wire, translated only at display time. Business/Valuation/Risk/
 * Conviction status vocabularies are shared verbatim with Portfolio
 * Cockpit's own types (ATLAS-028) -- both surfaces read the same
 * `CanonicalAnalysis`, so they must agree (Phase 47).
 */
type OpenQuestionKind =
  | "no_evidence_recorded_for_case"
  | "observation_without_evidence"
  | "decision_without_linked_observation"
  | "business_durability_not_assessable"
  | "valuation_thesis_not_documented"
  | "portfolio_factor_not_assessable";

interface OpenQuestionView {
  kind: OpenQuestionKind;
  reference: string | null;
}

/** Now lives in `../status/statusTone` as `ConvictionLevel`
 * (Workspace Migration, Foundation extraction); this local alias keeps
 * every existing `AnalysisConvictionLevel` usage site unchanged. */
type AnalysisConvictionLevel = ConvictionLevel;
// AnalysisValuationStatus/AnalysisRiskCategory/AnalysisRiskStatus/
// AnalysisBusinessCategory/AnalysisBusinessStatus/AnalysisHighlightKind/
// AnalysisOpenQuestionOrigin now live in
// "../changeIntelligence/describeChange" (imported above) -- shared
// with History v1 rather than duplicated here.
type AnalysisMetricTrend = "strong_metric" | "weak_metric" | "mixed_metric";

// AnalysisChangeCategory/AnalysisChangeDirection/AnalysisThesisImpact
// now live in "../changeIntelligence/describeChange" (imported above).

interface HoldingContextView {
  held: boolean;
  ticker: string | null;
  weightPercent: number | null;
  valueAbsolute: number | null;
  reconciliationStatus: string | null;
}

interface CurrentThesisView {
  latestDecisionReason: string | null;
  latestDecisionType: string | null;
  latestObservationStatement: string | null;
}

interface BusinessFindingView {
  kind: AnalysisBusinessCategory;
  status: AnalysisBusinessStatus;
  severity: string;
  supportingEvidence: string[];
  contradictingEvidence: string[];
  missingEvidence: string[];
  confidence: EvidenceCoverageLevel;
  updatedAt: string;
}

interface ValuationFindingView {
  kind: string;
  status: AnalysisValuationStatus;
  severity: string;
  supportingFacts: string[];
  contradictingFacts: string[];
  assumptions: string[];
  missingEvidence: string[];
  confidence: EvidenceCoverageLevel;
  currentYield: number | null;
}

interface RiskFindingView {
  category: AnalysisRiskCategory;
  status: AnalysisRiskStatus;
  severity: string;
  supportingFacts: string[];
  contradictingFacts: string[];
  missingEvidence: string[];
  confidence: EvidenceCoverageLevel;
}

/** Figma-fidelity rebuild -- Atlas View's compact "Risk Level" dot
 * needs one representative category, not the full four-category vector
 * `risk.findings` already carries. The same real `risk_projection()`
 * Portfolio Cockpit's Holdings table Risk column already calls
 * (`atlas.analysis_engine.risk.projection`), reused verbatim, never a
 * second, divergent computation. */
interface RiskProjectionView {
  category: AnalysisRiskCategory;
  status: AnalysisRiskStatus;
}

interface ObservationClassificationView {
  observationId: string;
  status: string;
  supportingEvidenceCount: number;
  challengingEvidenceCount: number;
}

interface EvidenceQualityView {
  totalEvidenceCount: number;
  supportingEvidenceCount: number;
  challengingEvidenceCount: number;
  coverage: EvidenceCoverageLevel;
  observationClassifications: ObservationClassificationView[];
}

interface DecisionHistoryEntryView {
  decisionId: string;
  decisionType: string;
  reason: string;
  investorConfidence: number;
  decidedAt: string;
  observationId: string | null;
}

interface ObservationEntryView {
  observationId: string;
  subject: string;
  statement: string;
  observedAt: string;
}

interface OutcomeEntryView {
  outcomeId: string;
  decisionId: string;
  statement: string;
  occurredAt: string;
}

/** Migration Review §11.1/§13's header evidence-support sentence --
 * evidence-support language only, never a raw RecommendationDirection
 * member name (Decision Log #1). See `atlas.alpha.decision_support`'s
 * own module docstring (backend) for the full presentation-layer
 * rationale; this type is its wire shape. */
interface RecommendationOutlookAlignmentView {
  shortTerm: OutlookRecommendationRelationship;
  longTerm: OutlookRecommendationRelationship;
}

interface RecommendationStateView {
  level: DecisionSupportLevel;
  badgeLabel: string;
  statement: string;
  convictionGateMet: boolean;
  outlookAlignment: RecommendationOutlookAlignmentView;
  /** Beta Recommendation Experience implementation sprint (`UX-022` §4)
   * -- real, per-case `RecommendationWithheld.missing_evaluations`,
   * always `[]` when `level !== "insufficient_evidence"`. */
  missingEvaluations: MissingEvaluationCategory[];
  /** Calibration Phase 2 (Investment Case Coherence Implementation),
   * Phase 6 -- the real, populated `ChangeTriggerKind` values from
   * `ComputedDirectionalRecommendation.reasoning.what_would_change`.
   * Always `[]` when `level === "insufficient_evidence"` (no Direction
   * was ever selected, so there is no specific condition to name). */
  whatWouldChange: ChangeTriggerKind[];
}

// Investment Case Engine v1 slice (extended Company Data Foundation
// v1): descriptive company identity and raw financial data,
// automatically populated on Watchlist/Portfolio add -- see
// atlas/alpha/investment_case/company_profile.py and
// financial_history.py. Every field beyond ticker/asOf may be null: an
// honest absence when the provider did not report it, never a guess.
interface CompanyProfileView {
  ticker: string;
  name: string | null;
  exchange: string | null;
  sector: string | null;
  industry: string | null;
  country: string | null;
  description: string | null;
  asOf: string;
  currency: string | null;
  fiscalYearEnd: string | null;
}

/** Internal Alpha Stabilization 1 (MSFT price root cause fix) --
 * `"fresh" | "stale" | "refreshing" | "failed" | "unavailable"`, real,
 * server-computed against the actual trading day this price is from
 * -- never a client-side guess. */
export type PriceFreshnessStatus = "fresh" | "stale" | "refreshing" | "failed" | "unavailable";

interface MarketSnapshotView {
  asOf: string;
  sharePrice: number | null;
  sharesOutstanding: number | null;
  currency: string | null;
  marketCap: number | null;
  /** The real trading day this price is from (the source record's own
   * `period_end`) -- distinct from `asOf` (when Atlas fetched it). */
  tradingDay: string | null;
  priceFreshness: PriceFreshnessStatus;
}

// Investment Case Intelligence v1 slice: Strengths/Risks/Growth/
// Valuation Context/Atlas Thesis/Open Questions, synthesized from the
// same structured business/valuation/risk analysis the page already
// renders below (Business Analysis, Valuation, Risk sections) -- see
// atlas/analysis_engine/investment_case_synthesis.py. Every value here
// is a closed enum's raw string or a real evidence-reference id, never
// free-form AI text with no structured origin.
interface CaseHighlightView {
  kind: AnalysisHighlightKind;
  supportingFindingId: string;
  evidenceReferences: string[];
}

interface RecentRevenueTrendView {
  trend: AnalysisMetricTrend;
  periodsConsidered: string[];
  evidenceReferences: string[];
}

interface GrowthAnalysisView {
  status: AnalysisBusinessStatus;
  recentTrend: RecentRevenueTrendView | null;
  evidenceReferences: string[];
}

interface ValuationContextView {
  fcfYieldStatus: AnalysisValuationStatus;
  currentYield: number | null;
  scenarioAvailable: boolean;
  evidenceReferences: string[];
}

interface CaseOpenQuestionView {
  origin: AnalysisOpenQuestionOrigin;
  reference: string | null;
}

interface AtlasThesisView {
  posture: string;
  narrative: string;
  supportingHighlightIds: string[];
  keyUncertaintyOrigins: string[];
}

// ChangeFindingView now lives in "../changeIntelligence/describeChange"
// (imported above) -- shared with History v1. OutlookView (and its
// nested Horizon/ExpectedReturn/Scenario/Driver shapes) now lives in
// "../investmentCase/AtlasOutlookSection" (imported above), the same
// "component exports its own wire-shape Input type, page imports it"
// convention HeroAnalysisInput already established -- never redefined
// here.

interface InvestmentCaseAnalysisView {
  caseId: string;
  holdingContext: HoldingContextView;
  currentThesis: CurrentThesisView;
  isThesisStale: boolean;
  confidence: EvidenceCoverageLevel;
  conviction: { level: AnalysisConvictionLevel; reasons: string[] };
  coverage: CoverageAssessmentView;
  stance: StanceView | null;
  businessAnalysis: { state: string; findings: BusinessFindingView[] };
  valuation: { state: string; findings: ValuationFindingView[] };
  /** Alpha Freeze correction sprint (Principal Engineer Review 2.0,
   * finding M-2) -- `DE-015`'s `ValuationSupport`, additive, never
   * conflated with `valuation` above (see backend `ValuationSupportView`'s
   * own docstring). `status` is one of the real Core enum's three values
   * (`supported`/`not_supported`/`insufficient_input`); the frontend
   * renders it only through the safe presentation labels in
   * `status/statusTone.ts`, never verbatim. */
  valuationSupport: { status: string; gap: string | null };
  risk: { state: string; findings: RiskFindingView[] };
  riskProjection: RiskProjectionView;
  evidenceQuality: EvidenceQualityView | null;
  openQuestions: OpenQuestionView[];
  recommendation: RecommendationStateView;
  decisionHistory: DecisionHistoryEntryView[];
  observationHistory: ObservationEntryView[];
  outcomeHistory: OutcomeEntryView[];
  companyProfile: CompanyProfileView | null;
  financialHistory: FinancialPeriodView[];
  marketSnapshot: MarketSnapshotView | null;
  strengths: CaseHighlightView[];
  risks: CaseHighlightView[];
  growthAnalysis: GrowthAnalysisView;
  valuationContext: ValuationContextView;
  atlasThesis: AtlasThesisView;
  outlook: OutlookView;
  keyOpenQuestions: CaseOpenQuestionView[];
  changeIntelligenceAvailable: boolean;
  isBaselineCase: boolean;
  latestChanges: ChangeFindingView[];
  changeSummary: string;
  thesisChange: AnalysisThesisImpact;
  previousAnalysisAt: string | null;
  currentAnalysisAt: string;
  generatedAt: string;
  explanation: ExplanationView | null;
  evidenceQualityReport: EvidenceQualityReportView | null;
  evidenceTimeline: EvidenceHistoryView | null;
  materiality: MaterialityAssessmentView | null;
  monitoring: MonitoringStatusView | null;
  operationalFreshness: OperationalFreshnessView | null;
  knowledgeCoverage: InvestmentCaseKnowledgeCoverageView | null;
  /** Product Utilization Sprint 1 (Investment Case Experience
   * Activation). Every field below already existed on the backend
   * response (Capability Expansion Sprints 10/11/15/16/17/18/19/20/21)
   * -- this interface simply never grew to include them, so they were
   * unreachable from this page regardless of what Atlas actually knew.
   * See `ManagementIntelligencePanel`/`RegulatoryIntelligencePanel`'s
   * own module docstrings. */
  regulatoryFilings: RegulatoryFilingView[];
  executiveChangeIntelligence: ExecutiveChangeIntelligenceView;
  executiveTrackRecordIntelligence: ExecutiveTrackRecordIntelligenceView;
  governanceIntelligence: GovernanceIntelligenceView;
  riskFactorIntelligence: RiskFactorIntelligenceView;
  legalProceedingsIntelligence: LegalProceedingsIntelligenceView;
  ownershipIntelligence: OwnershipIntelligenceView;
  executiveCompensationIntelligence: ExecutiveCompensationIntelligenceView;
  insiderAlignmentIntelligence: InsiderAlignmentIntelligenceView;
  /** Import Robustness (Internal Alpha Stabilization 1) -- see the
   * backend `InvestmentCaseAnalysisView.no_provider_data_found`'s own
   * docstring for the exact, narrow honesty rule. Optional to default
   * safely to `false` ("nothing unusual to report") if ever absent. */
  noProviderDataFound?: boolean;
}

/** Atlas Intelligence Sprint 7 (Monitoring & Change Detection,
 * Deliverable 13). `null` only when Monitoring has never run for this
 * Case yet. */
interface MonitoringStatusView {
  status: "up_to_date" | "changed_review_suggested" | "changed_high_importance" | "waiting_for_better_evidence" | "unavailable";
  materialChangeCount: number;
  latestChangeReason: string | null;
  generatedAt: string | null;
}

/** Atlas Intelligence Sprint 8/9 (Automated Monitoring Operations /
 * Data Ingestion & Automatic Refresh, Deliverable 15/6/7) -- purely
 * operational, never investment status. */
interface OperationalFreshnessView {
  isPending: boolean;
  lastMonitoredAt: string | null;
  lastRunFailedForCase: boolean;
  dataFreshnessStatus: DataFreshnessStatus;
}

type DataFreshnessStatus = "waiting_for_new_data" | "waiting_for_analysis" | "monitoring_failed" | "no_data_source" | "unknown";

type InvestmentCaseAnalysisFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: InvestmentCaseAnalysisView };

/**
 * Investment Case (Alpha Sprint 1A) — merges the former Investment Case
 * shell (Sprint 1, Commit 8) and Decision Workspace (Sprint 1, Commits
 * 9-11+) into the one shared Investment Case implementation Alpha Sprint
 * 1 requires ("Use one shared Investment Case implementation. Do not
 * create a separate Decision Workspace."). The `/decision-workspace/*`
 * routes are removed; every real workflow that used to live there
 * (Observation, Evidence, Knowledge Reference, Reasoning Trace,
 * Judgment, Decision, Outcome) now lives here, unchanged in behavior.
 *
 * TERMINOLOGY, corrected: the former docstring here read "Investment
 * Case... not yet a settled Atlas concept," citing the pre-reconciliation
 * state of Architecture-Governance.md and Atlas-Alpha-Baseline-v1.0.md.
 * That is now stale. As of this session's own Product Architecture
 * Reconciliation (commit 963b008), `APP-001` v0.4 §3.13 settles
 * "Investment Case" as the confirmed, 1:1 product-facing name for
 * atlas/core's own `Case` (`OE-002` §3.1), distinct from, and enclosing,
 * Decision Context — see `Architecture-Governance.md` §8.7.4 and
 * `Atlas-Alpha-Baseline-v1.0.md` §4/§6. `UX-012`'s own text has not
 * itself been updated to cite this resolution (a separate, UX-track
 * document edit, outside this sprint's scope) — but the Product-layer
 * question this page previously deferred on is closed.
 *
 * This page still does not adopt UX-012 §15's separately-defined
 * "Investment Workspace" reasoning sequence (Current Conclusion,
 * Supporting Factors, Challenges, ...), and does not fabricate any
 * Investment Case content with no backend model yet (Atlas assessment,
 * thesis, risks, conviction, valuation context, monitoring conditions —
 * per Alpha Sprint 1 Phase 4, "do not fabricate the full designed
 * Investment Case content that has no backend model yet"). It renders
 * exactly the real backend concepts that exist: Case, and every Core
 * Loop object already implemented beneath it.
 *
 * Foundation Patch: reopening this page for the same Case (via
 * Portfolio's now-idempotent "Open Investment Case" link, or a direct
 * URL) fetches this Case's real Observations, Evidence, Knowledge
 * References, Reasoning Traces, Judgments, Decisions, and Outcomes from
 * the unmodified Core API exactly as before — nothing here changed to
 * make that true; it was already true, and now Portfolio reliably sends
 * the investor back to the same `caseId` instead of a fresh one.
 */
export function InvestmentCasePage() {
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const { caseId } = useParams<{ caseId?: string }>();
  const location = useLocation();
  const origin = (location.state as { origin?: string; ticker?: string } | null)?.origin ?? null;
  const originTicker = (location.state as { origin?: string; ticker?: string } | null)?.ticker ?? null;
  const originLabelKey: TranslationKey | null =
    origin === "portfolio"
      ? "investmentCase.origin.portfolio"
      : origin === "history"
        ? "investmentCase.origin.history"
        : origin === "daily-brief"
          ? "investmentCase.origin.dailyBrief"
          : origin === "discovery"
            ? "investmentCase.origin.discovery"
            : origin === "watchlist"
              ? "investmentCase.origin.watchlist"
              : origin === "companion"
                ? "investmentCase.origin.companion"
                : origin === "company"
                  ? "investmentCase.origin.company"
                  : null;

  /**
   * Origin-aware return (Sprint 8 audit fix): the badge above already
   * names which of the three real entry points sent the investor here
   * — this reuses that same `origin` value so the return link actually
   * goes back there, instead of always landing on Portfolio regardless
   * of where the investor came from. A missing or unrecognized origin
   * (a brand-new Case, or a direct URL) still falls back to Portfolio,
   * the one origin with nothing more specific to return to.
   */
  // Product Sprint 7 (Deliverable 9 -- Navigation): `origin === "companion"`
  // previously had no explicit branch here, unlike the badge above
  // (`originLabelKey`), which does name it -- it silently fell through
  // to the same final `/portfolio` default every unrecognized origin
  // uses. The destination was already correct (Companion is a
  // persistent, cross-page overlay with no route of its own, so
  // Portfolio is as sensible a landing spot as any), but naming it
  // explicitly keeps this ternary chain honest about every origin the
  // badge can show, rather than one falling through silently.
  const returnTo: string =
    origin === "history"
      ? "/history"
      : origin === "daily-brief"
        ? "/daily-brief"
        : origin === "discovery"
          ? "/discovery"
          : origin === "watchlist"
            ? "/watchlist"
            : origin === "company" && originTicker
              ? `/company/${encodeURIComponent(originTicker)}`
              : "/portfolio";
  const returnLabelKey: TranslationKey =
    origin === "history"
      ? "investmentCase.returnTo.history"
      : origin === "daily-brief"
        ? "investmentCase.returnTo.dailyBrief"
        : origin === "discovery"
          ? "investmentCase.returnTo.discovery"
          : origin === "watchlist"
            ? "investmentCase.returnTo.watchlist"
            : origin === "company" && originTicker
              ? "investmentCase.returnTo.company"
              : "investmentCase.returnTo.portfolio";

  const [status, setStatus] = useState<CaseStatus>({ kind: "loading" });

  const [observations, setObservations] = useState<ObservationRecord[]>([]);
  const [listStatus, setListStatus] = useState<ListStatus>({ kind: "loading" });
  const [createStatus, setCreateStatus] = useState<ObservationCreateStatus>({ kind: "idle" });
  const [subjectInput, setSubjectInput] = useState("");
  const [statementInput, setStatementInput] = useState("");

  const [allEvidence, setAllEvidence] = useState<EvidenceRecord[]>([]);
  const [evidenceListStatus, setEvidenceListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [evidenceCreateStatus, setEvidenceCreateStatus] = useState<
    Record<string, EvidenceCreateStatus>
  >({});
  const [evidenceForm, setEvidenceForm] = useState<Record<string, EvidenceFormInput>>({});
  const [evidenceDeleteStatus, setEvidenceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allKnowledgeReferences, setAllKnowledgeReferences] = useState<KnowledgeReferenceRecord[]>(
    [],
  );
  const [knowledgeReferenceListStatus, setKnowledgeReferenceListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [knowledgeReferenceCreateStatus, setKnowledgeReferenceCreateStatus] = useState<
    Record<string, KnowledgeReferenceCreateStatus>
  >({});
  const [knowledgeReferenceDeleteStatus, setKnowledgeReferenceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allReasoningTraces, setAllReasoningTraces] = useState<ReasoningTraceRecord[]>([]);
  const [reasoningTraceListStatus, setReasoningTraceListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [reasoningTraceCreateStatus, setReasoningTraceCreateStatus] = useState<
    Record<string, ReasoningTraceCreateStatus>
  >({});
  const [reasoningTraceDeleteStatus, setReasoningTraceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allJudgments, setAllJudgments] = useState<JudgmentRecord[]>([]);
  const [judgmentListStatus, setJudgmentListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [judgmentCreateStatus, setJudgmentCreateStatus] = useState<
    Record<string, JudgmentCreateStatus>
  >({});
  const [judgmentForm, setJudgmentForm] = useState<Record<string, string>>({});
  const [judgmentDeleteStatus, setJudgmentDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allDecisions, setAllDecisions] = useState<DecisionRecord[]>([]);
  const [decisionListStatus, setDecisionListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [decisionCreateStatus, setDecisionCreateStatus] = useState<
    Record<string, DecisionCreateStatus>
  >({});
  const [decisionForm, setDecisionForm] = useState<Record<string, DecisionFormInput>>({});

  const [allOutcomes, setAllOutcomes] = useState<OutcomeRecord[]>([]);
  const [outcomeListStatus, setOutcomeListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [outcomeCreateStatus, setOutcomeCreateStatus] = useState<
    Record<string, OutcomeCreateStatus>
  >({});
  const [outcomeForm, setOutcomeForm] = useState<Record<string, OutcomeFormInput>>({});
  const [tradeApplyStatus, setTradeApplyStatus] = useState<Record<string, TradeApplyStatus>>({});

  const alphaPortfolioResource = useAlphaPortfolio();
  const alphaPortfolioStatus: AlphaPortfolioStatus =
    alphaPortfolioResource.kind === "loaded"
      ? { kind: "loaded", view: alphaPortfolioResource.data as AlphaPortfolioView }
      : alphaPortfolioResource;
  const [tradeLogStatus, setTradeLogStatus] = useState<TradeLogFetchStatus>({ kind: "loading" });
  const watchlistStatus: WatchlistFetchStatus = useAlphaWatchlist();
  const [watchlistAddStatus, setWatchlistAddStatus] = useState<"idle" | "submitting" | "error">("idle");
  const [pendingAction, setPendingAction] = useState<PositionAction | null>(null);
  const [investmentCaseAnalysis, setInvestmentCaseAnalysis] = useState<InvestmentCaseAnalysisFetchStatus>({
    kind: "loading",
  });
  /** Product Sprint 4 (Portfolio Fit Engine) -- `null` once loaded means
   * the backend genuinely has no assessment for this Case (a disclosed
   * absence, not a fetch failure), distinct from `status.kind` staying
   * `"loading"`/`"error"`. */
  const [portfolioFitStatus, setPortfolioFitStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; assessment: PortfolioFitAssessmentView | null }
  >({ kind: "loading" });

  /** Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
   * Understanding, Deliverable 6) -- independent fetch, same pattern
   * as `portfolioFitStatus` above. */
  const [evidenceGraphStatus, setEvidenceGraphStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; graph: EvidenceGraphView }
  >({ kind: "loading" });

  /** Atlas Intelligence Sprint 11 (Decision Readiness & Decision
   * Eligibility, Deliverable 6) -- independent fetch, same pattern as
   * `evidenceGraphStatus` above. `change` is fetched separately and
   * allowed to fail/stay null silently -- "latest readiness change" is
   * a bonus fact, never a blocking one. */
  const [decisionReadinessStatus, setDecisionReadinessStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; readiness: DecisionReadinessView }
  >({ kind: "loading" });
  const [decisionReadinessChange, setDecisionReadinessChange] = useState<DecisionReadinessChangeView | null>(null);

  /** Atlas Decision Layer Sprint 1 (Investment Decision Synthesis,
   * Deliverable 6) -- independent fetch, same pattern as
   * `decisionReadinessStatus` above. `change` is fetched separately and
   * allowed to fail/stay null silently. */
  const [investmentDecisionStatus, setInvestmentDecisionStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; decision: InvestmentDecisionView }
  >({ kind: "loading" });
  const [investmentDecisionChange, setInvestmentDecisionChange] = useState<DecisionChangeView | null>(null);

  /** Atlas Decision Layer Sprint 2 (Recommendation Strength &
   * Conviction, Deliverable 6) -- independent fetch, same pattern as
   * `investmentDecisionStatus` above. */
  const [recommendationConvictionStatus, setRecommendationConvictionStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; conviction: RecommendationConvictionView }
  >({ kind: "loading" });
  const [recommendationConvictionChange, setRecommendationConvictionChange] = useState<ConvictionChangeView | null>(null);

  /** Atlas Decision Layer Sprint 3 (Decision Path & Required
   * Progress, Deliverable 6) -- independent fetch, same pattern as
   * `recommendationConvictionStatus` above. */
  const [decisionPathStatus, setDecisionPathStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; path: DecisionPathView }
  >({ kind: "loading" });
  const [decisionPathChange, setDecisionPathChange] = useState<DecisionPathChangeView | null>(null);

  /** Atlas Decision Layer Sprint 4 (Decision Alternatives &
   * Opportunity Cost, Deliverable 6) -- independent fetch, same
   * pattern as `decisionPathStatus` above. */
  const [opportunityCostStatus, setOpportunityCostStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; opportunityCost: OpportunityCostView }
  >({ kind: "loading" });
  const [opportunityCostChange, setOpportunityCostChange] = useState<OpportunityCostChangeView | null>(null);

  /** Atlas Decision Layer Sprint 5 (Decision Memory, Deliverable 6)
   * -- independent fetch, same pattern as `opportunityCostStatus`
   * above. No separate change fetch: `DecisionMemoryView.latestChange`
   * already embeds the latest real transition. */
  const [decisionMemoryStatus, setDecisionMemoryStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; memory: DecisionMemoryView }
  >({ kind: "loading" });

  /** Atlas Decision Layer Sprint 6 (Decision Explanation &
   * Traceability, Deliverable 6) -- independent fetch, same pattern
   * as `decisionMemoryStatus` above. */
  const [decisionExplanationStatus, setDecisionExplanationStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; explanation: DecisionExplanationView }
  >({ kind: "loading" });

  /** Atlas Decision Layer Sprint 7 (Decision Reliability, Deliverable
   * 7) -- independent fetch, same pattern as `decisionExplanationStatus`
   * above. */
  const [decisionReliabilityStatus, setDecisionReliabilityStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; reliability: DecisionReliabilityView }
  >({ kind: "loading" });

  /** Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis,
   * Deliverable 7) -- independent fetch, same pattern as
   * `decisionReliabilityStatus` above. */
  const [portfolioDecisionStatus, setPortfolioDecisionStatus] = useState<
    { kind: "loading" } | { kind: "error" } | { kind: "loaded"; decision: PortfolioDecisionView }
  >({ kind: "loading" });

  /** Fix Sprint 3 (Investment Case Post-Mutation Refresh Correctness).
   * `caseDataVersion` is a plain, request-local invalidation counter --
   * no polling, no timer, no global event: every one of the fetch
   * effects below that reads this Case's own Decision Layer state
   * (case analysis, Portfolio Fit, Evidence Graph, and all nine
   * Decision Layer sections) lists it as a dependency alongside
   * `caseId`, so incrementing it re-runs exactly those effects, the
   * same way a `caseId` change already does. Every mutation that
   * writes to a repository `InvestmentCaseCompositionService.build()`
   * itself reads (Decision, Observation, Evidence, Outcome -- verified
   * directly in `atlas/alpha/investment_case/service.py`; confirmed by
   * grep that Judgment/KnowledgeReference/ReasoningTrace are read by no
   * Alpha service at all, so their own mutations do not increment this)
   * increments it on success only -- never on validation/API error, so
   * a failed mutation leaves the page exactly as it was.
   * `portfolioDataVersion` is the identical mechanism for the two
   * Portfolio-scoped fetches (`/api/alpha-portfolio`, `/api/alpha-
   * portfolio/trade-log`), incremented only by `applyTrade`, since a
   * trade is the one mutation on this page that changes Portfolio
   * state rather than only this Case's own. */
  const [caseDataVersion, setCaseDataVersion] = useState(0);
  const [portfolioDataVersion, setPortfolioDataVersion] = useState(0);
  /** Internal Alpha Stabilization 1 (MSFT price root cause fix) -- the
   * manual "Uppdatera" button's own local in-flight flag, purely for
   * immediate UI feedback (disables the button while a request is in
   * the air). The real dedup/serialization guarantee lives server-side
   * (`PriceRefreshCoordinator`); this only prevents a double-click from
   * firing two HTTP requests, it is not what makes concurrent refresh
   * attempts safe. */
  const [priceRefreshStatus, setPriceRefreshStatus] = useState<"idle" | "refreshing">("idle");

  /** Action Flow Tier 2 (Workspace Migration Phase 3, approved §13
   * Option A) -- whether the inline decision-recording panel is
   * expanded. Starts collapsed; the header's own "[Record a decision]"
   * trigger (or the outstanding-outcome nudge) opens it. A decision
   * already in progress or awaiting its Outcome report keeps the panel
   * implicitly open regardless of this flag -- see the panel's own
   * render guard below. */
  const [isDecisionPanelExpanded, setIsDecisionPanelExpanded] = useState(false);

  /** Sprint 4 (Portfolio Evolution & Outcome Loop) fix: `reportDecisionId`
   * previously resolved only from `caseLevelDecisionStatus`, which is
   * local component state that resets to "idle" on every mount -- so a
   * Decision recorded in an earlier session had no real way to reach the
   * outcome-report form again (the "N decision(s) awaiting an outcome"
   * nudge just reopened the "record a new decision" chooser instead).
   * This holds the real, server-loaded Decision id extracted from an
   * Outstanding Work item when the investor explicitly asks to report on
   * it, so the same, unmodified `submitOutcome`/`applyTrade` machinery
   * below (already generic over its dictionary key) can be reused. */
  const [reportingExistingDecisionId, setReportingExistingDecisionId] = useState<string | null>(
    null,
  );

  /** The trigger button unmounts the moment the panel below opens (see
   * that panel's own comment), so without this the browser drops focus
   * to `<body>` and a keyboard/screen-reader user loses their place
   * entirely. Moving focus onto the panel's own heading keeps it
   * discoverable without changing the panel's visible layout. */
  const decisionPanelHeadingRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (isDecisionPanelExpanded) {
      decisionPanelHeadingRef.current?.focus();
    }
  }, [isDecisionPanelExpanded]);

  /** Figma-fidelity rebuild -- the approved screen's own bottom tab bar
   * (Decision History / Timeline / Last Activity / Outstanding Work /
   * Outcomes / More Details), replacing the previous single `<details>`
   * "More details" catch-all: the approved screen shows six distinct
   * labels, not one. Every tab's content is unchanged from its former
   * always-rendered-when-open location -- only the container (a real
   * tab switch instead of native `<details>`) and default tab moved. */
  type InvestmentCaseTabKey =
    | "decisionHistory"
    | "timeline"
    | "lastActivity"
    | "outstandingWork"
    | "outcomes"
    | "moreDetails";
  const [activeTab, setActiveTab] = useState<InvestmentCaseTabKey>("decisionHistory");

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setStatus({ kind: "loading" });

    fetch(`/api/cases/${caseId}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<CaseSummary>;
      })
      .then((caseSummary) => setStatus({ kind: "loaded", case: caseSummary }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });

    return () => controller.abort();
  }, [caseId]);

  /** Daily Brief RC-3, Phase 4 (Read State Everywhere) -- every real
   * navigation path into an Investment Case (Daily Brief, Portfolio,
   * Watchlist, Discover, a direct link) converges on this one page, so
   * this is the single place a change genuinely gets marked SEEN,
   * rather than duplicating a mark-seen call at each origin's own
   * click handler. Reuses the exact same change-log read/write Daily
   * Brief itself uses -- no second read-state mechanism. Best-effort
   * and silent: this page renders nothing about it either way, and a
   * failed call simply leaves the change NEW for one more Daily Brief
   * visit, never a lie in the other direction. */
  useEffect(() => {
    if (!caseId) return;
    const controller = new AbortController();
    fetchDailyBriefChangeLog(ALPHA_PLACEHOLDER_USER_ID, controller.signal)
      .then((groups) => {
        const unseen = groups.find((group) => group.primary.caseId === caseId && group.isNew);
        if (unseen) return markDailyBriefChangesSeen(ALPHA_PLACEHOLDER_USER_ID, [unseen.primary.id], controller.signal);
        return undefined;
      })
      .catch(() => {});
    return () => controller.abort();
  }, [caseId]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setInvestmentCaseAnalysis({ kind: "loading" });

    fetch(`/api/cases/${caseId}/analysis`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<InvestmentCaseAnalysisView>;
      })
      .then((report) => setInvestmentCaseAnalysis({ kind: "loaded", report }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setInvestmentCaseAnalysis({ kind: "error" });
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  // Product Sprint 4 (Portfolio Fit Engine, Deliverable 8) -- the new
  // Portfolio Fit section's own fetch, independent of the analysis
  // fetch above (Portfolio Fit is a separate Alpha-layer interpretation,
  // not a field on `InvestmentCaseAnalysisView`).
  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setPortfolioFitStatus({ kind: "loading" });

    fetchPortfolioFitForCase(caseId, controller.signal)
      .then((assessment) => setPortfolioFitStatus({ kind: "loaded", assessment }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioFitStatus({ kind: "error" });
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion, portfolioDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setEvidenceGraphStatus({ kind: "loading" });

    fetchEvidenceGraph(caseId, controller.signal)
      .then((graph) => setEvidenceGraphStatus({ kind: "loaded", graph }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setEvidenceGraphStatus({ kind: "error" });
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setDecisionReadinessStatus({ kind: "loading" });

    fetchDecisionReadiness(caseId, controller.signal)
      .then((readiness) => setDecisionReadinessStatus({ kind: "loaded", readiness }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionReadinessStatus({ kind: "error" });
      });
    fetchDecisionReadinessChange(caseId, controller.signal)
      .then((change) => setDecisionReadinessChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setInvestmentDecisionStatus({ kind: "loading" });

    fetchInvestmentDecision(caseId, controller.signal)
      .then((decision) => setInvestmentDecisionStatus({ kind: "loaded", decision }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setInvestmentDecisionStatus({ kind: "error" });
      });
    fetchInvestmentDecisionChange(caseId, controller.signal)
      .then((change) => setInvestmentDecisionChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setRecommendationConvictionStatus({ kind: "loading" });

    fetchRecommendationConviction(caseId, controller.signal)
      .then((conviction) => setRecommendationConvictionStatus({ kind: "loaded", conviction }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setRecommendationConvictionStatus({ kind: "error" });
      });
    fetchRecommendationConvictionChange(caseId, controller.signal)
      .then((change) => setRecommendationConvictionChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setDecisionPathStatus({ kind: "loading" });

    fetchDecisionPath(caseId, controller.signal)
      .then((path) => setDecisionPathStatus({ kind: "loaded", path }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionPathStatus({ kind: "error" });
      });
    fetchDecisionPathChange(caseId, controller.signal)
      .then((change) => setDecisionPathChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  /** Investment Case Decision Layer Bundle (Opportunity Cost Cross-
   * Case Computation Review, follow-up implementation sprint) --
   * replaces what were four independent fetches (opportunity-cost +
   * its own change fetch, decision-memory, decision-explanation,
   * portfolio-decision) with a single request. `portfolioDataVersion`
   * is kept in the dependency array (not just `caseDataVersion`) since
   * `portfolio_decision`'s own data depends on portfolio-wide state
   * (weights, other holdings), exactly as its own separate effect
   * required before this change. Each of the four sections keeps its
   * own independent loading/error status -- a `null` field in the
   * bundle (whichever section it came from) maps to that section's own
   * `"error"` state, matching exactly how that section's own separate
   * fetch already handled a 404 or an unexpected failure, without
   * affecting the other three. */
  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setOpportunityCostStatus({ kind: "loading" });
    setDecisionMemoryStatus({ kind: "loading" });
    setDecisionExplanationStatus({ kind: "loading" });
    setPortfolioDecisionStatus({ kind: "loading" });

    fetchInvestmentCaseDecisionLayerBundle(caseId, controller.signal)
      .then((bundle) => {
        setOpportunityCostStatus(
          bundle.opportunityCost !== null ? { kind: "loaded", opportunityCost: bundle.opportunityCost } : { kind: "error" },
        );
        setOpportunityCostChange(bundle.opportunityCostChange);
        setDecisionMemoryStatus(
          bundle.decisionMemory !== null ? { kind: "loaded", memory: bundle.decisionMemory } : { kind: "error" },
        );
        setDecisionExplanationStatus(
          bundle.decisionExplanation !== null
            ? { kind: "loaded", explanation: bundle.decisionExplanation }
            : { kind: "error" },
        );
        setPortfolioDecisionStatus(
          bundle.portfolioDecision !== null ? { kind: "loaded", decision: bundle.portfolioDecision } : { kind: "error" },
        );
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setOpportunityCostStatus({ kind: "error" });
        setDecisionMemoryStatus({ kind: "error" });
        setDecisionExplanationStatus({ kind: "error" });
        setPortfolioDecisionStatus({ kind: "error" });
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion, portfolioDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setDecisionReliabilityStatus({ kind: "loading" });

    fetchDecisionReliability(caseId, controller.signal)
      .then((reliability) => setDecisionReliabilityStatus({ kind: "loaded", reliability }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionReliabilityStatus({ kind: "error" });
      });

    return () => controller.abort();
  }, [caseId, caseDataVersion]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setListStatus({ kind: "loading" });

    fetch("/api/observations", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<ObservationRecord[]>;
      })
      .then((allObservations) => {
        setObservations(allObservations.filter((o) => o.caseId === caseId));
        setListStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setListStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });

    return () => controller.abort();
  }, [caseId]);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/alpha-portfolio/trade-log", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<TradeLogEntry[]>;
      })
      .then((trades) => setTradeLogStatus({ kind: "loaded", trades }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setTradeLogStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });

    return () => controller.abort();
  }, [portfolioDataVersion]);

  const unknownErrorMessage = t("common.unknownError");
  useApiList<EvidenceRecord>(
    "/api/evidence",
    caseId,
    setAllEvidence,
    setEvidenceListStatus,
    unknownErrorMessage,
  );
  useApiList<KnowledgeReferenceRecord>(
    "/api/knowledge-references",
    caseId,
    setAllKnowledgeReferences,
    setKnowledgeReferenceListStatus,
    unknownErrorMessage,
  );
  useApiList<ReasoningTraceRecord>(
    "/api/reasoning-traces",
    caseId,
    setAllReasoningTraces,
    setReasoningTraceListStatus,
    unknownErrorMessage,
  );
  useApiList<JudgmentRecord>(
    "/api/judgments",
    caseId,
    setAllJudgments,
    setJudgmentListStatus,
    unknownErrorMessage,
  );
  useApiList<DecisionRecord>(
    "/api/decisions",
    caseId,
    setAllDecisions,
    setDecisionListStatus,
    unknownErrorMessage,
  );
  useApiList<OutcomeRecord>(
    "/api/outcomes",
    caseId,
    setAllOutcomes,
    setOutcomeListStatus,
    unknownErrorMessage,
  );

  function submitEvidence(observationId: string) {
    const form = evidenceForm[observationId] ?? EMPTY_EVIDENCE_FORM;
    setEvidenceCreateStatus((current) => ({ ...current, [observationId]: { kind: "submitting" } }));

    fetch("/api/evidence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        observationId,
        statement: form.summary,
        direction: form.direction,
        source: form.source || null,
        observedAt: new Date().toISOString(),
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setEvidenceCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? t("common.invalidInput"),
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const evidence = (await response.json()) as EvidenceRecord;
        setAllEvidence((current) => [...current, evidence]);
        setEvidenceCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", evidence },
        }));
        // Fix Sprint 3: new Evidence is a `composition.build()` input
        // (`evidence_repository`) -- every Decision Layer section
        // derived from it is now stale until this bumps.
        setCaseDataVersion((v) => v + 1);
      })
      .catch((error: unknown) => {
        setEvidenceCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function deleteEvidence(evidenceId: string) {
    deleteRecord<EvidenceRecord>(
      `/api/evidence/${evidenceId}`,
      evidenceId,
      (e) => e.evidenceId === evidenceId,
      setAllEvidence,
      setEvidenceDeleteStatus,
      // Fix Sprint 3: same reasoning as `submitEvidence` above -- removing
      // Evidence changes the same `composition.build()` input.
      () => setCaseDataVersion((v) => v + 1),
    );
  }

  /** Internal Alpha Stabilization 1 (MSFT price root cause fix) -- the
   * manual "Uppdatera" escape hatch, calling the exact same server-side
   * `refresh_price_only` the lazy background trigger on the analysis
   * fetch itself already uses (`POST /cases/{caseId}/refresh-price`).
   * Bumps `caseDataVersion` only on a real, attempted call (whether it
   * succeeded, was a no-op duplicate/quota-exhausted, or failed) so the
   * page re-reads the server's own current freshness status either
   * way -- never assumes success client-side. */
  function refreshPrice() {
    if (!caseId || priceRefreshStatus === "refreshing") return;
    setPriceRefreshStatus("refreshing");
    fetch(`/api/cases/${caseId}/refresh-price`, { method: "POST" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<{ attempted: boolean }>;
      })
      .then(() => {
        setCaseDataVersion((v) => v + 1);
      })
      .catch(() => {
        // Honest failure: the analysis refetch below will still show
        // the real, unchanged `priceFreshness` from the server (never
        // client-side guessed as "fresh") -- nothing to fabricate here.
      })
      .finally(() => {
        setPriceRefreshStatus("idle");
      });
  }

  function submitKnowledgeReference(observationId: string) {
    if (!caseId) return;
    setKnowledgeReferenceCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/knowledge-references", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        target: { targetType: "Observation", targetId: observationId },
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setKnowledgeReferenceCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? t("common.invalidInput"),
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const knowledgeReference = (await response.json()) as KnowledgeReferenceRecord;
        setAllKnowledgeReferences((current) => [...current, knowledgeReference]);
        setKnowledgeReferenceCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", knowledgeReference },
        }));
      })
      .catch((error: unknown) => {
        setKnowledgeReferenceCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function deleteKnowledgeReference(knowledgeReferenceId: string) {
    deleteRecord<KnowledgeReferenceRecord>(
      `/api/knowledge-references/${knowledgeReferenceId}`,
      knowledgeReferenceId,
      (k) => k.knowledgeReferenceId === knowledgeReferenceId,
      setAllKnowledgeReferences,
      setKnowledgeReferenceDeleteStatus,
    );
  }

  function submitReasoningTrace(observationId: string) {
    if (!caseId) return;
    setReasoningTraceCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/reasoning-traces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        supports: [{ targetType: "Observation", targetId: observationId }],
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setReasoningTraceCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? t("common.invalidInput"),
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const reasoningTrace = (await response.json()) as ReasoningTraceRecord;
        setAllReasoningTraces((current) => [...current, reasoningTrace]);
        setReasoningTraceCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", reasoningTrace },
        }));
      })
      .catch((error: unknown) => {
        setReasoningTraceCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function deleteReasoningTrace(reasoningTraceId: string) {
    deleteRecord<ReasoningTraceRecord>(
      `/api/reasoning-traces/${reasoningTraceId}`,
      reasoningTraceId,
      (r) => r.reasoningTraceId === reasoningTraceId,
      setAllReasoningTraces,
      setReasoningTraceDeleteStatus,
    );
  }

  function submitJudgment(observationId: string) {
    if (!caseId) return;
    const characterization = judgmentForm[observationId] ?? "";
    setJudgmentCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/judgments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        characterization,
        subject: { targetType: "Observation", targetId: observationId },
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setJudgmentCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? t("common.invalidInput"),
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const judgment = (await response.json()) as JudgmentRecord;
        setAllJudgments((current) => [...current, judgment]);
        setJudgmentCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", judgment },
        }));
      })
      .catch((error: unknown) => {
        setJudgmentCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function deleteJudgment(judgmentId: string) {
    deleteRecord<JudgmentRecord>(
      `/api/judgments/${judgmentId}`,
      judgmentId,
      (j) => j.judgmentId === judgmentId,
      setAllJudgments,
      setJudgmentDeleteStatus,
    );
  }

  /**
   * `formKey` scopes `decisionForm`/`decisionCreateStatus` (any string —
   * an Observation id for the legacy per-Observation entry point, or
   * `CASE_LEVEL_DECISION_KEY` for the new top-level "What would you like
   * to do?" entry point). `observationId`, separately, is the actual
   * optional anchor sent to the backend — omitted entirely (not merely
   * `null`) when absent, matching `Decision.observation_id`'s own
   * optional-anchor design (`atlas/core/domain/decision/entity.py`):
   * every Decision is valid with no Observation at all. This is the same
   * `POST /api/decisions` call either way — one workflow, two entry
   * points into the same form-state shape.
   */
  function submitDecision(formKey: string, observationId?: string) {
    if (!caseId) return;
    const form = decisionForm[formKey] ?? EMPTY_DECISION_FORM;
    const confidence = Number.parseInt(form.confidence, 10);
    setDecisionCreateStatus((current) => ({
      ...current,
      [formKey]: { kind: "submitting" },
    }));

    fetch("/api/decisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        userId: ALPHA_PLACEHOLDER_USER_ID,
        decisionType: form.decisionType,
        subject: form.subject,
        reason: form.reason,
        confidence,
        ...(observationId ? { observationId } : {}),
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 422 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setDecisionCreateStatus((current) => ({
            ...current,
            [formKey]: {
              kind: response.status === 404 ? "api-error" : "validation-error",
              message: body.detail ?? t("common.invalidInput"),
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const decision = (await response.json()) as DecisionRecord;
        setAllDecisions((current) => [...current, decision]);
        setDecisionCreateStatus((current) => ({
          ...current,
          [formKey]: { kind: "success", decision },
        }));
        // Fix Sprint 3: a new Decision is a `composition.build()` input
        // (`decision_repository`) -- every Decision Layer section
        // derived from it is now stale until this bumps.
        setCaseDataVersion((v) => v + 1);
      })
      .catch((error: unknown) => {
        setDecisionCreateStatus((current) => ({
          ...current,
          [formKey]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function applyTrade(observationId: string, form: OutcomeFormInput, outcome: OutcomeRecord) {
    setTradeApplyStatus((current) => ({ ...current, [observationId]: { kind: "applying" } }));

    fetch("/api/alpha-portfolio/apply-trade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        outcomeId: outcome.id,
        decisionId: form.decisionId,
        security: form.security,
        transactionType: form.transactionType,
        quantity: Number.parseFloat(form.quantity),
        executionPrice: Number.parseFloat(form.executionPrice),
        executedAt: form.executedAt || new Date().toISOString(),
        fees: form.fees.trim() === "" ? null : Number.parseFloat(form.fees),
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = (await response.json().catch(() => ({}))) as { detail?: string };
          setTradeApplyStatus((current) => ({
            ...current,
            [observationId]: {
              kind: "error",
              message: body.detail ?? `Backend responded with ${response.status}`,
            },
          }));
          return;
        }
        const view = (await response.json()) as { awaitingReconciliation: boolean };
        setTradeApplyStatus((current) => ({
          ...current,
          [observationId]: {
            kind: view.awaitingReconciliation ? "awaiting-reconciliation" : "updated",
          },
        }));
        // Fix Sprint 3: a trade changes Portfolio holdings (Portfolio-
        // scoped state, not only this Case's own) and, through
        // `portfolio_store`, `composition.build()`'s own `holding_context`
        // -- both this Case's Decision Layer sections and the Portfolio-
        // scoped fetches below are now stale until these bump.
        // Internal Alpha Stabilization 1 (navigation/cache fix):
        // `/api/alpha-portfolio` itself is no longer part of what
        // `portfolioDataVersion` re-fetches (that endpoint now goes
        // through the shared cache), so it needs its own explicit
        // invalidation here too -- `portfolioDataVersion` still governs
        // the trade-log re-fetch below unchanged.
        setCaseDataVersion((v) => v + 1);
        setPortfolioDataVersion((v) => v + 1);
        invalidateAlphaPortfolio();
      })
      .catch((error: unknown) => {
        setTradeApplyStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function submitOutcome(observationId: string) {
    const form = outcomeForm[observationId] ?? EMPTY_OUTCOME_FORM;

    if (form.isExternalTrade) {
      const quantity = Number.parseFloat(form.quantity);
      const executionPrice = Number.parseFloat(form.executionPrice);
      if (
        form.security.trim() === "" ||
        Number.isNaN(quantity) ||
        Number.isNaN(executionPrice) ||
        (form.fees.trim() !== "" && Number.isNaN(Number.parseFloat(form.fees)))
      ) {
        setOutcomeCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "validation-error",
            message: t("investmentCase.outcome.validation.tradeRequiredFields"),
          },
        }));
        return;
      }
    }

    setOutcomeCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/outcomes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decisionId: form.decisionId,
        statement: form.statement,
        occurredAt: new Date().toISOString(),
        note: form.note || null,
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setOutcomeCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? t("common.invalidInput"),
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const outcome = (await response.json()) as OutcomeRecord;
        setAllOutcomes((current) => [...current, outcome]);
        setOutcomeCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", outcome },
        }));
        // Fix Sprint 3: a new Outcome is a `composition.build()` input
        // (`outcome_repository`) -- every Decision Layer section derived
        // from it is now stale until this bumps. `applyTrade` below bumps
        // it again itself once the trade completes, which is correct: two
        // real, sequential state changes, two refreshes.
        setCaseDataVersion((v) => v + 1);
        if (form.isExternalTrade) {
          applyTrade(observationId, form, outcome);
        }
      })
      .catch((error: unknown) => {
        setOutcomeCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function submitObservation() {
    if (!caseId) return;
    setCreateStatus({ kind: "submitting" });

    fetch("/api/observations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        subject: subjectInput,
        statement: statementInput,
        observedAt: new Date().toISOString(),
      }),
    })
      .then(async (response) => {
        if (response.status === 400) {
          const body = (await response.json()) as { detail?: string };
          setCreateStatus({ kind: "validation-error", message: body.detail ?? t("common.invalidInput") });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const observation = (await response.json()) as ObservationRecord;
        setObservations((current) => [...current, observation]);
        setCreateStatus({ kind: "success", observation });
        // Fix Sprint 3: a new Observation is a `composition.build()`
        // input (`observation_repository`) -- every Decision Layer
        // section derived from it is now stale until this bumps.
        setCaseDataVersion((v) => v + 1);
      })
      .catch((error: unknown) => {
        setCreateStatus({
          kind: "api-error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  // ---------------------------------------------------------------------
  // Investment Case v2: derived, read-only state. Nothing below fetches
  // anything new beyond the one `alphaPortfolioStatus` effect above —
  // every value here is a pure derivation from state already fetched for
  // the legacy per-Observation sections, re-read at the Case level
  // instead of the Observation level. `allDecisions`/`allOutcomes` are
  // fetched unfiltered (`GET /api/decisions` and `/api/outcomes` return
  // every record in the system); every other page on this Case already
  // relies on client-side filtering by id, so filtering by `caseId` here
  // is the same pattern, just at the Case level rather than the
  // Observation level.
  // ---------------------------------------------------------------------

  const alphaHoldings = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.holdings : [];
  const linkedHolding = alphaHoldings.find((holding) => holding.caseId === caseId) ?? null;

  const caseDecisions = allDecisions.filter((decision) => decision.caseId === caseId);
  const caseOutcomes = allOutcomes.filter((outcome) => outcome.caseId === caseId);

  const observationIds = new Set(observations.map((o) => o.observationId));
  const evidenceForCase = allEvidence.filter((e) => observationIds.has(e.observationId));
  const knowledgeReferencesForCase = allKnowledgeReferences.filter(
    (k) => k.target.targetType === "Observation" && observationIds.has(k.target.targetId),
  );
  const reasoningTracesForCase = allReasoningTraces.filter((r) =>
    r.supports.some((s) => s.targetType === "Observation" && observationIds.has(s.targetId)),
  );
  const judgmentsForCase = allJudgments.filter(
    (j) => j.subject !== null && j.subject.targetType === "Observation" && observationIds.has(j.subject.targetId),
  );

  const lastActivityAt = latestTimestamp([
    ...observations.map((o) => o.observedAt),
    ...evidenceForCase.map((e) => e.observedAt),
    ...knowledgeReferencesForCase.map((k) => k.recordedAt),
    ...reasoningTracesForCase.map((r) => r.recordedAt),
    ...judgmentsForCase.map((j) => j.recordedAt),
    ...caseDecisions.map((d) => d.recordedAt),
    ...caseOutcomes.map((o) => o.recordedAt),
  ]);

  const assessmentStatusKey: TranslationKey =
    caseOutcomes.length > 0
      ? "investmentCase.assessment.outcomeRecorded"
      : caseDecisions.length > 0
        ? "investmentCase.assessment.decisionRecorded"
        : linkedHolding
          ? "investmentCase.assessment.heldNoAssessment"
          : "investmentCase.assessment.notLinkedYet";

  /** Opens the compact reason/confidence form for one of the four decision actions. */
  function openAction(action: PositionAction) {
    setPendingAction(action);
    setDecisionForm((current) => ({
      ...current,
      [CASE_LEVEL_DECISION_KEY]: {
        decisionType: ACTION_DECISION_TYPE[action],
        subject: linkedHolding?.ticker ?? "",
        reason: "",
        confidence: "50",
      },
    }));
    setDecisionCreateStatus((current) => ({
      ...current,
      [CASE_LEVEL_DECISION_KEY]: { kind: "creating" },
    }));
  }

  /** Also collapses Action Flow Tier 2 (Workspace Migration Phase 3) --
   * "Cancel" during the reason/confidence form, and "Close" after a
   * decision (and optionally its Outcome) has been recorded, both
   * return the page to its default, panel-collapsed state. */
  function closeAction() {
    setPendingAction(null);
    setDecisionCreateStatus((current) => ({
      ...current,
      [CASE_LEVEL_DECISION_KEY]: { kind: "idle" },
    }));
    setReportingExistingDecisionId(null);
    setIsDecisionPanelExpanded(false);
  }

  const caseLevelDecisionStatus: DecisionCreateStatus =
    decisionCreateStatus[CASE_LEVEL_DECISION_KEY] ?? { kind: "idle" };
  const caseLevelDecisionForm: DecisionFormInput =
    decisionForm[CASE_LEVEL_DECISION_KEY] ?? EMPTY_DECISION_FORM;

  // Reporting the completed external transaction after a recorded
  // Add/Trim/Remove decision reuses `outcomeForm`/`outcomeCreateStatus`/
  // `tradeApplyStatus`/`submitOutcome`/`applyTrade` exactly as the
  // per-Observation section does — only the dictionary key changes, from
  // an Observation id to the newly-recorded Decision's own id.
  const reportDecisionId =
    caseLevelDecisionStatus.kind === "success"
      ? caseLevelDecisionStatus.decision.id
      : reportingExistingDecisionId;
  const reportOutcomeStatus: OutcomeCreateStatus = reportDecisionId
    ? (outcomeCreateStatus[reportDecisionId] ?? { kind: "idle" })
    : { kind: "idle" };
  const reportOutcomeForm: OutcomeFormInput = reportDecisionId
    ? (outcomeForm[reportDecisionId] ?? {
        ...EMPTY_OUTCOME_FORM,
        decisionId: reportDecisionId,
        transactionType: pendingAction
          ? POSITION_ACTION_TRANSACTION_TYPE[pendingAction]
          : EMPTY_OUTCOME_FORM.transactionType,
      })
    : EMPTY_OUTCOME_FORM;
  const reportTradeApplyStatus: TradeApplyStatus = reportDecisionId
    ? (tradeApplyStatus[reportDecisionId] ?? { kind: "idle" })
    : { kind: "idle" };

  // ---------------------------------------------------------------------
  // Sprint 4 (Decision Continuity & History): Last activity, Decision
  // Timeline, and Outstanding work all reuse `deriveActivity`/
  // `deriveOutstandingWork` (`../activity/deriveActivity.ts`) — the same
  // functions History and Dashboard use — scoped to this Case by
  // filtering on `caseId`, so "what happened" is defined in exactly one
  // place rather than three.
  // ---------------------------------------------------------------------

  const caseTrades =
    tradeLogStatus.kind === "loaded"
      ? tradeLogStatus.trades.filter((trade) => caseDecisions.some((d) => d.id === trade.decisionId))
      : [];

  const caseTimeline =
    alphaPortfolioStatus.kind === "loaded"
      ? sortActivity(
          deriveActivity(caseDecisions, caseOutcomes, caseTrades, alphaPortfolioStatus.view.holdings),
          "oldest",
        )
      : [];

  const latestOf = (kind: "decision" | "outcome" | "trade") => {
    const matches = caseTimeline.filter((event) => event.kind === kind);
    return matches.length > 0 ? matches[matches.length - 1] : null;
  };
  const lastDecisionEvent = latestOf("decision");
  const lastOutcomeEvent = latestOf("outcome");
  const lastTradeEvent = latestOf("trade");

  const caseOutstandingWork =
    alphaPortfolioStatus.kind === "loaded"
      ? deriveOutstandingWork(
          caseDecisions,
          caseOutcomes,
          caseTrades,
          alphaPortfolioStatus.view.holdings,
        ).filter((item) => item.caseId === caseId)
      : [];

  /** Header Tier 1 nudge (approved §13): the same real, already-
   * deduplicated set Outstanding Work renders in full further down the
   * page (progressive disclosure), just counted -- never a second
   * computation. `reconciliation-needed` is a Portfolio-level holding
   * concern, not a per-Case Decision awaiting its own Outcome, so it's
   * excluded here exactly as Outstanding Work's own render already
   * excludes it. */
  const decisionsAwaitingOutcome = caseOutstandingWork.filter(
    (item) => item.kind !== "reconciliation-needed",
  );

  const companyProfile = investmentCaseAnalysis.kind === "loaded" ? investmentCaseAnalysis.report.companyProfile : null;

  /** Product Sprint 10 (Navigation & Workflow Excellence, Deliverable
   * 4/5): `linkedHolding` alone left any case for a ticker that isn't
   * (yet) a Portfolio holding without a resolvable ticker at all -- no
   * Compare link, no Add-to-Watchlist affordance. `companyProfile.ticker`
   * is populated for any case with real analysis, regardless of
   * Portfolio/Watchlist status, so it's the more general source; falls
   * back to `linkedHolding`, and finally to `originTicker` (live-tested:
   * a Watchlist entry with no analysis yet -- e.g. `VOLVO B` -- arrives
   * here with neither `companyProfile` nor a linked holding, so without
   * this last fallback the ticker was unresolvable even though
   * `WatchlistPage.tsx` already knew it and now passes it along). */
  const resolvedTicker = companyProfile?.ticker ?? linkedHolding?.ticker ?? originTicker ?? null;
  const isOnWatchlist =
    watchlistStatus.kind === "loaded" &&
    resolvedTicker !== null &&
    watchlistStatus.entries.some((entry) => entry.ticker === resolvedTicker);

  function handleAddToWatchlist() {
    if (!resolvedTicker) return;
    setWatchlistAddStatus("submitting");
    addTickerToWatchlist(resolvedTicker).then((result) => {
      if (result.kind === "added") {
        setWatchlistAddStatus("idle");
      } else {
        setWatchlistAddStatus("error");
      }
    });
  }

  const identityLine = companyProfile
    ? [companyProfile.exchange, companyProfile.sector, companyProfile.industry].filter(Boolean).join(" · ")
    : "";
  /** Visual Fidelity Pass -- the approved screen's single compact
   * metadata line (Valuation / Portfolio fit / Portfolio weight /
   * Status), pipe-separated, replacing four separate paragraphs.
   * Every value is the same real one those paragraphs already read --
   * only the presentation is denser.
   *
   * Product Sprint 4 -- Portfolio Fit is now a real value (Deliverable
   * 8's own full section, further down this page, is the same
   * `portfolioFitStatus` fetch read in full; this line stays the
   * existing compact one-word summary, never a duplicated computation). */
  const metadataLineParts: string[] =
    investmentCaseAnalysis.kind === "loaded"
      ? [
          // Calibration Phase 2 (Investment Case Coherence
          // Implementation), Phase 4/C4: relabeled from bare
          // "Valuation" -- this is a vs-own-trading-history comparison
          // (`fcfYieldStatus`), a genuinely different question than
          // `ValuationSupportCard`'s own capital-deployment verdict
          // shown just below. Two real, independently-designed facts
          // (`atlas.analysis_engine.valuation.support`'s own docstring)
          // sharing the bare word "Valuation" is exactly the labeling
          // collision Phase 1's audit found; this line now names what
          // it actually measures.
          `${t("investmentCase.header.valuationVsHistoryLabel")}: ${t(VALUATION_STATUS_KEY[investmentCaseAnalysis.report.valuationContext.fcfYieldStatus])}`,
          `${t("investmentCase.header.portfolioFitLabel")}: ${
            portfolioFitStatus.kind === "loaded" && portfolioFitStatus.assessment !== null
              ? t(FIT_RATING_KEY[portfolioFitStatus.assessment.overall])
              : t("investmentCase.atlasView.notAvailable")
          }`,
          linkedHolding
            ? `${t("investmentCase.header.currentAllocation", { percent: linkedHolding.weightPercent.toFixed(1) })}`
            : null,
          // Calibration Phase 2, Phase 2/C6: the "Status" badge that
          // used to render here (`deriveCaseStatus`, "Worth a look"/
          // "Time-sensitive"/"Healthy") answered a workflow question
          // ("does this case need review") from the exact same visual
          // position -- right beside the ticker -- a reader expects a
          // recommendation-direction verdict. Removed rather than
          // relabeled: the real recommendation now leads HeroCard
          // below, and this workflow signal had no other consumer on
          // this page (`deriveCaseStatus`/`CaseStatusLevel` removed
          // from `deriveExecutiveSummary.ts` alongside this).
        ].filter((part): part is string => part !== null)
      : [];

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        {/* Header — company/security identity is the primary title; the
            Case id is secondary/technical only (never the primary
            identity). Ticker comes from the Alpha portfolio's
            holding-to-case link (`holding.caseId`) — Case itself carries
            no identity of its own (`atlas/core/domain/case/entity.py`). */}
        {/* Figma-fidelity pass: identity and the Hero narrative now read
            as one unified card, matching the approved design's visual
            flow -- previously two visually separate blocks (a bare
            header, then a bordered Hero card below it). The Action Flow
            trigger stays outside this card, unchanged in behavior, since
            the approved design doesn't fold decision-recording UI into
            this card either. */}
        <Surface tier="primary">
          <Stack gap="metadata">
          <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
            <RouterLink to={returnTo} style={ACCENT_LINK_STYLE}>
              {t(returnLabelKey)}
            </RouterLink>
            {originLabelKey && <Text color="tertiary">{t(originLabelKey)}</Text>}
          </Inline>

          {/* Figma-fidelity pass: company name carries the primary visual
              weight (as the approved design shows), ticker demoted to a
              secondary inline label beside it -- same underlying data,
              same accessible h1, only the visual role swapped. Falls back
              to the ticker as the primary heading when no company name has
              loaded yet, so nothing ever renders as an empty title. */}
          <Inline gap="row" align="baseline" wrap>
            <Heading level={1} style={{ fontWeight: 700 }}>
              {companyProfile?.name
                ? companyProfile.name
                : (resolvedTicker ?? t("investmentCase.header.untitled"))}
            </Heading>
            {companyProfile?.name && resolvedTicker && (
              <Text as="span" color="secondary" style={{ fontSize: "var(--type-size-h4)" }}>
                {resolvedTicker}
              </Text>
            )}
          </Inline>
          {identityLine && (
            <Text as="p" color="tertiary">
              {identityLine}
            </Text>
          )}

          {metadataLineParts.length > 0 && (
            <Text as="p" color="secondary">
              {metadataLineParts.join("   |   ")}
            </Text>
          )}

          {/* Product Sprint 7 (Investment Case Excellence, Deliverable 9
              -- Navigation): the only way off this page used to be the
              single origin-aware back-link above -- no path forward to
              Compare, even though Discovery/Portfolio/Daily Brief all
              already link into Compare for the same ticker
              (`/discovery/compare?a=...`, Sprint 5). Reuses that exact
              existing route and query param; no new navigation concept.
              Product Sprint 10 (Navigation & Workflow Excellence,
              Deliverable 4/5): broadened from `linkedHolding` to
              `resolvedTicker` -- a case for a ticker that isn't (yet) a
              Portfolio holding previously had no Compare link either,
              even when its own analysis already carries a real ticker.
              The same widening also enables the new Add-to-Watchlist
              action right beside it, for the one case that was a real
              isolated island: a ticker Atlas has analyzed but the
              investor has neither watchlisted nor bought. */}
          {resolvedTicker && (
            <Inline gap="row" wrap>
              <RouterLink to={`/discovery/compare?a=${encodeURIComponent(resolvedTicker)}`} style={ACCENT_LINK_STYLE}>
                {t("investmentCase.header.compareLink")}
              </RouterLink>
              {!linkedHolding && !isOnWatchlist && (
                <Button variant="tertiary" onClick={handleAddToWatchlist} disabled={watchlistAddStatus === "submitting"}>
                  {t("watchlist.addForm.submit")}
                </Button>
              )}
            </Inline>
          )}
          {watchlistAddStatus === "error" && (
            <Text color="tertiary" role="alert">
              {t("discovery.card.addFailed")}
            </Text>
          )}

          {/* Internal Alpha Sprint 2 (Real-World Workflow Validation) --
              real-usage finding: `alphaHoldings` defaults to `[]` while
              `alphaPortfolioStatus` is still "loading" (a fast, ~1-2s
              fetch), so `!linkedHolding` was `true` -- and this message
              rendered -- for every Case during that window, including
              ones that genuinely are a real portfolio holding. A
              confirmed-loaded "not linked" is a real fact; a
              still-loading "not linked" is not linked information at
              all -- "unknown remains unknown," never shown as a
              premature negative. */}
          {alphaPortfolioStatus.kind === "loaded" && !linkedHolding && caseId && (
            <Text color="secondary">{t("investmentCase.header.notLinked")}</Text>
          )}
          {!caseId && (
            <Stack gap="metadata">
              <Text color="secondary">{t("investmentCase.noCaseSelected")}</Text>
              {/* Product Sprint 10 (Navigation & Workflow Excellence,
                  Deliverable 1/7): the bare `/investment-case` route
                  (no `:caseId`) is unreachable from any in-app link --
                  it previously rendered this text with no way forward
                  at all except the browser's own Back button. */}
              <RouterLink to="/portfolio" style={ACCENT_LINK_STYLE}>
                {t("investmentCase.noCaseSelected.goToPortfolio")}
              </RouterLink>
            </Stack>
          )}
          {caseId && status.kind === "loading" && (
            <Text role="status" aria-live="polite">
              {t("investmentCase.hero.loading", {
                ticker: resolvedTicker ?? t("investmentCase.header.untitled"),
              })}
            </Text>
          )}
          {caseId && status.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("investmentCase.loadError", { message: status.message })}
            </Text>
          )}

          {/* Product Sprint 7 (Investment Case Excellence, Deliverable
              10 -- Polish) -- `investmentCaseAnalysis` is the single
              most important fetch on this page (it drives the Hero,
              Executive Summary, every canonical section, and two of
              the six tabs), but every one of its consumers only ever
              branched on `.kind === "loaded"`. A still-loading or
              failed analysis fetch previously showed nothing at all --
              a silent blank page -- even after the case summary itself
              (`status`) had already loaded successfully and its own
              loading/error text above had disappeared. This mirrors
              that same text, gated on the fetch that was actually
              missing it. */}
          {caseId && status.kind === "loaded" && investmentCaseAnalysis.kind === "loading" && (
            <Text role="status" aria-live="polite">
              {t("investmentCase.hero.loading", {
                ticker: resolvedTicker ?? t("investmentCase.header.untitled"),
              })}
            </Text>
          )}
          {caseId && status.kind === "loaded" && investmentCaseAnalysis.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("investmentCase.analysisLoadError")}
            </Text>
          )}

          {/* Hero (UX-020, implementing APP-002/APP-003/UX-018/UX-019) --
              the paragraph is now the primary interface: current
              conclusion, why, whether action is required, what could
              change the view. Recommendation, Conviction, and Risk --
              formerly a standalone badge here plus assessment-point
              sentences and a priority chip inside `ExecutiveSummaryCard`
              below -- are now one coherent narrative, with those same
              facts appearing underneath it as a quiet supporting strip,
              never a second, competing rendering of the same fact. */}
          {investmentCaseAnalysis.kind === "loaded" && (() => {
            const report = investmentCaseAnalysis.report;
            const growth = report.businessAnalysis.findings.find((f) => f.kind === "growth");
            const capitalAllocation = report.businessAnalysis.findings.find((f) => f.kind === "capital_allocation");
            const longTerm = report.outlook.longTerm;
            const shortTerm = report.outlook.shortTerm;
            const longTermBull = longTerm.scenarios.find((s) => s.kind === "bull");
            const longTermBear = longTerm.scenarios.find((s) => s.kind === "bear");
            const riskFindings = report.risk.findings.map((f) => ({ category: f.category, status: f.status }));
            const valuationSupportStatus = report.valuationSupport.status as ValuationSupportStatus;
            const valuationSupportGap = report.valuationSupport.gap as ValuationSupportGapKind | null;
            // `UX-022` §3/§6/§9: at most 2 real limiting factors, and
            // whether Valuation Support is load-bearing for the
            // Direction shown -- entry/increase directions (BUY/ADD)
            // where Valuation Support is the supporting pillar, or any
            // direction where it is actively not supported/unresolved
            // (the specific reason a stronger Direction wasn't reached).
            const limitingFactors: LimitingFactor[] = deriveLimitingFactors({
              riskFindings,
              valuationSupportStatus,
              valuationSupportGap,
            });
            const isValuationSupportLoadBearing =
              valuationSupportStatus !== "supported" ||
              report.recommendation.level === "entry_supported" ||
              report.recommendation.level === "increase_supported";
            const heroAnalysis: HeroAnalysisInput = {
              recommendationLevel: report.recommendation.level,
              convictionLevel: report.conviction.level,
              valuationSupportStatus,
              growthStatus: growth ? growth.status : "not_evaluated",
              capitalAllocationStatus: capitalAllocation ? capitalAllocation.status : "not_evaluated",
              valuationStatus: report.valuationContext.fcfYieldStatus,
              riskFindings,
              topStrengthKind: report.strengths[0]?.kind ?? null,
              isBaselineCase: report.isBaselineCase,
              latestChangeCount: report.latestChanges.length,
              currentAnalysisAt: report.currentAnalysisAt,
              longTermExpectedReturn: longTerm.expectedReturn
                ? { lowPercent: longTerm.expectedReturn.lowPercent, highPercent: longTerm.expectedReturn.highPercent }
                : null,
              longTermExpectedReturnGap: longTerm.expectedReturnGap,
              longTermBullReturnPercent: longTermBull ? longTermBull.returnPercent : null,
              longTermBearReturnPercent: longTermBear ? longTermBear.returnPercent : null,
              outlookAlignmentLongTerm: report.recommendation.outlookAlignment.longTerm,
              limitingFactors,
              missingEvaluations: report.recommendation.missingEvaluations,
              sharePrice: report.marketSnapshot ? report.marketSnapshot.sharePrice : null,
              currency: report.marketSnapshot ? report.marketSnapshot.currency : null,
              tradingDay: report.marketSnapshot ? report.marketSnapshot.tradingDay : null,
              priceFreshness: report.marketSnapshot ? report.marketSnapshot.priceFreshness : "unavailable",
              stance: report.stance,
              noProviderDataFound: report.noProviderDataFound ?? false,
              convictionReasonCodes: report.conviction.reasons as ConvictionReasonCode[],
              strengthKinds: report.strengths.map((s) => s.kind) as RecommendationDriverKind[],
              challengeKinds: report.risks.map((r) => r.kind) as RecommendationDriverKind[],
              whatWouldChange: report.recommendation.whatWouldChange,
            };

            /** Atlas UX Phase 7A (Semantic Investment Model, Foundation
             * Sprint) -- the seven-category bar and Case DNA, computed
             * once here from data this IIFE already fetched/derived
             * above (no new fetch, no new analysis) and reused by both
             * the bar and the promoted Case DNA line. `tension` is the
             * identical pure computation `HeroCard` runs internally
             * from the same three inputs -- recomputed here rather than
             * threaded through a prop, the same "cheap and pure, so
             * just call it again" convention this codebase already
             * uses elsewhere for shared derivations. */
            const tension = deriveHeroTension({
              growthStatus: heroAnalysis.growthStatus,
              capitalAllocationStatus: heroAnalysis.capitalAllocationStatus,
              valuationStatus: heroAnalysis.valuationStatus,
            });
            const caseDnaSentence = t(HERO_WHY_KEY[tension]);
            const sevenCategories: SevenCategoriesInput = {
              company: deriveCompanyRating(report.businessAnalysis.findings),
              investment: deriveInvestmentRating(report.recommendation.level),
              portfolio: derivePortfolioRating(
                portfolioFitStatus.kind === "loaded" ? (portfolioFitStatus.assessment?.overall ?? null) : null,
              ),
              evidence: deriveEvidenceRating(report.coverage.overallCoverage, report.coverage.overallConfidence),
              upside: deriveUpside(longTermBull ? longTermBull.returnPercent : null),
              risk: deriveRisk(riskFindings),
              horizon: deriveHorizon(
                longTerm.expectedReturn
                  ? { monthsLow: longTerm.expectedReturn.horizonMonthsLow, monthsHigh: longTerm.expectedReturn.horizonMonthsHigh }
                  : null,
                shortTerm.expectedReturn
                  ? { monthsLow: shortTerm.expectedReturn.horizonMonthsLow, monthsHigh: shortTerm.expectedReturn.horizonMonthsHigh }
                  : null,
              ),
            };

            return (
              <>
                <HeroCard
                  ticker={resolvedTicker ?? t("investmentCase.header.untitled")}
                  analysis={heroAnalysis}
                  outstandingWorkKinds={caseOutstandingWork.map((item) => item.kind)}
                  isThesisStale={report.isThesisStale}
                  // Calibration Phase 2 (Investment Case Coherence
                  // Implementation), Phase 3/C1: `report.openQuestions`
                  // is `decision_engine`'s own evidence-linkage gap list
                  // (a different, disjoint concept from a business-
                  // analysis open question -- see the backend's own
                  // `key_open_questions` docstring). `keyOpenQuestions`
                  // is the one canonical, investor-facing open-question
                  // source -- the same list `InvestmentArgumentSection`
                  // below already renders in full; the Hero now shows
                  // the identical count and the identical top question,
                  // never a second, silently-different answer.
                  openQuestionCount={report.keyOpenQuestions.length}
                  primaryOpenQuestionKey={
                    report.keyOpenQuestions[0] ? OPEN_QUESTION_ORIGIN_KEY[report.keyOpenQuestions[0].origin] : null
                  }
                  t={t}
                  locale={locale}
                  suppressLimitingFactorPreview
                  suppressTensionSentence
                  onRefreshPrice={refreshPrice}
                  isRefreshingPrice={priceRefreshStatus === "refreshing"}
                />
                {report.recommendation.level !== "insufficient_evidence" && isValuationSupportLoadBearing && (
                  <>
                    <Divider tone="hairline" />
                    <ValuationSupportCard status={valuationSupportStatus} gap={valuationSupportGap} t={t} />
                  </>
                )}
                {report.recommendation.level !== "insufficient_evidence" && limitingFactors.length > 0 && (
                  <>
                    <Divider tone="hairline" />
                    <LimitingFactorsCard factors={limitingFactors} t={t} />
                  </>
                )}

                {/* Convergence Sprint 1B (Investment Case Information
                    Architecture) -- Atlas's conclusion now opens the case.

                    Sprint 1 moved this block above Portfolio Fit, which was
                    correct but not sufficient: `InvestmentCaseCanonicalSections`
                    below renders fifteen analytical sections and sat ~700 lines
                    of JSX *above* it, so a reader still met the seven-category
                    bar, Outlook, Investment Argument, Atlas Reasoning, Evidence
                    and six audit panels before learning what Atlas concluded.
                    Executive Summary and `AtlasDecisionSummary` are the page's
                    Level 1 answer; everything below them explains it. */}
            {/* Executive Summary (Investment Case Workspace v2, Sprint 2;
                "Discuss this Case" removed in Workspace Migration Phase 3
                -- Decision Log #2, no embedded Ask Atlas UI) -- the whole
                "understand in ~10 seconds, no scrolling" section: Atlas
                Assessment, Current Priority, Portfolio Impact,
                Outstanding Issues. Renders only once the analysis has
                loaded; a fetch failure or still-loading state never
                blocks the rest of the page (same independent-fetch
                pattern every other section here already uses). */}
            {investmentCaseAnalysis.kind === "loaded" && (
              <ExecutiveSummaryCard
                analysis={investmentCaseAnalysis.report}
                linkedHolding={linkedHolding}
                alphaPortfolioStatus={alphaPortfolioStatus}
                outstandingWorkKinds={caseOutstandingWork.map((item) => item.kind)}
                t={t}
              />
            )}

            <Divider tone="hairline" />

            {/* Convergence Sprint 1 (Investment Case Compression) --
                this block moved here from below Portfolio Fit and the
                Evidence Graph. `AtlasDecisionSummary` is the page's own
                Level 1 answer ("what does Atlas think, and why isn't it
                more certain"); it previously rendered ~40 lines of JSX
                and two full analytical sections below the material it
                exists to summarise, so the reader met Level 3 evidence
                before the conclusion. Nothing inside the block changed:
                the nine Decision Layer sections keep their own collapsed
                disclosure exactly as before. */}
            {/* Information Compression (Productization Sprint P2, Phase
                4 -- Decision-Layer Consolidation). The nine Decision
                Layer sections below (Readiness through Portfolio
                Decision) all independently restate one underlying
                question -- "why isn't Atlas more certain, and what
                would change that" -- each in its own vocabulary.
                `AtlasDecisionSummary` answers it once, from the two
                views built to already hold a single authoritative
                answer (Decision Reliability's own `primaryLimitingReason`,
                Decision Path's own `nextAchievableImprovement`) -- no
                new fetch, no new computation. The nine sections
                themselves are unchanged and un-deleted; they move into
                one collapsed disclosure immediately below, so every
                reason, count, and source tag they show remains exactly
                as reachable as before -- only the default reading path
                changes. */}
            {decisionReliabilityStatus.kind === "loaded" && (
              <AtlasDecisionSummary
                reliability={decisionReliabilityStatus.reliability}
                path={decisionPathStatus.kind === "loaded" ? decisionPathStatus.path : null}
                t={t}
              />
            )}

            <ExpandableDetail summaryLabel={t("investmentCase.decisionSummary.viewFullLabel")}>
              <Stack gap="inter-section">
                {/* Atlas Intelligence Sprint 11 (Decision Readiness &
                    Decision Eligibility, Deliverable 6). Independent fetch
                    (`decisionReadinessStatus`); renders nothing on error,
                    never blocking the rest of the page. */}
                {decisionReadinessStatus.kind === "loaded" && (
                  <DecisionReadinessSection
                    readiness={decisionReadinessStatus.readiness}
                    change={decisionReadinessChange}
                    t={t}
                  />
                )}

                {/* Atlas Decision Layer Sprint 1 (Investment Decision
                    Synthesis, Deliverable 6). Independent fetch
                    (`investmentDecisionStatus`); renders nothing on error,
                    never blocking the rest of the page. */}
                {investmentDecisionStatus.kind === "loaded" && (
                  <InvestmentDecisionSection
                    decision={investmentDecisionStatus.decision}
                    change={investmentDecisionChange}
                    t={t}
                  />
                )}

                {/* Atlas Decision Layer Sprint 2 (Recommendation Strength
                    & Conviction, Deliverable 6). Independent fetch
                    (`recommendationConvictionStatus`); renders nothing on
                    error, never blocking the rest of the page. */}
                {recommendationConvictionStatus.kind === "loaded" && (
                  <RecommendationConvictionSection
                    conviction={recommendationConvictionStatus.conviction}
                    change={recommendationConvictionChange}
                    t={t}
                  />
                )}

                {/* Atlas Decision Layer Sprint 3 (Decision Path &
                    Required Progress, Deliverable 6). Independent fetch
                    (`decisionPathStatus`); renders nothing on error, never
                    blocking the rest of the page. */}
                {decisionPathStatus.kind === "loaded" && (
                  <DecisionPathSection path={decisionPathStatus.path} change={decisionPathChange} t={t} />
                )}

                {/* Atlas Decision Layer Sprint 4 (Decision Alternatives &
                    Opportunity Cost, Deliverable 6). Independent fetch
                    (`opportunityCostStatus`); renders nothing when there
                    are no real alternatives, never blocking the rest of
                    the page. */}
                {opportunityCostStatus.kind === "loaded" && (
                  <OpportunityCostSection
                    opportunityCost={opportunityCostStatus.opportunityCost}
                    currentTicker={resolvedTicker ?? ""}
                    change={opportunityCostChange}
                    t={t}
                  />
                )}

                {/* Atlas Decision Layer Sprint 5 (Decision Memory,
                    Deliverable 6). Independent fetch
                    (`decisionMemoryStatus`); renders nothing on error,
                    never blocking the rest of the page. */}
                {decisionMemoryStatus.kind === "loaded" && <DecisionMemorySection memory={decisionMemoryStatus.memory} t={t} />}

                {/* Atlas Decision Layer Sprint 6 (Decision Explanation &
                    Traceability, Deliverable 6). Independent fetch
                    (`decisionExplanationStatus`); renders nothing on
                    error, never blocking the rest of the page. */}
                {decisionExplanationStatus.kind === "loaded" && (
                  <DecisionExplanationSection explanation={decisionExplanationStatus.explanation} t={t} />
                )}

                {/* Atlas Decision Layer Sprint 7 (Decision Reliability,
                    Deliverable 7). Independent fetch
                    (`decisionReliabilityStatus`); renders nothing on
                    error, never blocking the rest of the page. */}
                {decisionReliabilityStatus.kind === "loaded" && (
                  <DecisionReliabilitySection reliability={decisionReliabilityStatus.reliability} t={t} />
                )}

                {/* Atlas Decision Layer Sprint 8 (Portfolio Decision
                    Synthesis, Deliverable 7). Independent fetch
                    (`portfolioDecisionStatus`); renders nothing on error,
                    never blocking the rest of the page. */}
                {portfolioDecisionStatus.kind === "loaded" && (
                  <PortfolioDecisionSection decision={portfolioDecisionStatus.decision} t={t} />
                )}
              </Stack>
            </ExpandableDetail>

                {/* Atlas UX Phase 7A -- the seven-category bar and Case
                    DNA lead the page, immediately after the Hero and
                    its own supporting cards, per this sprint's own
                    "Hero -> Seven Categories -> Case DNA -> ..."
                    layout. */}
                <Divider tone="hairline" />
                <SevenCategoriesSection ratings={sevenCategories} t={t} />
                <CaseDnaLine sentence={caseDnaSentence} t={t} />

                {/* Outlook -> Investment Argument -> Atlas Reasoning ->
                    Evidence -> everything else, in that order (reordered
                    inside `InvestmentCaseCanonicalSections` itself) --
                    moved up from its previous position after Executive
                    Summary/the decision-recording action panel so it
                    sits directly under Case DNA, matching this sprint's
                    layout exactly. "Strengths"/"Concerns" are not a
                    separate pair of sections: `InvestmentArgumentSection`
                    already renders them together (as "Supports the
                    Case"/"Challenges the Case") alongside Open
                    Questions, and duplicating that content in a second,
                    separate Strengths/Concerns block would violate this
                    codebase's own "never repeat the same reason twice"
                    discipline -- a disclosed, deliberate reading of the
                    spec's own ordering, not a silent omission. */}
                <InvestmentCaseCanonicalSections
                  analysis={report}
                  linkedHolding={linkedHolding}
                  alphaPortfolioStatus={alphaPortfolioStatus}
                  onViewMoreDetails={() => setActiveTab("moreDetails")}
                  t={t}
                  locale={locale}
                />
              </>
            );
          })()}
        </Stack>
        </Surface>

        {/* Action Flow Tier 1 trigger (approved §13 Option A) -- the
            investor's own, clearly-separate action vocabulary, distinct
            from Atlas's sentence in the card above. `[ Record a decision
            ]` is the only entry point; the nudge reuses
            `caseOutstandingWork`'s already-computed count (same data
            Outstanding Work renders in full further down the page, in
            progressive disclosure) rather than a new computation. Kept
            outside the identity/Hero card (Figma-fidelity pass) -- the
            approved design doesn't fold decision-recording UI into that
            card either. Hidden once the panel below is open, so the
            trigger and the open panel are never both visible at once. */}
        <Stack gap="metadata">
          {caseId && status.kind === "loaded" && !isDecisionPanelExpanded && (
            <>
              <Divider tone="hairline" />
              {/* Internal Alpha Sprint 2 (Real-World Workflow
                  Validation) -- real-usage finding: this branch and its
                  `linkedHolding && (...)` sibling below both keyed
                  purely off `linkedHolding`, which defaults to `null`
                  while `alphaPortfolioStatus` is still "loading." A real
                  holding's own Case briefly showed this not-linked
                  branch (import-portfolio note + Start Decision) instead
                  of the real "Record a decision" trigger, for the same
                  ~1-2s window Finding 1 covers above -- confirmed live
                  by instrumenting `linkedHolding` across renders: `null`
                  for many renders, then the real, matching holding. */}
              {alphaPortfolioStatus.kind === "loaded" && !linkedHolding && (
                // Product Sprint 11 (Investment Workflow Excellence,
                // Deliverable 2/8): this note previously named a real
                // requirement ("linked to a portfolio holding") with no
                // way to act on it -- a decision entry point that looked
                // hidden rather than simply not-yet-applicable. Atlas has
                // no in-context "buy this new ticker" flow (a Core/
                // ontology change, out of this sprint's scope) -- the
                // real mechanism is re-importing the portfolio once a
                // trade has actually been made, so this now names that
                // path explicitly, reusing the exact same route/label
                // Portfolio's own empty state already uses.
                <Stack gap="metadata">
                  <Text color="secondary">{t("investmentCase.actions.notLinkedNote")}</Text>
                  <RouterLink to="/portfolio/import" style={ACCENT_LINK_STYLE}>
                    {t("portfolio.empty.importButton")}
                  </RouterLink>
                  {/* Product Sprint 12 (Decision Workflow Consolidation,
                      Deliverable 2/3 -- One Decision Workflow / Start
                      Decision): the real, working alternative to the
                      quick-action panel above (which requires an
                      existing holding) -- recording an actual decision
                      on a brand-new candidate via the existing,
                      previously-unreachable Decision Draft system.

                      Convergence Sprint 1: moved behind a disclosure
                      rather than rendered inline. The form asks the
                      investor for a BUY/WATCH/PASS choice, a required
                      free-text thesis and a 0-100 confidence value --
                      Level 1 *input* standing between the reader and
                      Atlas's own Level 1 conclusion, which is the
                      opposite of this page's job. Nothing about it
                      changed: same component, same `caseId`/`ticker`,
                      same Decision Draft calls, same persistence.
                      `Decision.reason` still feeds Decision Memory's
                      thesis history (`DE-005` section 1) and
                      `Decision.confidence` still feeds investor pattern
                      recognition, so neither field is removed or
                      reinterpreted here -- the terminal-action model is
                      explicitly out of this sprint's scope. */}
                  {caseId && (
                    <ExpandableDetail summaryLabel={t("investmentCase.actions.recordManuallyLabel")}>
                      <StartDecisionSection caseId={caseId} ticker={resolvedTicker} />
                    </ExpandableDetail>
                  )}
                </Stack>
              )}
              {linkedHolding && (
                <Inline gap="row" align="center">
                  <Button variant="primary" onClick={() => setIsDecisionPanelExpanded(true)}>
                    {t("investmentCase.actions.recordDecisionTrigger")}
                  </Button>
                  {decisionsAwaitingOutcome.length > 0 && (
                    <Button
                      variant="tertiary"
                      onClick={() => {
                        // Only an "outcome-missing" item names a real Decision id
                        // (`outcome-missing:${decisionId}`) that the report-outcome
                        // form below can act on -- "trade-missing" items name an
                        // Outcome id instead, which is not a valid `decisionId` and
                        // would make `POST /outcomes` fail. When the case's only
                        // outstanding item is trade-missing (an Outcome already
                        // exists; only its trade hasn't been reported), there is no
                        // real form for that yet, so this falls back to the
                        // original "record a new decision" panel rather than
                        // opening a form that cannot succeed.
                        const outcomeMissingItem = decisionsAwaitingOutcome.find(
                          (item) => item.kind === "outcome-missing",
                        );
                        const firstDecisionId = outcomeMissingItem?.id.replace(
                          "outcome-missing:",
                          "",
                        );
                        if (firstDecisionId) {
                          setReportingExistingDecisionId(firstDecisionId);
                        }
                        setIsDecisionPanelExpanded(true);
                      }}
                    >
                      {t(
                        decisionsAwaitingOutcome.length === 1
                          ? "investmentCase.actions.outcomeAwaitingNudgeOne"
                          : "investmentCase.actions.outcomeAwaitingNudgeOther",
                        { count: decisionsAwaitingOutcome.length },
                      )}
                    </Button>
                  )}
                </Inline>
              )}
            </>
          )}
        </Stack>

        {/* Action Flow Tier 2 (approved §13 Option A) -- an inline
            expandable panel directly beneath the header, the same
            interaction pattern Portfolio's own single-row Reconcile
            form already established (Workspace Migration Phase 2),
            rather than a new pattern. Every field, handler, and
            validation rule below is unchanged from the flow's former
            always-visible, bottom-of-page location -- only the
            container and its default-collapsed visibility moved. */}
        {caseId && status.kind === "loaded" && linkedHolding && isDecisionPanelExpanded && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <div ref={decisionPanelHeadingRef} tabIndex={-1}>
                <Heading level={2}>
                  {reportingExistingDecisionId
                    ? t("investmentCase.actions.reportTransaction")
                    : t("investmentCase.actions.heading")}
                </Heading>
              </div>

              {caseLevelDecisionStatus.kind === "idle" && !reportingExistingDecisionId && (
                <div>
                  <Button variant="primary" onClick={() => openAction("ADD")}>
                    {t("investmentCase.actions.addToPosition")}
                  </Button>{" "}
                  <Button variant="tertiary" onClick={() => openAction("TRIM")}>
                    {t("investmentCase.actions.trimPosition")}
                  </Button>{" "}
                  <Button variant="tertiary" onClick={() => openAction("REMOVE")}>
                    {t("investmentCase.actions.removePosition")}
                  </Button>{" "}
                  <Button variant="tertiary" onClick={() => openAction("LEAVE_AS_IS")}>
                    {t("investmentCase.actions.leaveAsIs")}
                  </Button>{" "}
                  <Button variant="tertiary" onClick={closeAction}>
                    {t("common.cancel")}
                  </Button>
                </div>
              )}

              {pendingAction &&
                (caseLevelDecisionStatus.kind === "creating" ||
                  caseLevelDecisionStatus.kind === "submitting" ||
                  caseLevelDecisionStatus.kind === "validation-error" ||
                  caseLevelDecisionStatus.kind === "api-error") && (
                  <Stack gap="inter-section">
                    <Heading level={3}>{t(ACTION_LABEL_KEY[pendingAction])}</Heading>
                    <Text as="label">
                      {t("investmentCase.actions.reasonLabel")}
                      <br />
                      <textarea
                        value={caseLevelDecisionForm.reason}
                        onChange={(event) =>
                          setDecisionForm((current) => ({
                            ...current,
                            [CASE_LEVEL_DECISION_KEY]: {
                              ...caseLevelDecisionForm,
                              reason: event.target.value,
                            },
                          }))
                        }
                        disabled={caseLevelDecisionStatus.kind === "submitting"}
                      />
                    </Text>
                    <Text as="label">
                      {t("investmentCase.actions.confidenceLabel")}
                      <br />
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={caseLevelDecisionForm.confidence}
                        onChange={(event) =>
                          setDecisionForm((current) => ({
                            ...current,
                            [CASE_LEVEL_DECISION_KEY]: {
                              ...caseLevelDecisionForm,
                              confidence: event.target.value,
                            },
                          }))
                        }
                        disabled={caseLevelDecisionStatus.kind === "submitting"}
                      />
                    </Text>

                    {caseLevelDecisionStatus.kind === "validation-error" && (
                      <Text color="tertiary" role="alert">
                        {caseLevelDecisionStatus.message}
                      </Text>
                    )}
                    {caseLevelDecisionStatus.kind === "api-error" && (
                      <Text color="tertiary" role="alert">
                        {t("investmentCase.actions.recordError", {
                          message: caseLevelDecisionStatus.message,
                        })}
                      </Text>
                    )}

                    <div>
                      <Button
                        variant="primary"
                        onClick={() => submitDecision(CASE_LEVEL_DECISION_KEY)}
                        disabled={caseLevelDecisionStatus.kind === "submitting"}
                      >
                        {caseLevelDecisionStatus.kind === "submitting"
                          ? t("common.submitting")
                          : t("investmentCase.actions.submit")}
                      </Button>{" "}
                      <Button
                        variant="tertiary"
                        onClick={closeAction}
                        disabled={caseLevelDecisionStatus.kind === "submitting"}
                      >
                        {t("common.cancel")}
                      </Button>
                    </div>
                  </Stack>
                )}

              {(caseLevelDecisionStatus.kind === "success" || reportingExistingDecisionId) && (
                <Stack gap="inter-section">
                  {caseLevelDecisionStatus.kind === "success" && (
                    <Text>
                      {t("investmentCase.decision.recorded", {
                        decisionType: DECISION_TYPE_KEY[
                          caseLevelDecisionStatus.decision.decisionType
                        ]
                          ? t(DECISION_TYPE_KEY[caseLevelDecisionStatus.decision.decisionType]!)
                          : caseLevelDecisionStatus.decision.decisionType,
                        subject: caseLevelDecisionStatus.decision.subject,
                      })}
                    </Text>
                  )}

                  {caseLevelDecisionStatus.kind === "success" && pendingAction === "LEAVE_AS_IS" && (
                    <Text color="secondary">
                      {t("investmentCase.actions.leaveAsIsRecordedNote")}
                    </Text>
                  )}

                  {pendingAction !== "LEAVE_AS_IS" && reportDecisionId && (
                    <>
                      <Text color="secondary">
                        {t("investmentCase.actions.decisionRecordedNote")}
                      </Text>

                      {reportOutcomeStatus.kind === "idle" && (
                        <div>
                          <Button
                            variant="tertiary"
                            onClick={() =>
                              setOutcomeCreateStatus((current) => ({
                                ...current,
                                [reportDecisionId]: { kind: "creating" },
                              }))
                            }
                          >
                            {t("investmentCase.actions.reportTransaction")}
                          </Button>
                        </div>
                      )}

                      {(reportOutcomeStatus.kind === "creating" ||
                        reportOutcomeStatus.kind === "submitting" ||
                        reportOutcomeStatus.kind === "validation-error" ||
                        reportOutcomeStatus.kind === "api-error") && (
                        <Stack gap="inter-section">
                          <Text as="label">
                            {t("investmentCase.outcome.statementLabel")}
                            <br />
                            <textarea
                              value={reportOutcomeForm.statement}
                              onChange={(event) =>
                                setOutcomeForm((current) => ({
                                  ...current,
                                  [reportDecisionId]: {
                                    ...reportOutcomeForm,
                                    statement: event.target.value,
                                  },
                                }))
                              }
                              disabled={reportOutcomeStatus.kind === "submitting"}
                            />
                          </Text>
                          <Text as="label">
                            {t("investmentCase.outcome.noteLabel")}
                            <br />
                            <textarea
                              value={reportOutcomeForm.note}
                              onChange={(event) =>
                                setOutcomeForm((current) => ({
                                  ...current,
                                  [reportDecisionId]: {
                                    ...reportOutcomeForm,
                                    note: event.target.value,
                                  },
                                }))
                              }
                              disabled={reportOutcomeStatus.kind === "submitting"}
                            />
                          </Text>

                          <Text as="label">
                            <input
                              type="checkbox"
                              checked={reportOutcomeForm.isExternalTrade}
                              onChange={(event) =>
                                setOutcomeForm((current) => ({
                                  ...current,
                                  [reportDecisionId]: {
                                    ...reportOutcomeForm,
                                    isExternalTrade: event.target.checked,
                                  },
                                }))
                              }
                              disabled={reportOutcomeStatus.kind === "submitting"}
                            />{" "}
                            {t("investmentCase.outcome.externalTradeCheckbox")}
                          </Text>

                          {reportOutcomeForm.isExternalTrade && (
                            <Stack gap="inter-section">
                              <Text as="label">
                                {t("investmentCase.outcome.securityLabel")}
                                <br />
                                <input
                                  value={reportOutcomeForm.security}
                                  onChange={(event) =>
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [reportDecisionId]: {
                                        ...reportOutcomeForm,
                                        security: event.target.value,
                                      },
                                    }))
                                  }
                                  disabled={reportOutcomeStatus.kind === "submitting"}
                                />
                              </Text>
                              <Text as="label">
                                {t("investmentCase.outcome.typeLabel")}
                                <br />
                                <select
                                  value={reportOutcomeForm.transactionType}
                                  onChange={(event) =>
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [reportDecisionId]: {
                                        ...reportOutcomeForm,
                                        transactionType: event.target.value as
                                          | "BUY"
                                          | "SELL"
                                          | "ADD"
                                          | "EXIT",
                                      },
                                    }))
                                  }
                                  disabled={reportOutcomeStatus.kind === "submitting"}
                                >
                                  <option value="BUY">
                                    {t("investmentCase.decision.typeBuy")}
                                  </option>
                                  <option value="ADD">
                                    {t("investmentCase.outcome.transactionTypeAdd")}
                                  </option>
                                  <option value="SELL">
                                    {t("investmentCase.decision.typeSell")}
                                  </option>
                                  <option value="EXIT">
                                    {t("investmentCase.outcome.transactionTypeExit")}
                                  </option>
                                </select>
                              </Text>
                              <Text as="label">
                                {t("investmentCase.outcome.quantityLabel")}
                                <br />
                                <input
                                  value={reportOutcomeForm.quantity}
                                  onChange={(event) =>
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [reportDecisionId]: {
                                        ...reportOutcomeForm,
                                        quantity: event.target.value,
                                      },
                                    }))
                                  }
                                  disabled={reportOutcomeStatus.kind === "submitting"}
                                />
                              </Text>
                              <Text as="label">
                                {t("investmentCase.outcome.executionPriceLabel")}
                                <br />
                                <input
                                  value={reportOutcomeForm.executionPrice}
                                  onChange={(event) =>
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [reportDecisionId]: {
                                        ...reportOutcomeForm,
                                        executionPrice: event.target.value,
                                      },
                                    }))
                                  }
                                  disabled={reportOutcomeStatus.kind === "submitting"}
                                />
                              </Text>
                              <Text as="label">
                                {t("investmentCase.outcome.feesLabel")}
                                <br />
                                <input
                                  value={reportOutcomeForm.fees}
                                  onChange={(event) =>
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [reportDecisionId]: {
                                        ...reportOutcomeForm,
                                        fees: event.target.value,
                                      },
                                    }))
                                  }
                                  disabled={reportOutcomeStatus.kind === "submitting"}
                                />
                              </Text>
                              <Text as="label">
                                {t("investmentCase.outcome.executedAtLabel")}
                                <br />
                                <input
                                  type="datetime-local"
                                  value={reportOutcomeForm.executedAt}
                                  onChange={(event) =>
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [reportDecisionId]: {
                                        ...reportOutcomeForm,
                                        executedAt: event.target.value
                                          ? new Date(event.target.value).toISOString()
                                          : "",
                                      },
                                    }))
                                  }
                                  disabled={reportOutcomeStatus.kind === "submitting"}
                                />
                              </Text>
                            </Stack>
                          )}

                          {reportOutcomeStatus.kind === "validation-error" && (
                            <Text color="tertiary" role="alert">
                              {reportOutcomeStatus.message}
                            </Text>
                          )}
                          {reportOutcomeStatus.kind === "api-error" && (
                            <Text color="tertiary" role="alert">
                              {t("investmentCase.outcome.recordError", {
                                message: reportOutcomeStatus.message,
                              })}
                            </Text>
                          )}

                          <div>
                            <Button
                              variant="primary"
                              onClick={() => submitOutcome(reportDecisionId)}
                              disabled={
                                reportOutcomeStatus.kind === "submitting" ||
                                !reportOutcomeForm.decisionId
                              }
                            >
                              {reportOutcomeStatus.kind === "submitting"
                                ? t("common.submitting")
                                : t("common.submit")}
                            </Button>{" "}
                            <Button
                              variant="tertiary"
                              onClick={() =>
                                setOutcomeCreateStatus((current) => ({
                                  ...current,
                                  [reportDecisionId]: { kind: "idle" },
                                }))
                              }
                              disabled={reportOutcomeStatus.kind === "submitting"}
                            >
                              {t("common.cancel")}
                            </Button>
                          </div>
                        </Stack>
                      )}

                      {reportOutcomeStatus.kind === "success" && (
                        <Stack gap="inter-section">
                          <Text>
                            {t("investmentCase.outcome.recorded", {
                              statement: reportOutcomeStatus.outcome.statement,
                            })}
                          </Text>
                          {reportTradeApplyStatus.kind === "applying" && (
                            <Text role="status" aria-live="polite">
                              {t("investmentCase.outcome.updatingPortfolio")}
                            </Text>
                          )}
                          {reportTradeApplyStatus.kind === "updated" && (
                            <Text color="secondary">
                              {t("investmentCase.outcome.updatedAutomatically")}
                            </Text>
                          )}
                          {reportTradeApplyStatus.kind === "awaiting-reconciliation" && (
                            <Text color="tertiary">
                              {t("investmentCase.outcome.awaitingReconciliation")}
                            </Text>
                          )}
                          {reportTradeApplyStatus.kind === "error" && (
                            <Text color="tertiary" role="alert">
                              {t("investmentCase.outcome.applyTradeError", {
                                message: reportTradeApplyStatus.message,
                              })}
                            </Text>
                          )}
                        </Stack>
                      )}
                    </>
                  )}

                  <div>
                    {reportOutcomeStatus.kind === "success" && (
                      <>
                        <RouterLink to="/history" style={ACCENT_LINK_STYLE}>
                          {t("investmentCase.actions.openHistory")}
                        </RouterLink>{" "}
                      </>
                    )}
                    <RouterLink to={returnTo} style={ACCENT_LINK_STYLE}>
                      {t(returnLabelKey)}
                    </RouterLink>{" "}
                    <Button variant="tertiary" onClick={closeAction}>
                      {t("investmentCase.actions.close")}
                    </Button>
                  </div>
                </Stack>
              )}
            </Stack>
          </Surface>
        )}

        {caseId && status.kind === "loaded" && (
          <>

            {/* Product Sprint 4 (Portfolio Fit Engine, Deliverable 8) --
                a new, always-visible section, the same placement tier as
                Business/Valuation/Risk/Evidence above (not hidden behind
                a tab click, matching Portfolio Fit's own stated product
                priority). Independent fetch (`portfolioFitStatus`); a
                still-loading or failed fetch never blocks the rest of
                the page, the same pattern every section on this page
                already follows. */}
            {portfolioFitStatus.kind === "loaded" && <PortfolioFitSection assessment={portfolioFitStatus.assessment} />}
            {portfolioFitStatus.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("portfolioFit.section.loading")}
              </Text>
            )}
            {portfolioFitStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("portfolioFit.section.unavailable")}
              </Text>
            )}

            {/* Atlas Intelligence Sprint 10 (Evidence Graph &
                Dependency Understanding, Deliverable 6). Independent
                fetch (`evidenceGraphStatus`); renders nothing at all
                on error or when the graph is genuinely empty -- never
                a placeholder, never blocking the rest of the page. */}
            {evidenceGraphStatus.kind === "loaded" && <EvidenceGraphSection graph={evidenceGraphStatus.graph} t={t} />}


            <Divider tone="hairline" />

            {/* Figma-fidelity rebuild -- the approved screen's own
                bottom tab bar, replacing the previous single <details>
                "More details" catch-all: the approved screen shows six
                distinct labels (Decision History / Timeline / Last
                Activity / Outstanding Work / Outcomes / More Details),
                never one combined disclosure. Every tab's content below
                is unchanged from its former always-rendered-when-open
                location -- only the container and default tab moved. */}
            <Inline gap="inter-section" wrap role="tablist">
              {(
                [
                  ["decisionHistory", "investmentCase.analysis.decisionHistory.heading"],
                  ["timeline", "investmentCase.timeline.heading"],
                  ["lastActivity", "investmentCase.lastActivity.heading"],
                  ["outstandingWork", "investmentCase.outstandingWork.heading"],
                  ["outcomes", "investmentCase.analysis.outcomes.heading"],
                  ["moreDetails", "investmentCase.moreDetails.heading"],
                ] as [InvestmentCaseTabKey, TranslationKey][]
              ).map(([key, labelKey]) => (
                <TabLabel
                  key={key}
                  active={activeTab === key}
                  onClick={() => setActiveTab(key)}
                  id={`investment-case-tab-${key}`}
                  controls={`investment-case-tabpanel-${key}`}
                >
                  {t(labelKey)}
                </TabLabel>
              ))}
            </Inline>

            {/* Decision History (Phase 26) -- kept mostly unchanged, per
                this sprint's own instruction; moved from its former
                always-visible position (`InvestmentCaseCanonicalSections`)
                into its own tab, matching the approved screen's own tab
                bar. */}
            {activeTab === "decisionHistory" && investmentCaseAnalysis.kind === "loaded" && (
              <Stack
                gap="row"
                role="tabpanel"
                id="investment-case-tabpanel-decisionHistory"
                aria-labelledby="investment-case-tab-decisionHistory"
              >
                <Label>{t("investmentCase.analysis.decisionHistory.heading")}</Label>
                {investmentCaseAnalysis.report.decisionHistory.length === 0 && (
                  <StatusText label={t("investmentCase.analysis.decisionHistory.empty")} />
                )}
                {investmentCaseAnalysis.report.decisionHistory.map((entry) => (
                  <Stack key={entry.decisionId} gap="metadata">
                    <Text as="p">
                      {DECISION_TYPE_KEY[entry.decisionType]
                        ? t(DECISION_TYPE_KEY[entry.decisionType]!)
                        : entry.decisionType}
                      {" — "}
                      {entry.reason}
                    </Text>
                    <Text color="tertiary" as="p">
                      {formatRelativeTime(entry.decidedAt, t)}
                    </Text>
                    {/* Product Sprint 10 (Navigation & Workflow Excellence,
                        Deliverable 1/4): the real Reasoning Workspace for
                        this exact Decision (Assumptions, Case Conditions,
                        the Reasoning Timeline) previously had no link
                        anywhere in the app -- reachable only by typing
                        the URL directly. */}
                    <RouterLink to={`/decisions/${entry.decisionId}/workspace`} style={ACCENT_LINK_STYLE}>
                      {t("investmentCase.analysis.decisionHistory.openReasoningWorkspace")}
                    </RouterLink>
                    <Divider tone="hairline" />
                  </Stack>
                ))}
              </Stack>
            )}

            {/* Outcomes (Phase 27) -- kept mostly unchanged, per this
                sprint's own instruction; moved into its own tab. */}
            {activeTab === "outcomes" && investmentCaseAnalysis.kind === "loaded" && (
              <Stack
                gap="row"
                role="tabpanel"
                id="investment-case-tabpanel-outcomes"
                aria-labelledby="investment-case-tab-outcomes"
              >
                <Label>{t("investmentCase.analysis.outcomes.heading")}</Label>
                {investmentCaseAnalysis.report.outcomeHistory.length === 0 && (
                  <StatusText label={t("investmentCase.analysis.outcomes.empty")} />
                )}
                {investmentCaseAnalysis.report.outcomeHistory.map((entry) => (
                  <Stack key={entry.outcomeId} gap="metadata">
                    <Text as="p">{entry.statement}</Text>
                    <Text color="tertiary" as="p">
                      {entry.occurredAt}
                    </Text>
                    <Divider tone="hairline" />
                  </Stack>
                ))}
              </Stack>
            )}

            {/* Last activity (Sprint 4) — factual continuity only: the
                most recent Decision, Outcome, and Trade this Case has,
                each with a relative-time phrase computed from its own
                real timestamp, plus the linked holding's current
                reconciliation status. No AI interpretation, no
                recommendation — see `deriveActivity`. */}
            {activeTab === "lastActivity" && (
              <Stack
                gap="metadata"
                role="tabpanel"
                id="investment-case-tabpanel-lastActivity"
                aria-labelledby="investment-case-tab-lastActivity"
              >
                <Label>{t("investmentCase.lastActivity.heading")}</Label>
                {!lastDecisionEvent && !lastOutcomeEvent && !lastTradeEvent && (
                  <StatusText label={t("investmentCase.lastActivity.noneYet")} />
                )}
                  {lastDecisionEvent && (
                    <Text>
                      {t("investmentCase.lastActivity.lastDecision", {
                        type:
                          lastDecisionEvent.decisionType &&
                          DECISION_TYPE_KEY[lastDecisionEvent.decisionType]
                            ? t(DECISION_TYPE_KEY[lastDecisionEvent.decisionType]!)
                            : (lastDecisionEvent.decisionType ?? ""),
                        relativeTime: formatRelativeTime(lastDecisionEvent.date, t),
                      })}
                    </Text>
                  )}
                  {lastOutcomeEvent && (
                    <Text>
                      {t("investmentCase.lastActivity.lastOutcome", {
                        relativeTime: formatRelativeTime(lastOutcomeEvent.date, t),
                      })}
                    </Text>
                  )}
                  {lastTradeEvent && (
                    <Text>
                      {t("investmentCase.lastActivity.lastTrade", {
                        type:
                          lastTradeEvent.decisionType && DECISION_TYPE_KEY[lastTradeEvent.decisionType]
                            ? t(DECISION_TYPE_KEY[lastTradeEvent.decisionType]!)
                            : (lastTradeEvent.decisionType ?? ""),
                        detail: lastTradeEvent.summary,
                        relativeTime: formatRelativeTime(lastTradeEvent.date, t),
                      })}
                    </Text>
                  )}
                  {linkedHolding && linkedHolding.reconciliationStatus !== "NONE" && (
                    <Text color={linkedHolding.reconciliationStatus === "AWAITING_RECONCILIATION" ? "tertiary" : "secondary"}>
                      {linkedHolding.reconciliationStatus === "AWAITING_RECONCILIATION"
                        ? t("investmentCase.lastActivity.reconciliationNeeded")
                        : t("investmentCase.lastActivity.reconciliationOk")}
                    </Text>
                  )}
              </Stack>
            )}

            {/* Decision Timeline (Sprint 4) — a simple, entirely
                chronological presentation of this Case's own
                Decision/Outcome/Trade events (`deriveActivity`, oldest
                first, no advanced visualization), ending with the
                current status already computed above
                (`assessmentStatusKey`). What Changed (Investment Case
                Change Intelligence) joins this tab -- Figma's own
                screen shows neither a standalone "What Changed" section
                nor a Timeline section on the primary view; both are
                real, chronological, change-over-time content, so they
                share this one tab rather than either being fabricated
                a Figma slot or silently dropped. */}
            {activeTab === "timeline" && (
              <Stack
                gap="row"
                role="tabpanel"
                id="investment-case-tabpanel-timeline"
                aria-labelledby="investment-case-tab-timeline"
              >
                <Label>{t("investmentCase.timeline.heading")}</Label>
                {caseTimeline.length === 0 && (
                  <StatusText label={t("investmentCase.timeline.empty")} />
                )}
                {caseTimeline.map((event) => (
                  <Stack key={event.id} gap="metadata">
                    <Text>
                      {t(
                        event.kind === "decision"
                          ? "history.row.kindDecision"
                          : event.kind === "outcome"
                            ? "history.row.kindOutcome"
                            : "history.row.kindTrade",
                      )}
                    </Text>
                    <Text color="secondary" as="p">
                      {event.decisionType &&
                        (DECISION_TYPE_KEY[event.decisionType]
                          ? t(DECISION_TYPE_KEY[event.decisionType]!)
                          : event.decisionType)}
                      {" — "}
                      {event.summary}
                    </Text>
                    <Text color="tertiary" as="p">
                      {event.date}
                    </Text>
                  </Stack>
                ))}
                {caseTimeline.length > 0 && (
                  <Text as="p">
                    <Text as="span" color="secondary">
                      {t("investmentCase.timeline.currentStatus")}:{" "}
                    </Text>
                    {t(assessmentStatusKey)}
                  </Text>
                )}
                {investmentCaseAnalysis.kind === "loaded" && (
                  <>
                    <Divider tone="hairline" />
                    <WhatChangedSection
                      changeIntelligenceAvailable={investmentCaseAnalysis.report.changeIntelligenceAvailable}
                      isBaselineCase={investmentCaseAnalysis.report.isBaselineCase}
                      latestChanges={investmentCaseAnalysis.report.latestChanges}
                      thesisChange={investmentCaseAnalysis.report.thesisChange}
                      factsForDimension={(dimension) => {
                        const report = investmentCaseAnalysis.report;
                        const business = report.businessAnalysis.findings.find((f) => f.kind === dimension);
                        if (business) {
                          return { supporting: business.supportingEvidence, contradicting: business.contradictingEvidence };
                        }
                        const risk = report.risk.findings.find((f) => f.category === dimension);
                        if (risk) {
                          return { supporting: risk.supportingFacts, contradicting: risk.contradictingFacts };
                        }
                        const valuation = report.valuation.findings.find((f) => f.kind === dimension);
                        if (valuation) {
                          return { supporting: valuation.supportingFacts, contradicting: valuation.contradictingFacts };
                        }
                        return { supporting: [], contradicting: [] };
                      }}
                      t={t}
                    />
                  </>
                )}
              </Stack>
            )}

            {/* Outstanding work (Sprint 4) — deterministic state checks
                only (`deriveOutstandingWork`): no scoring, no AI, no
                recommendation. Reconciliation is already covered by the
                Last Activity tab, so only the two Decision/Outcome-
                chain checks are shown here to avoid repeating the same
                fact twice. */}
            {activeTab === "outstandingWork" && (
              <Stack
                gap="metadata"
                role="tabpanel"
                id="investment-case-tabpanel-outstandingWork"
                aria-labelledby="investment-case-tab-outstandingWork"
              >
                <Label>{t("investmentCase.outstandingWork.heading")}</Label>
                {caseOutstandingWork.filter((item) => item.kind !== "reconciliation-needed").length ===
                  0 && <StatusText label={t("investmentCase.outstandingWork.none")} />}
                {caseOutstandingWork
                  .filter((item) => item.kind !== "reconciliation-needed")
                  .map((item) => (
                    <Text key={item.id} color="tertiary">
                      {t(
                        item.kind === "outcome-missing"
                          ? "investmentCase.outstandingWork.outcomeMissing"
                          : "investmentCase.outstandingWork.tradeMissing",
                      )}
                    </Text>
                  ))}
              </Stack>
            )}

            {/* More details — every existing Observation/Evidence/
                Knowledge Reference/Reasoning Trace/Judgment record
                remains fully accessible for Alpha inspection and
                debugging, exactly as before -- now behind its own tab
                instead of a `<details>` disclosure, matching the
                approved screen's own tab bar. Also holds every real,
                evidence-traceable analysis the approved screen's
                primary view doesn't have a slot for: the former Atlas
                View narrative content, the full four-category Risk
                vector, the detailed FCF Yield valuation finding, and
                Business Analysis's own Portfolio Context subsection --
                none of it fabricated or unsupported, just real depth
                one tab away rather than deleted (Figma's own "View full
                analysis →" / "View full valuation →" links on the
                primary view imply exactly this kind of deeper tab). */}
            {activeTab === "moreDetails" && (
                <Stack
                  gap="intra-section"
                  role="tabpanel"
                  id="investment-case-tabpanel-moreDetails"
                  aria-labelledby="investment-case-tab-moreDetails"
                >
                  <Text color="secondary">{t("investmentCase.moreDetails.subheading")}</Text>

                  {investmentCaseAnalysis.kind === "loaded" && (
                    <>
                      <CaseNarrativeDetailSection analysis={investmentCaseAnalysis.report} t={t} />
                      <Divider tone="hairline" />
                      <RiskSection analysis={investmentCaseAnalysis.report} t={t} />
                      <Divider tone="hairline" />
                      <ValuationDetailSection analysis={investmentCaseAnalysis.report} t={t} />
                      {linkedHolding && (
                        <>
                          <Divider tone="hairline" />
                          <PortfolioContextDetail
                            linkedHolding={linkedHolding}
                            alphaPortfolioStatus={alphaPortfolioStatus}
                            t={t}
                          />
                        </>
                      )}
                      <Divider tone="hairline" />
                      <EvidenceDetailSection analysis={investmentCaseAnalysis.report} t={t} />
                    </>
                  )}

                  <Divider tone="hairline" />

                  {/* Calibration Phase 2 (Investment Case Coherence
                      Implementation), Phase 9: the Observations record
                      -- and, nested under each one, the full Evidence/
                      Knowledge Reference/Reasoning Trace/Judgment/
                      Decision/Outcome CRUD console -- is real engine-
                      inspection tooling, not investor-facing analysis.
                      Nothing is removed (every real record and form
                      here still works exactly as before); it now sits
                      behind its own explicit, collapsed-by-default
                      disclosure, distinct from the legitimate
                      investor-facing detail above it in this same tab,
                      so it is reached only intentionally. */}
                  {caseId && (
            <ExpandableDetail summaryLabel={t("investmentCase.observations.technicalTransparencyLabel")}>
              <Stack gap="inter-section">
                <Heading level={3}>{t("investmentCase.observations.heading")}</Heading>

                {listStatus.kind === "loading" && (
                  <Text role="status" aria-live="polite">
                    {t("investmentCase.observations.loading")}
                  </Text>
                )}
                {listStatus.kind === "error" && (
                  <Text color="tertiary" role="alert">
                    {t("investmentCase.observations.loadError", { message: listStatus.message })}
                  </Text>
                )}
                {listStatus.kind === "ready" && observations.length === 0 && (
                  <Text color="secondary">{t("investmentCase.observations.empty")}</Text>
                )}
                {listStatus.kind === "ready" && observations.length > 0 && (
                  <Stack gap="inter-section">
                    {observations.map((observation) => {
                      const evidenceForObservation = allEvidence.filter(
                        (e) => e.observationId === observation.observationId,
                      );
                      const thisCreateStatus: EvidenceCreateStatus = evidenceCreateStatus[
                        observation.observationId
                      ] ?? { kind: "idle" };
                      const thisForm: EvidenceFormInput =
                        evidenceForm[observation.observationId] ?? EMPTY_EVIDENCE_FORM;

                      const knowledgeReferencesForObservation = allKnowledgeReferences.filter(
                        (k) =>
                          k.target.targetType === "Observation" &&
                          k.target.targetId === observation.observationId,
                      );
                      const thisKnowledgeReferenceCreateStatus: KnowledgeReferenceCreateStatus =
                        knowledgeReferenceCreateStatus[observation.observationId] ?? {
                          kind: "idle",
                        };

                      const reasoningTracesForObservation = allReasoningTraces.filter((trace) =>
                        trace.supports.some(
                          (support) =>
                            support.targetType === "Observation" &&
                            support.targetId === observation.observationId,
                        ),
                      );
                      const thisReasoningTraceCreateStatus: ReasoningTraceCreateStatus =
                        reasoningTraceCreateStatus[observation.observationId] ?? { kind: "idle" };

                      const judgmentsForObservation = allJudgments.filter(
                        (judgment) =>
                          judgment.subject !== null &&
                          judgment.subject.targetType === "Observation" &&
                          judgment.subject.targetId === observation.observationId,
                      );
                      const thisJudgmentCreateStatus: JudgmentCreateStatus =
                        judgmentCreateStatus[observation.observationId] ?? { kind: "idle" };
                      const thisJudgmentForm = judgmentForm[observation.observationId] ?? "";

                      const decisionsForObservation = allDecisions.filter(
                        (decision) => decision.observationId === observation.observationId,
                      );
                      const thisDecisionCreateStatus: DecisionCreateStatus =
                        decisionCreateStatus[observation.observationId] ?? { kind: "idle" };
                      const thisDecisionForm: DecisionFormInput =
                        decisionForm[observation.observationId] ?? EMPTY_DECISION_FORM;

                      const decisionIdsForObservation = new Set(
                        decisionsForObservation.map((decision) => decision.id),
                      );
                      const outcomesForObservation = allOutcomes.filter((outcome) =>
                        decisionIdsForObservation.has(outcome.decisionId),
                      );
                      const thisOutcomeCreateStatus: OutcomeCreateStatus =
                        outcomeCreateStatus[observation.observationId] ?? { kind: "idle" };
                      const thisOutcomeForm: OutcomeFormInput = outcomeForm[
                        observation.observationId
                      ] ?? {
                        ...EMPTY_OUTCOME_FORM,
                        decisionId:
                          decisionsForObservation.length === 1
                            ? decisionsForObservation[0]?.id ?? ""
                            : "",
                        transactionType:
                          decisionsForObservation.length === 1
                            ? defaultTransactionTypeForDecisionType(
                                decisionsForObservation[0]?.decisionType,
                              )
                            : EMPTY_OUTCOME_FORM.transactionType,
                      };
                      const thisTradeApplyStatus: TradeApplyStatus =
                        tradeApplyStatus[observation.observationId] ?? { kind: "idle" };

                      return (
                        <div key={observation.observationId}>
                          <Text>{observation.subject}</Text>
                          <Text color="secondary" as="p">
                            {observation.statement}
                          </Text>
                          <Text color="tertiary" as="p">
                            {formatRelativeTime(observation.observedAt, t)}
                          </Text>

                          <Stack gap="inter-section">
                            <Heading level={4}>{t("investmentCase.evidence.heading")}</Heading>

                            {evidenceListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                {t("investmentCase.evidence.loading")}
                              </Text>
                            )}
                            {evidenceListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                {t("investmentCase.evidence.loadError", {
                                  message: evidenceListStatus.message,
                                })}
                              </Text>
                            )}
                            {evidenceListStatus.kind === "ready" &&
                              evidenceForObservation.length === 0 && (
                                <Text color="secondary">{t("investmentCase.evidence.empty")}</Text>
                              )}
                            {evidenceListStatus.kind === "ready" &&
                              evidenceForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {evidenceForObservation.map((evidence) => (
                                    <div key={evidence.evidenceId}>
                                      <Text>{evidence.statement}</Text>
                                      <Text color="secondary" as="p">
                                        {evidence.direction === "SUPPORTS"
                                          ? t("investmentCase.evidence.directionSupports")
                                          : t("investmentCase.evidence.directionChallenges")}
                                        {evidence.source ? ` — ${evidence.source}` : ""}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() => deleteEvidence(evidence.evidenceId)}
                                        disabled={
                                          evidenceDeleteStatus[evidence.evidenceId] === "deleting"
                                        }
                                      >
                                        {evidenceDeleteStatus[evidence.evidenceId] === "deleting"
                                          ? t("common.deleting")
                                          : t("common.delete")}
                                      </Button>
                                      {evidenceDeleteStatus[evidence.evidenceId] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          {t("investmentCase.evidence.deleteError")}
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setEvidenceCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                {t("investmentCase.evidence.addButton")}
                              </Button>
                            )}

                            {thisCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  {t("investmentCase.evidence.recorded", {
                                    statement: thisCreateStatus.evidence.statement,
                                  })}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setEvidenceForm((current) => ({
                                      ...current,
                                      [observation.observationId]: EMPTY_EVIDENCE_FORM,
                                    }));
                                    setEvidenceCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  {t("common.addAnother")}
                                </Button>
                              </Stack>
                            )}

                            {(thisCreateStatus.kind === "creating" ||
                              thisCreateStatus.kind === "submitting" ||
                              thisCreateStatus.kind === "validation-error" ||
                              thisCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text as="label">
                                  {t("investmentCase.evidence.summaryLabel")}
                                  <br />
                                  <input
                                    value={thisForm.summary}
                                    onChange={(event) =>
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisForm,
                                          summary: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  {t("investmentCase.evidence.sourceLabel")}
                                  <br />
                                  <input
                                    value={thisForm.source}
                                    onChange={(event) =>
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisForm,
                                          source: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  {t("investmentCase.evidence.directionLabel")}
                                  <br />
                                  <select
                                    value={thisForm.direction}
                                    onChange={(event) =>
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisForm,
                                          direction: event.target.value as "SUPPORTS" | "CHALLENGES",
                                        },
                                      }))
                                    }
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  >
                                    <option value="SUPPORTS">
                                      {t("investmentCase.evidence.directionSupports")}
                                    </option>
                                    <option value="CHALLENGES">
                                      {t("investmentCase.evidence.directionChallenges")}
                                    </option>
                                  </select>
                                </Text>

                                {thisCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisCreateStatus.message}
                                  </Text>
                                )}
                                {thisCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.evidence.recordError", {
                                      message: thisCreateStatus.message,
                                    })}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitEvidence(observation.observationId)}
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  >
                                    {thisCreateStatus.kind === "submitting"
                                      ? t("common.submitting")
                                      : t("common.submit")}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: EMPTY_EVIDENCE_FORM,
                                      }));
                                      setEvidenceCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  >
                                    {t("common.cancel")}
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>
                              {t("investmentCase.knowledgeReference.heading")}
                            </Heading>

                            {knowledgeReferenceListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                {t("investmentCase.knowledgeReference.loading")}
                              </Text>
                            )}
                            {knowledgeReferenceListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                {t("investmentCase.knowledgeReference.loadError", {
                                  message: knowledgeReferenceListStatus.message,
                                })}
                              </Text>
                            )}
                            {knowledgeReferenceListStatus.kind === "ready" &&
                              knowledgeReferencesForObservation.length === 0 && (
                                <Text color="secondary">
                                  {t("investmentCase.knowledgeReference.empty")}
                                </Text>
                              )}
                            {knowledgeReferenceListStatus.kind === "ready" &&
                              knowledgeReferencesForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {knowledgeReferencesForObservation.map((knowledgeReference) => (
                                    <div key={knowledgeReference.knowledgeReferenceId}>
                                      <Text>
                                        {t("investmentCase.knowledgeReference.itemLabel", {
                                          id: knowledgeReference.knowledgeReferenceId,
                                        })}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        {formatRelativeTime(knowledgeReference.recordedAt, t)}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() =>
                                          deleteKnowledgeReference(
                                            knowledgeReference.knowledgeReferenceId,
                                          )
                                        }
                                        disabled={
                                          knowledgeReferenceDeleteStatus[
                                            knowledgeReference.knowledgeReferenceId
                                          ] === "deleting"
                                        }
                                      >
                                        {knowledgeReferenceDeleteStatus[
                                          knowledgeReference.knowledgeReferenceId
                                        ] === "deleting"
                                          ? t("common.deleting")
                                          : t("common.delete")}
                                      </Button>
                                      {knowledgeReferenceDeleteStatus[
                                        knowledgeReference.knowledgeReferenceId
                                      ] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          {t("investmentCase.knowledgeReference.deleteError")}
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisKnowledgeReferenceCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setKnowledgeReferenceCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                {t("investmentCase.knowledgeReference.addButton")}
                              </Button>
                            )}

                            {thisKnowledgeReferenceCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  {t("investmentCase.knowledgeReference.recorded", {
                                    id: thisKnowledgeReferenceCreateStatus.knowledgeReference
                                      .knowledgeReferenceId,
                                  })}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() =>
                                    setKnowledgeReferenceCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }))
                                  }
                                >
                                  {t("common.addAnother")}
                                </Button>
                              </Stack>
                            )}

                            {(thisKnowledgeReferenceCreateStatus.kind === "creating" ||
                              thisKnowledgeReferenceCreateStatus.kind === "submitting" ||
                              thisKnowledgeReferenceCreateStatus.kind === "validation-error" ||
                              thisKnowledgeReferenceCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text color="secondary">
                                  {t("investmentCase.knowledgeReference.prompt")}
                                </Text>

                                {thisKnowledgeReferenceCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisKnowledgeReferenceCreateStatus.message}
                                  </Text>
                                )}
                                {thisKnowledgeReferenceCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.knowledgeReference.recordError", {
                                      message: thisKnowledgeReferenceCreateStatus.message,
                                    })}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() =>
                                      submitKnowledgeReference(observation.observationId)
                                    }
                                    disabled={thisKnowledgeReferenceCreateStatus.kind === "submitting"}
                                  >
                                    {thisKnowledgeReferenceCreateStatus.kind === "submitting"
                                      ? t("common.submitting")
                                      : t("common.submit")}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() =>
                                      setKnowledgeReferenceCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }))
                                    }
                                    disabled={thisKnowledgeReferenceCreateStatus.kind === "submitting"}
                                  >
                                    {t("common.cancel")}
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>{t("investmentCase.reasoningTrace.heading")}</Heading>

                            {reasoningTraceListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                {t("investmentCase.reasoningTrace.loading")}
                              </Text>
                            )}
                            {reasoningTraceListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                {t("investmentCase.reasoningTrace.loadError", {
                                  message: reasoningTraceListStatus.message,
                                })}
                              </Text>
                            )}
                            {reasoningTraceListStatus.kind === "ready" &&
                              reasoningTracesForObservation.length === 0 && (
                                <Text color="secondary">
                                  {t("investmentCase.reasoningTrace.empty")}
                                </Text>
                              )}
                            {reasoningTraceListStatus.kind === "ready" &&
                              reasoningTracesForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {reasoningTracesForObservation.map((reasoningTrace) => (
                                    <div key={reasoningTrace.reasoningTraceId}>
                                      <Text>
                                        {t("investmentCase.reasoningTrace.itemLabel", {
                                          id: reasoningTrace.reasoningTraceId,
                                        })}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        {formatRelativeTime(reasoningTrace.recordedAt, t)}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() =>
                                          deleteReasoningTrace(reasoningTrace.reasoningTraceId)
                                        }
                                        disabled={
                                          reasoningTraceDeleteStatus[
                                            reasoningTrace.reasoningTraceId
                                          ] === "deleting"
                                        }
                                      >
                                        {reasoningTraceDeleteStatus[
                                          reasoningTrace.reasoningTraceId
                                        ] === "deleting"
                                          ? t("common.deleting")
                                          : t("common.delete")}
                                      </Button>
                                      {reasoningTraceDeleteStatus[
                                        reasoningTrace.reasoningTraceId
                                      ] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          {t("investmentCase.reasoningTrace.deleteError")}
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisReasoningTraceCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setReasoningTraceCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                {t("investmentCase.reasoningTrace.addButton")}
                              </Button>
                            )}

                            {thisReasoningTraceCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  {t("investmentCase.reasoningTrace.recorded", {
                                    id: thisReasoningTraceCreateStatus.reasoningTrace
                                      .reasoningTraceId,
                                  })}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() =>
                                    setReasoningTraceCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }))
                                  }
                                >
                                  {t("common.addAnother")}
                                </Button>
                              </Stack>
                            )}

                            {(thisReasoningTraceCreateStatus.kind === "creating" ||
                              thisReasoningTraceCreateStatus.kind === "submitting" ||
                              thisReasoningTraceCreateStatus.kind === "validation-error" ||
                              thisReasoningTraceCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text color="secondary">
                                  {t("investmentCase.reasoningTrace.prompt")}
                                </Text>

                                {thisReasoningTraceCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisReasoningTraceCreateStatus.message}
                                  </Text>
                                )}
                                {thisReasoningTraceCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.reasoningTrace.recordError", {
                                      message: thisReasoningTraceCreateStatus.message,
                                    })}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitReasoningTrace(observation.observationId)}
                                    disabled={thisReasoningTraceCreateStatus.kind === "submitting"}
                                  >
                                    {thisReasoningTraceCreateStatus.kind === "submitting"
                                      ? t("common.submitting")
                                      : t("common.submit")}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() =>
                                      setReasoningTraceCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }))
                                    }
                                    disabled={thisReasoningTraceCreateStatus.kind === "submitting"}
                                  >
                                    {t("common.cancel")}
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>{t("investmentCase.judgment.heading")}</Heading>

                            {judgmentListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                {t("investmentCase.judgment.loading")}
                              </Text>
                            )}
                            {judgmentListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                {t("investmentCase.judgment.loadError", {
                                  message: judgmentListStatus.message,
                                })}
                              </Text>
                            )}
                            {judgmentListStatus.kind === "ready" &&
                              judgmentsForObservation.length === 0 && (
                                <Text color="secondary">{t("investmentCase.judgment.empty")}</Text>
                              )}
                            {judgmentListStatus.kind === "ready" &&
                              judgmentsForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {judgmentsForObservation.map((judgment) => (
                                    <div key={judgment.judgmentId}>
                                      <Text>{judgment.characterization}</Text>
                                      <Text color="tertiary" as="p">
                                        {formatRelativeTime(judgment.recordedAt, t)}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() => deleteJudgment(judgment.judgmentId)}
                                        disabled={
                                          judgmentDeleteStatus[judgment.judgmentId] === "deleting"
                                        }
                                      >
                                        {judgmentDeleteStatus[judgment.judgmentId] === "deleting"
                                          ? t("common.deleting")
                                          : t("common.delete")}
                                      </Button>
                                      {judgmentDeleteStatus[judgment.judgmentId] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          {t("investmentCase.judgment.deleteError")}
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisJudgmentCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setJudgmentCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                {t("investmentCase.judgment.addButton")}
                              </Button>
                            )}

                            {thisJudgmentCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  {t("investmentCase.judgment.recorded", {
                                    characterization:
                                      thisJudgmentCreateStatus.judgment.characterization,
                                  })}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setJudgmentForm((current) => ({
                                      ...current,
                                      [observation.observationId]: "",
                                    }));
                                    setJudgmentCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  {t("common.addAnother")}
                                </Button>
                              </Stack>
                            )}

                            {(thisJudgmentCreateStatus.kind === "creating" ||
                              thisJudgmentCreateStatus.kind === "submitting" ||
                              thisJudgmentCreateStatus.kind === "validation-error" ||
                              thisJudgmentCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text as="label">
                                  {t("investmentCase.judgment.characterizationLabel")}
                                  <br />
                                  <textarea
                                    value={thisJudgmentForm}
                                    onChange={(event) =>
                                      setJudgmentForm((current) => ({
                                        ...current,
                                        [observation.observationId]: event.target.value,
                                      }))
                                    }
                                    disabled={thisJudgmentCreateStatus.kind === "submitting"}
                                  />
                                </Text>

                                {thisJudgmentCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisJudgmentCreateStatus.message}
                                  </Text>
                                )}
                                {thisJudgmentCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.judgment.recordError", {
                                      message: thisJudgmentCreateStatus.message,
                                    })}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitJudgment(observation.observationId)}
                                    disabled={thisJudgmentCreateStatus.kind === "submitting"}
                                  >
                                    {thisJudgmentCreateStatus.kind === "submitting"
                                      ? t("common.submitting")
                                      : t("common.submit")}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setJudgmentForm((current) => ({
                                        ...current,
                                        [observation.observationId]: "",
                                      }));
                                      setJudgmentCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisJudgmentCreateStatus.kind === "submitting"}
                                  >
                                    {t("common.cancel")}
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>{t("investmentCase.decision.heading")}</Heading>

                            {decisionListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                {t("investmentCase.decision.loading")}
                              </Text>
                            )}
                            {decisionListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                {t("investmentCase.decision.loadError", {
                                  message: decisionListStatus.message,
                                })}
                              </Text>
                            )}
                            {decisionListStatus.kind === "ready" &&
                              decisionsForObservation.length === 0 && (
                                <Text color="secondary">{t("investmentCase.decision.empty")}</Text>
                              )}
                            {decisionListStatus.kind === "ready" &&
                              decisionsForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {decisionsForObservation.map((decision) => (
                                    <div key={decision.id}>
                                      <Text>
                                        {DECISION_TYPE_KEY[decision.decisionType]
                                          ? t(DECISION_TYPE_KEY[decision.decisionType]!)
                                          : decision.decisionType}{" "}
                                        — {decision.subject}
                                      </Text>
                                      <Text color="secondary" as="p">
                                        {decision.reason}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        {t("investmentCase.decision.confidencePrefix", {
                                          value: decision.confidence,
                                        })}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        {formatRelativeTime(decision.decidedAt, t)}
                                      </Text>
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisDecisionCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setDecisionCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                {t("investmentCase.decision.addButton")}
                              </Button>
                            )}

                            {thisDecisionCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  {t("investmentCase.decision.recorded", {
                                    decisionType: DECISION_TYPE_KEY[
                                      thisDecisionCreateStatus.decision.decisionType
                                    ]
                                      ? t(
                                          DECISION_TYPE_KEY[
                                            thisDecisionCreateStatus.decision.decisionType
                                          ]!,
                                        )
                                      : thisDecisionCreateStatus.decision.decisionType,
                                    subject: thisDecisionCreateStatus.decision.subject,
                                  })}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setDecisionForm((current) => ({
                                      ...current,
                                      [observation.observationId]: EMPTY_DECISION_FORM,
                                    }));
                                    setDecisionCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  {t("common.addAnother")}
                                </Button>
                              </Stack>
                            )}

                            {(thisDecisionCreateStatus.kind === "creating" ||
                              thisDecisionCreateStatus.kind === "submitting" ||
                              thisDecisionCreateStatus.kind === "validation-error" ||
                              thisDecisionCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text as="label">
                                  {t("investmentCase.decision.typeLabel")}
                                  <br />
                                  <select
                                    value={thisDecisionForm.decisionType}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          decisionType: event.target.value as
                                            | "BUY"
                                            | "SELL"
                                            | "HOLD"
                                            | "WATCH"
                                            | "PASS",
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  >
                                    <option value="BUY">{t("investmentCase.decision.typeBuy")}</option>
                                    <option value="SELL">{t("investmentCase.decision.typeSell")}</option>
                                    <option value="HOLD">{t("investmentCase.decision.typeHold")}</option>
                                    <option value="WATCH">
                                      {t("investmentCase.decision.typeWatch")}
                                    </option>
                                    <option value="PASS">{t("investmentCase.decision.typePass")}</option>
                                  </select>
                                </Text>
                                <Text as="label">
                                  {t("investmentCase.decision.subjectLabel")}
                                  <br />
                                  <input
                                    value={thisDecisionForm.subject}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          subject: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  {t("investmentCase.decision.reasonLabel")}
                                  <br />
                                  <textarea
                                    value={thisDecisionForm.reason}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          reason: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  {t("investmentCase.decision.confidenceLabel")}
                                  <br />
                                  <input
                                    type="number"
                                    min={0}
                                    max={100}
                                    value={thisDecisionForm.confidence}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          confidence: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  />
                                </Text>

                                {thisDecisionCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisDecisionCreateStatus.message}
                                  </Text>
                                )}
                                {thisDecisionCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.decision.recordError", {
                                      message: thisDecisionCreateStatus.message,
                                    })}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() =>
                                      submitDecision(
                                        observation.observationId,
                                        observation.observationId,
                                      )
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  >
                                    {thisDecisionCreateStatus.kind === "submitting"
                                      ? t("common.submitting")
                                      : t("common.submit")}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: EMPTY_DECISION_FORM,
                                      }));
                                      setDecisionCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  >
                                    {t("common.cancel")}
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>{t("investmentCase.outcome.heading")}</Heading>

                            {outcomeListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                {t("investmentCase.outcome.loading")}
                              </Text>
                            )}
                            {outcomeListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                {t("investmentCase.outcome.loadError", {
                                  message: outcomeListStatus.message,
                                })}
                              </Text>
                            )}
                            {outcomeListStatus.kind === "ready" &&
                              outcomesForObservation.length === 0 && (
                                <Text color="secondary">{t("investmentCase.outcome.empty")}</Text>
                              )}
                            {outcomeListStatus.kind === "ready" &&
                              outcomesForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {outcomesForObservation.map((outcome) => (
                                    <div key={outcome.id}>
                                      <Text>{outcome.statement}</Text>
                                      {outcome.note && (
                                        <Text color="secondary" as="p">
                                          {outcome.note}
                                        </Text>
                                      )}
                                      <Text color="tertiary" as="p">
                                        {outcome.occurredAt}
                                      </Text>
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {decisionsForObservation.length === 0 && (
                              <Text color="secondary">
                                {t("investmentCase.outcome.needsDecisionFirst")}
                              </Text>
                            )}

                            {decisionsForObservation.length > 0 &&
                              thisOutcomeCreateStatus.kind === "idle" && (
                                <Button
                                  variant="tertiary"
                                  onClick={() =>
                                    setOutcomeCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }))
                                  }
                                >
                                  {t("investmentCase.outcome.addButton")}
                                </Button>
                              )}

                            {thisOutcomeCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  {t("investmentCase.outcome.recorded", {
                                    statement: thisOutcomeCreateStatus.outcome.statement,
                                  })}
                                </Text>
                                {thisTradeApplyStatus.kind === "applying" && (
                                  <Text role="status" aria-live="polite">
                                    {t("investmentCase.outcome.updatingPortfolio")}
                                  </Text>
                                )}
                                {thisTradeApplyStatus.kind === "updated" && (
                                  <Text color="secondary">
                                    {t("investmentCase.outcome.updatedAutomatically")}
                                  </Text>
                                )}
                                {thisTradeApplyStatus.kind === "awaiting-reconciliation" && (
                                  <Text color="tertiary">
                                    {t("investmentCase.outcome.awaitingReconciliation")}
                                  </Text>
                                )}
                                {thisTradeApplyStatus.kind === "error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.outcome.applyTradeError", {
                                      message: thisTradeApplyStatus.message,
                                    })}
                                  </Text>
                                )}
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [observation.observationId]: {
                                        ...EMPTY_OUTCOME_FORM,
                                        decisionId:
                                          decisionsForObservation.length === 1
                                            ? decisionsForObservation[0]?.id ?? ""
                                            : "",
                                        transactionType:
                                          decisionsForObservation.length === 1
                                            ? defaultTransactionTypeForDecisionType(
                                                decisionsForObservation[0]?.decisionType,
                                              )
                                            : EMPTY_OUTCOME_FORM.transactionType,
                                      },
                                    }));
                                    setOutcomeCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  {t("common.addAnother")}
                                </Button>
                              </Stack>
                            )}

                            {(thisOutcomeCreateStatus.kind === "creating" ||
                              thisOutcomeCreateStatus.kind === "submitting" ||
                              thisOutcomeCreateStatus.kind === "validation-error" ||
                              thisOutcomeCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                {decisionsForObservation.length > 1 && (
                                  <Text as="label">
                                    {t("investmentCase.outcome.decisionLabel")}
                                    <br />
                                    <select
                                      value={thisOutcomeForm.decisionId}
                                      onChange={(event) =>
                                        setOutcomeForm((current) => ({
                                          ...current,
                                          [observation.observationId]: {
                                            ...thisOutcomeForm,
                                            decisionId: event.target.value,
                                          },
                                        }))
                                      }
                                      disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                    >
                                      <option value="">
                                        {t("investmentCase.outcome.decisionPlaceholder")}
                                      </option>
                                      {decisionsForObservation.map((decision) => (
                                        <option key={decision.id} value={decision.id}>
                                          {DECISION_TYPE_KEY[decision.decisionType]
                                            ? t(DECISION_TYPE_KEY[decision.decisionType]!)
                                            : decision.decisionType}{" "}
                                          — {decision.subject}
                                        </option>
                                      ))}
                                    </select>
                                  </Text>
                                )}
                                <Text as="label">
                                  {t("investmentCase.outcome.statementLabel")}
                                  <br />
                                  <textarea
                                    value={thisOutcomeForm.statement}
                                    onChange={(event) =>
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisOutcomeForm,
                                          statement: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  {t("investmentCase.outcome.noteLabel")}
                                  <br />
                                  <textarea
                                    value={thisOutcomeForm.note}
                                    onChange={(event) =>
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisOutcomeForm,
                                          note: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  />
                                </Text>

                                <Text as="label">
                                  <input
                                    type="checkbox"
                                    checked={thisOutcomeForm.isExternalTrade}
                                    onChange={(event) =>
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisOutcomeForm,
                                          isExternalTrade: event.target.checked,
                                        },
                                      }))
                                    }
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  />{" "}
                                  {t("investmentCase.outcome.externalTradeCheckbox")}
                                </Text>

                                {thisOutcomeForm.isExternalTrade && (
                                  <Stack gap="inter-section">
                                    <Text as="label">
                                      {t("investmentCase.outcome.securityLabel")}
                                      <br />
                                      <input
                                        value={thisOutcomeForm.security}
                                        onChange={(event) =>
                                          setOutcomeForm((current) => ({
                                            ...current,
                                            [observation.observationId]: {
                                              ...thisOutcomeForm,
                                              security: event.target.value,
                                            },
                                          }))
                                        }
                                        disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                      />
                                    </Text>
                                    <Text as="label">
                                      {t("investmentCase.outcome.typeLabel")}
                                      <br />
                                      <select
                                        value={thisOutcomeForm.transactionType}
                                        onChange={(event) =>
                                          setOutcomeForm((current) => ({
                                            ...current,
                                            [observation.observationId]: {
                                              ...thisOutcomeForm,
                                              transactionType: event.target.value as
                                                | "BUY"
                                                | "SELL"
                                                | "ADD"
                                                | "EXIT",
                                            },
                                          }))
                                        }
                                        disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                      >
                                        <option value="BUY">
                                          {t("investmentCase.decision.typeBuy")}
                                        </option>
                                        <option value="ADD">
                                          {t("investmentCase.outcome.transactionTypeAdd")}
                                        </option>
                                        <option value="SELL">
                                          {t("investmentCase.decision.typeSell")}
                                        </option>
                                        <option value="EXIT">
                                          {t("investmentCase.outcome.transactionTypeExit")}
                                        </option>
                                      </select>
                                    </Text>
                                    <Text as="label">
                                      {t("investmentCase.outcome.quantityLabel")}
                                      <br />
                                      <input
                                        value={thisOutcomeForm.quantity}
                                        onChange={(event) =>
                                          setOutcomeForm((current) => ({
                                            ...current,
                                            [observation.observationId]: {
                                              ...thisOutcomeForm,
                                              quantity: event.target.value,
                                            },
                                          }))
                                        }
                                        disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                      />
                                    </Text>
                                    <Text as="label">
                                      {t("investmentCase.outcome.executionPriceLabel")}
                                      <br />
                                      <input
                                        value={thisOutcomeForm.executionPrice}
                                        onChange={(event) =>
                                          setOutcomeForm((current) => ({
                                            ...current,
                                            [observation.observationId]: {
                                              ...thisOutcomeForm,
                                              executionPrice: event.target.value,
                                            },
                                          }))
                                        }
                                        disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                      />
                                    </Text>
                                    <Text as="label">
                                      {t("investmentCase.outcome.feesLabel")}
                                      <br />
                                      <input
                                        value={thisOutcomeForm.fees}
                                        onChange={(event) =>
                                          setOutcomeForm((current) => ({
                                            ...current,
                                            [observation.observationId]: {
                                              ...thisOutcomeForm,
                                              fees: event.target.value,
                                            },
                                          }))
                                        }
                                        disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                      />
                                    </Text>
                                    <Text as="label">
                                      {t("investmentCase.outcome.executedAtLabel")}
                                      <br />
                                      <input
                                        type="datetime-local"
                                        value={thisOutcomeForm.executedAt}
                                        onChange={(event) =>
                                          setOutcomeForm((current) => ({
                                            ...current,
                                            [observation.observationId]: {
                                              ...thisOutcomeForm,
                                              executedAt: event.target.value
                                                ? new Date(event.target.value).toISOString()
                                                : "",
                                            },
                                          }))
                                        }
                                        disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                      />
                                    </Text>
                                  </Stack>
                                )}

                                {thisOutcomeCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisOutcomeCreateStatus.message}
                                  </Text>
                                )}
                                {thisOutcomeCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    {t("investmentCase.outcome.recordError", {
                                      message: thisOutcomeCreateStatus.message,
                                    })}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitOutcome(observation.observationId)}
                                    disabled={
                                      thisOutcomeCreateStatus.kind === "submitting" ||
                                      !thisOutcomeForm.decisionId
                                    }
                                  >
                                    {thisOutcomeCreateStatus.kind === "submitting"
                                      ? t("common.submitting")
                                      : t("common.submit")}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...EMPTY_OUTCOME_FORM,
                                          decisionId:
                                            decisionsForObservation.length === 1
                                              ? decisionsForObservation[0]?.id ?? ""
                                              : "",
                                        },
                                      }));
                                      setOutcomeCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  >
                                    {t("common.cancel")}
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>
                        </div>
                      );
                    })}
                  </Stack>
                )}

                <Divider tone="hairline" />

                {createStatus.kind === "idle" && (
                  <Button
                    variant="tertiary"
                    onClick={() => setCreateStatus({ kind: "creating" })}
                  >
                    {t("investmentCase.observations.addButton")}
                  </Button>
                )}

                {createStatus.kind === "success" && (
                  <Stack gap="inter-section">
                    <Text>
                      {t("investmentCase.observations.recorded", {
                        subject: createStatus.observation.subject,
                      })}
                    </Text>
                    <Button
                      variant="tertiary"
                      onClick={() => {
                        setSubjectInput("");
                        setStatementInput("");
                        setCreateStatus({ kind: "creating" });
                      }}
                    >
                      {t("common.addAnother")}
                    </Button>
                  </Stack>
                )}

                {(createStatus.kind === "creating" ||
                  createStatus.kind === "submitting" ||
                  createStatus.kind === "validation-error" ||
                  createStatus.kind === "api-error") && (
                  <Stack gap="inter-section">
                    <Text as="label">
                      {t("investmentCase.observations.subjectLabel")}
                      <br />
                      <input
                        value={subjectInput}
                        onChange={(event) => setSubjectInput(event.target.value)}
                        disabled={createStatus.kind === "submitting"}
                      />
                    </Text>
                    <Text as="label">
                      {t("investmentCase.observations.statementLabel")}
                      <br />
                      <textarea
                        value={statementInput}
                        onChange={(event) => setStatementInput(event.target.value)}
                        disabled={createStatus.kind === "submitting"}
                      />
                    </Text>

                    {createStatus.kind === "validation-error" && (
                      <Text color="tertiary" role="alert">
                        {createStatus.message}
                      </Text>
                    )}
                    {createStatus.kind === "api-error" && (
                      <Text color="tertiary" role="alert">
                        {t("investmentCase.observations.recordError", {
                          message: createStatus.message,
                        })}
                      </Text>
                    )}

                    <div>
                      <Button
                        variant="primary"
                        onClick={submitObservation}
                        disabled={createStatus.kind === "submitting"}
                      >
                        {createStatus.kind === "submitting"
                          ? t("common.submitting")
                          : t("common.submit")}
                      </Button>{" "}
                      <Button
                        variant="tertiary"
                        onClick={() => {
                          setSubjectInput("");
                          setStatementInput("");
                          setCreateStatus({ kind: "idle" });
                        }}
                        disabled={createStatus.kind === "submitting"}
                      >
                        {t("common.cancel")}
                      </Button>
                    </div>
                  </Stack>
                )}
              </Stack>
            </ExpandableDetail>
          )}
          </Stack>
            )}

            <Divider tone="hairline" />

            {/* Continuity footer — worded so the application never claims
                active intelligence that isn't implemented yet. */}
            <Stack gap="metadata">
              <Text color="tertiary">{t("investmentCase.continuity.line1")}</Text>
              <Text color="tertiary">{t("investmentCase.continuity.line2")}</Text>
            </Stack>
          </>
        )}
      </Stack>
    </Container>
  );
}

const OPEN_QUESTION_KEY: Record<OpenQuestionKind, TranslationKey> = {
  no_evidence_recorded_for_case: "investmentCase.intelligence.openQuestions.noEvidenceRecordedForCase",
  observation_without_evidence: "investmentCase.intelligence.openQuestions.observationWithoutEvidence",
  decision_without_linked_observation:
    "investmentCase.intelligence.openQuestions.decisionWithoutLinkedObservation",
  business_durability_not_assessable: "investmentCase.intelligence.openQuestions.businessDurabilityNotAssessable",
  valuation_thesis_not_documented: "investmentCase.intelligence.openQuestions.valuationThesisNotDocumented",
  portfolio_factor_not_assessable: "investmentCase.intelligence.openQuestions.portfolioFactorNotAssessable",
};

// CONFIDENCE_KEY/CONVICTION_LEVEL_KEY now live in "../status/statusTone"
// (imported above) -- Portfolio Cockpit and Investment Case read the
// same `CanonicalAnalysis`, so the Conviction/Confidence vocabularies
// must be identical (Phase 47's own cross-surface consistency rule),
// not just similarly worded.
// VALUATION_STATUS_KEY/RISK_STATUS_KEY/RISK_CATEGORY_KEY/
// BUSINESS_STATUS_KEY/BUSINESS_CATEGORY_KEY now live in
// "../changeIntelligence/describeChange" (imported above).

// DECISION_SUPPORT_BADGE_KEY/DECISION_SUPPORT_STATEMENT_KEY/
// DECISION_SUPPORT_TONE now live in "../status/statusTone" (imported
// above) -- Workspace Migration Phase 1 evidence-support presentation
// layer (Decision Log #1); see that module's own doc comment.

// humanize/Translate now live in "../changeIntelligence/describeChange"
// (imported above).

/** Reused verbatim from `PortfolioPage.tsx`'s own lookup (ATLAS-028) --
 * same raw `ConcentrationLevel` enum value, same translation keys. */
const CASE_CONCENTRATION_LEVEL_KEY: Record<string, TranslationKey> = {
  Low: "portfolio.concentrationLevel.low",
  Moderate: "portfolio.concentrationLevel.moderate",
  Elevated: "portfolio.concentrationLevel.elevated",
  High: "portfolio.concentrationLevel.high",
};

const OUTSTANDING_ISSUE_KEY: Record<OutstandingIssueKind, TranslationKey> = {
  missingEvidence: "investmentCase.executiveSummary.outstandingIssues.missingEvidence",
  thesisStale: "investmentCase.executiveSummary.outstandingIssues.thesisStale",
  outcomeMissing: "investmentCase.executiveSummary.outstandingIssues.outcomeMissing",
  tradeMissing: "investmentCase.executiveSummary.outstandingIssues.tradeMissing",
  reconciliationNeeded: "investmentCase.executiveSummary.outstandingIssues.reconciliationNeeded",
};

/** Corrective pass (compactness): "Show at most 3 issues in the
 * Executive Summary... full issue detail remains available further
 * down the page" -- a display cap on `ExecutiveSummaryCard` only;
 * `deriveOutstandingIssues` itself is untouched. */
const MAX_OUTSTANDING_ISSUES_SHOWN = 3;

/**
 * Executive Summary (Investment Case Workspace v2, Sprint 2) -- the new
 * top section this sprint adds, immediately below the existing page
 * header and above the unchanged canonical analysis sections. Every
 * value is either read straight from `InvestmentCaseAnalysisView`/
 * `AlphaPortfolioView` (already fetched by this page) or selected by
 * `deriveExecutiveSummary.ts`'s pure functions from those same values --
 * nothing here computes a new fact, and nothing here selects a
 * directional Recommendation (see that module's own file-header
 * rationale, and `PortfolioPage.tsx`'s identical "Priority" rationale --
 * Current Priority here is the same kind of temporary stand-in, not a
 * Recommendation model).
 *
 * **Traceability** (per this sprint's own principle): each subsection
 * below carries a `data-trace-source` attribute naming which underlying
 * analysis axis it came from (assessment/priority/portfolioImpact/
 * outstandingIssues/discuss). No click handler exists yet -- this
 * sprint doesn't implement navigation -- but a future sprint can wire
 * "click a summary line -> jump to its supporting section" without
 * restructuring this markup.
 */
function ExecutiveSummaryCard({
  analysis,
  linkedHolding,
  alphaPortfolioStatus,
  outstandingWorkKinds,
  t,
}: {
  analysis: InvestmentCaseAnalysisView;
  linkedHolding: AlphaHoldingView | null;
  alphaPortfolioStatus: AlphaPortfolioStatus;
  outstandingWorkKinds: OutstandingWorkKind[];
  t: Translate;
}) {
  // Corrective pass (UX-020 Hero implementation): the former assessment-
  // points paragraph and priority chip that used to render here now
  // render, as one coherent narrative, in `HeroCard` above -- the same
  // Conviction/Valuation/Risk/thesis-staleness facts, never a second,
  // divergent computation of them. This card keeps only the content
  // `HeroCard` does not cover: Portfolio Impact and Outstanding Issues.
  const evidenceGap =
    analysis.evidenceQuality !== null &&
    (analysis.evidenceQuality.coverage === "none" || analysis.evidenceQuality.coverage === "partial");
  const hasOutstandingWork = outstandingWorkKinds.length > 0;

  const outstandingIssues = deriveOutstandingIssues({
    outstandingWorkKinds,
    isThesisStale: analysis.isThesisStale,
    evidenceGap,
  });

  const holdings = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.holdings : [];
  const largestHolding = holdings.reduce<AlphaHoldingView | null>(
    (max, h) => (max === null || h.weightPercent > max.weightPercent ? h : max),
    null,
  );
  const isLargestPosition =
    linkedHolding !== null && largestHolding !== null && largestHolding.ticker === linkedHolding.ticker;
  const cashWeightPercent = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.cashWeightPercent : null;
  const concentrationLevel = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.concentrationLevel : null;

  const portfolioImpactParts: string[] = [
    linkedHolding
      ? t("investmentCase.executiveSummary.portfolioImpact.weight", { percent: linkedHolding.weightPercent.toFixed(1) })
      : null,
    // Corrective pass (compactness): "largest position" and
    // "concentration" both describe the same concentration-relevance
    // fact -- showing both is exactly the redundant portfolio metric
    // this pass asks to avoid. Largest position is the more specific,
    // more decision-relevant of the two when true; concentration is the
    // fallback context otherwise. At most one of them renders.
    isLargestPosition
      ? t("investmentCase.executiveSummary.portfolioImpact.largestPosition")
      : concentrationLevel
        ? t("portfolio.concentration", {
            value: CASE_CONCENTRATION_LEVEL_KEY[concentrationLevel]
              ? t(CASE_CONCENTRATION_LEVEL_KEY[concentrationLevel]!)
              : concentrationLevel,
          })
        : null,
    cashWeightPercent !== null
      ? t("investmentCase.executiveSummary.portfolioImpact.cash", { percent: cashWeightPercent.toFixed(1) })
      : null,
  ].filter((part): part is string => part !== null);

  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.executiveSummary.heading")}</Label>

      {portfolioImpactParts.length > 0 && (
        <Text as="p" color="tertiary" data-trace-source="portfolioImpact">
          {t("investmentCase.executiveSummary.portfolioImpact.heading")}: {portfolioImpactParts.join(" · ")}
        </Text>
      )}

      {outstandingIssues.length > 0 && (
        <Text as="p" color="tertiary" data-trace-source="outstandingIssues">
          {t("investmentCase.executiveSummary.outstandingIssues.heading")}:{" "}
          {/* Corrective pass (compactness): "Show at most 3 issues ...
              show '+ N more issues'" -- full, untruncated detail remains
              exactly where it already was, in the unchanged Outstanding
              work section further down the page; this is a display cap
              only, `outstandingIssues` itself is unchanged. */}
          {outstandingIssues
            .slice(0, MAX_OUTSTANDING_ISSUES_SHOWN)
            .map((issue) => t(OUTSTANDING_ISSUE_KEY[issue]))
            .join(", ")}
          {outstandingIssues.length > MAX_OUTSTANDING_ISSUES_SHOWN &&
            ` ${t(
              outstandingIssues.length - MAX_OUTSTANDING_ISSUES_SHOWN === 1
                ? "investmentCase.executiveSummary.outstandingIssues.moreCountOne"
                : "investmentCase.executiveSummary.outstandingIssues.moreCountOther",
              { count: outstandingIssues.length - MAX_OUTSTANDING_ISSUES_SHOWN },
            )}`}
        </Text>
      )}
    </Stack>
  );
}


/**
 * Product Sprint 7 (Investment Case Excellence) -- this comment
 * previously described a "Business / Valuation / Risk / Evidence"
 * four-card layout from an earlier iteration (Investment Case
 * Workspace v2, Sprint 2), including a `BusinessSection` component.
 * That layout was superseded by `InvestmentCaseCanonicalSections`
 * (`AtlasOutlookSection` → `InvestmentArgumentSection` →
 * `AtlasReasoningSection` → `CompanyHealthAssessmentSection` →
 * `InterpretedFinancialEvidenceSection` → `CompanyOverviewSection` →
 * `EvidenceSection`, rendered above the tab bar) without this comment
 * being updated -- `BusinessSection` itself had zero call sites left
 * anywhere on the page and is removed as dead code this sprint.
 * `RiskSection`/`EvidenceSection`/`ValuationDetailSection` referenced
 * below are still real and still live in the `moreDetails` tab.
 */
/** Company Health Assessment summary sentences -- deliberately fuller
 * and more assessment-toned than `AtlasReasoningSection`'s own terse
 * interpretation sentences, even for the two cards (Business Quality,
 * Financial Strength) that read from the same underlying finding as one
 * of that section's cards. Depth differs; the underlying real status
 * never does. `insufficient_input`/`not_evaluated` share one honest
 * "not yet evaluated" sentence across every card, per this codebase's
 * standing discipline against fabricating an assessment it doesn't have. */
const NOT_YET_EVALUATED_KEY: TranslationKey = "investmentCase.companyHealth.notYetEvaluated";

const BUSINESS_QUALITY_SUMMARY_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  strong: "investmentCase.companyHealth.businessQuality.strong",
  moderate: "investmentCase.companyHealth.businessQuality.moderate",
  weak: "investmentCase.companyHealth.businessQuality.weak",
  insufficient_input: NOT_YET_EVALUATED_KEY,
  not_evaluated: NOT_YET_EVALUATED_KEY,
};

const FINANCIAL_STRENGTH_SUMMARY_KEY: Record<AnalysisRiskStatus, TranslationKey> = {
  low: "investmentCase.companyHealth.financialStrength.low",
  moderate: "investmentCase.companyHealth.financialStrength.moderate",
  high: "investmentCase.companyHealth.financialStrength.high",
  insufficient_input: NOT_YET_EVALUATED_KEY,
  not_evaluated: NOT_YET_EVALUATED_KEY,
};

const MANAGEMENT_SUMMARY_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  strong: "investmentCase.companyHealth.management.strong",
  moderate: "investmentCase.companyHealth.management.moderate",
  weak: "investmentCase.companyHealth.management.weak",
  insufficient_input: NOT_YET_EVALUATED_KEY,
  not_evaluated: NOT_YET_EVALUATED_KEY,
};

const CAPITAL_ALLOCATION_SUMMARY_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  strong: "investmentCase.companyHealth.capitalAllocation.strong",
  moderate: "investmentCase.companyHealth.capitalAllocation.moderate",
  weak: "investmentCase.companyHealth.capitalAllocation.weak",
  insufficient_input: NOT_YET_EVALUATED_KEY,
  not_evaluated: NOT_YET_EVALUATED_KEY,
};

const COMPETITIVE_POSITION_SUMMARY_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  strong: "investmentCase.companyHealth.competitivePosition.strong",
  moderate: "investmentCase.companyHealth.competitivePosition.moderate",
  weak: "investmentCase.companyHealth.competitivePosition.weak",
  insufficient_input: NOT_YET_EVALUATED_KEY,
  not_evaluated: NOT_YET_EVALUATED_KEY,
};

/**
 * Investment Case body (Figma-fidelity rebuild): Atlas Outlook,
 * Investment Argument, Atlas Reasoning, Company Health Assessment,
 * Interpreted Financial Evidence -- the approved design's own named
 * hierarchy, each a distinct block, never collapsed into one narrative
 * card. Every status/finding read below is real and already fetched by
 * this page; only the sentence forms and the Outlook's per-horizon
 * scenario fields are new (the latter honestly empty -- see
 * `AtlasOutlookSection`'s own file header and this sprint's backend-gap
 * report).
 */
function InvestmentCaseCanonicalSections({
  analysis,
  linkedHolding,
  alphaPortfolioStatus,
  onViewMoreDetails,
  t,
  locale,
}: {
  analysis: InvestmentCaseAnalysisView;
  linkedHolding: AlphaHoldingView | null;
  alphaPortfolioStatus: AlphaPortfolioStatus;
  onViewMoreDetails: () => void;
  t: Translate;
  locale: string;
}) {
  const findBusiness = (kind: AnalysisBusinessCategory) => analysis.businessAnalysis.findings.find((f) => f.kind === kind);
  const findRisk = (category: AnalysisRiskCategory) => analysis.risk.findings.find((f) => f.category === category);

  const growth = findBusiness("growth");
  const capitalAllocation = findBusiness("capital_allocation");
  const durability = findBusiness("durability");
  const management = findBusiness("management");
  const competitivePosition = findBusiness("competitive_position");
  const financialRisk = findRisk("financial_risk");
  const businessRisk = findRisk("business_risk");
  const valuationRisk = findRisk("valuation_risk");
  const fcfYield = analysis.valuation.findings.find((f) => f.kind === "fcf_yield_relative");
  const valuationStatus: AnalysisValuationStatus = fcfYield ? fcfYield.status : "not_evaluated";

  const strengthKinds = analysis.strengths.map((h) => h.kind);
  const riskKinds = analysis.risks.map((h) => h.kind);

  /** Product Sprint 13 (Company Intelligence Excellence, Deliverable 6
   * -- Bull/Bear Balance): `strengthKinds`/`riskKinds` alone are bare
   * category words (`CaseHighlightView.kind`) -- the real fact text
   * that explains *why* lives on the finding each kind already maps
   * to, one lookup away via the same `findBusiness`/`findRisk`/
   * `fcfYield` this function already resolved above for
   * `AtlasReasoningSection`. Reused, not recomputed. */
  function factsForHighlightKind(kind: AnalysisHighlightKind): ReasoningFacts {
    switch (kind) {
      case "growth":
        return { supporting: growth?.supportingEvidence ?? [], contradicting: growth?.contradictingEvidence ?? [] };
      case "capital_allocation":
        return {
          supporting: capitalAllocation?.supportingEvidence ?? [],
          contradicting: capitalAllocation?.contradictingEvidence ?? [],
        };
      case "valuation":
        return { supporting: fcfYield?.supportingFacts ?? [], contradicting: fcfYield?.contradictingFacts ?? [] };
      case "business_risk":
        return { supporting: businessRisk?.supportingFacts ?? [], contradicting: businessRisk?.contradictingFacts ?? [] };
      case "financial_risk":
        return { supporting: financialRisk?.supportingFacts ?? [], contradicting: financialRisk?.contradictingFacts ?? [] };
      case "valuation_risk":
        return { supporting: valuationRisk?.supportingFacts ?? [], contradicting: valuationRisk?.contradictingFacts ?? [] };
    }
  }

  const reasoningInput: AtlasReasoningInput = {
    growthStatus: growth?.status ?? "not_evaluated",
    growthFacts: { supporting: growth?.supportingEvidence ?? [], contradicting: growth?.contradictingEvidence ?? [] },
    valuationStatus,
    valuationFacts: { supporting: fcfYield?.supportingFacts ?? [], contradicting: fcfYield?.contradictingFacts ?? [] },
    financialHealthStatus: financialRisk?.status ?? "not_evaluated",
    financialHealthFacts: {
      supporting: financialRisk?.supportingFacts ?? [],
      contradicting: financialRisk?.contradictingFacts ?? [],
    },
    businessQualityStatus: durability?.status ?? "not_evaluated",
    businessQualityFacts: {
      supporting: durability?.supportingEvidence ?? [],
      contradicting: durability?.contradictingEvidence ?? [],
    },
  };

  const companyHealthCards: CompanyHealthCardInput[] = [
    {
      labelKey: "businessQuality",
      statusLabel: t(BUSINESS_STATUS_KEY[durability?.status ?? "not_evaluated"]),
      tone: BUSINESS_STATUS_TONE[durability?.status ?? "not_evaluated"],
      summary: t(BUSINESS_QUALITY_SUMMARY_KEY[durability?.status ?? "not_evaluated"]),
      supportingEvidence: durability?.supportingEvidence ?? [],
      contradictingEvidence: durability?.contradictingEvidence ?? [],
      missingEvidence: durability?.missingEvidence ?? [],
    },
    {
      labelKey: "financialStrength",
      statusLabel: t(RISK_STATUS_KEY[financialRisk?.status ?? "not_evaluated"]),
      tone: RISK_STATUS_TONE[financialRisk?.status ?? "not_evaluated"],
      summary: t(FINANCIAL_STRENGTH_SUMMARY_KEY[financialRisk?.status ?? "not_evaluated"]),
      supportingEvidence: financialRisk?.supportingFacts ?? [],
      contradictingEvidence: financialRisk?.contradictingFacts ?? [],
      missingEvidence: financialRisk?.missingEvidence ?? [],
    },
    {
      labelKey: "managementGovernance",
      statusLabel: t(BUSINESS_STATUS_KEY[management?.status ?? "not_evaluated"]),
      tone: BUSINESS_STATUS_TONE[management?.status ?? "not_evaluated"],
      summary: t(MANAGEMENT_SUMMARY_KEY[management?.status ?? "not_evaluated"]),
      supportingEvidence: management?.supportingEvidence ?? [],
      contradictingEvidence: management?.contradictingEvidence ?? [],
      missingEvidence: management?.missingEvidence ?? [],
    },
    {
      labelKey: "capitalAllocation",
      statusLabel: t(BUSINESS_STATUS_KEY[capitalAllocation?.status ?? "not_evaluated"]),
      tone: BUSINESS_STATUS_TONE[capitalAllocation?.status ?? "not_evaluated"],
      summary: t(CAPITAL_ALLOCATION_SUMMARY_KEY[capitalAllocation?.status ?? "not_evaluated"]),
      supportingEvidence: capitalAllocation?.supportingEvidence ?? [],
      contradictingEvidence: capitalAllocation?.contradictingEvidence ?? [],
      missingEvidence: capitalAllocation?.missingEvidence ?? [],
    },
    {
      labelKey: "competitivePosition",
      statusLabel: t(BUSINESS_STATUS_KEY[competitivePosition?.status ?? "not_evaluated"]),
      tone: BUSINESS_STATUS_TONE[competitivePosition?.status ?? "not_evaluated"],
      summary: t(COMPETITIVE_POSITION_SUMMARY_KEY[competitivePosition?.status ?? "not_evaluated"]),
      supportingEvidence: competitivePosition?.supportingEvidence ?? [],
      contradictingEvidence: competitivePosition?.contradictingEvidence ?? [],
      missingEvidence: competitivePosition?.missingEvidence ?? [],
    },
  ];

  /** Atlas UX Phase 7A (Semantic Investment Model, Foundation Sprint)
   * -- reordered so the four named-in-the-spec sections
   * (Outlook -> Investment Argument -> Atlas Reasoning -> Evidence)
   * render first, directly explaining the seven-category bar above
   * them; every other panel here (deeper Coverage/Knowledge/
   * Materiality/Explanation/Evidence-Quality/Evidence-Timeline/
   * Management/Regulatory detail, plus Company Health, Financials,
   * Company Overview) is real, unremoved "everything else" -- exactly
   * the detail this sprint's own layout says exists only to explain
   * the seven categories, now positioned as such rather than ahead of
   * them. */
  return (
    <Stack gap="inter-section">
      <AtlasOutlookSection outlook={analysis.outlook} latestChanges={analysis.latestChanges} t={t} />

      <Divider tone="hairline" />

      <InvestmentArgumentSection
        strengthKinds={strengthKinds}
        riskKinds={riskKinds}
        openQuestionOrigins={analysis.keyOpenQuestions.map((q) => q.origin)}
        factsForKind={factsForHighlightKind}
        t={t}
      />

      <Divider tone="hairline" />

      <AtlasReasoningSection input={reasoningInput} t={t} />

      <Divider tone="hairline" />

      <EvidenceSection analysis={analysis} linkedHolding={linkedHolding} onViewMoreDetails={onViewMoreDetails} t={t} />

      <Divider tone="hairline" />

      {/* Convergence Sprint 1B: the evidence/audit layer. Coverage
          percentages, knowledge-coverage domains, materiality counts,
          evidence-quality grades and the evidence timeline are how Atlas
          stays auditable -- they are not how an investor decides. They
          render unchanged, one disclosure down, so the audit trail is
          fully inspectable without standing between the reader and the
          investment case. */}
      <ExpandableDetail summaryLabel={t("investmentCase.canonical.evidenceAuditLabel")}>
        <Stack gap="inter-section">
          <CoveragePanel coverage={analysis.coverage} t={t} />

          {analysis.knowledgeCoverage && (
            <>
              <Divider tone="hairline" />
              <KnowledgeCoveragePanel coverage={analysis.knowledgeCoverage} t={t} />
            </>
          )}

          {analysis.materiality && (
            <>
              <Divider tone="hairline" />
              <MaterialityPanel assessment={analysis.materiality} t={t} />
            </>
          )}

          {analysis.explanation && (
            <>
              <Divider tone="hairline" />
              <ExplanationPanel explanation={analysis.explanation} t={t} />
            </>
          )}

          {analysis.evidenceQualityReport && (
            <>
              <Divider tone="hairline" />
              <EvidenceQualityPanel report={analysis.evidenceQualityReport} t={t} />
            </>
          )}

          {analysis.evidenceTimeline && (
            <>
              <Divider tone="hairline" />
              <EvidenceTimelinePanel caseId={analysis.caseId} history={analysis.evidenceTimeline} t={t} />
            </>
          )}
        </Stack>
      </ExpandableDetail>

      {/* Convergence Sprint 1B: the deep-analysis layer. Management,
          regulatory, company-health, interpreted financials and the
          company overview are real analytical depth and are kept in
          full -- but an investor reads them when investigating, not to
          learn what Atlas concluded. Unchanged components, one
          disclosure down. */}
      <ExpandableDetail summaryLabel={t("investmentCase.canonical.deepAnalysisLabel")}>
        <Stack gap="inter-section">
          {/* Product Utilization Sprint 1 (Investment Case Experience
              Activation). Two new, always-present panels (their own
              sub-sections handle emptiness individually, the same "real
              field, honest empty state" shape every other panel here
              already uses) -- see each panel's own module docstring. */}
          <Divider tone="hairline" />
          <ManagementIntelligencePanel
            regulatoryFilings={analysis.regulatoryFilings}
            executiveChange={analysis.executiveChangeIntelligence}
            trackRecord={analysis.executiveTrackRecordIntelligence}
            governance={analysis.governanceIntelligence}
            ownership={analysis.ownershipIntelligence}
            executiveCompensation={analysis.executiveCompensationIntelligence}
            insiderAlignment={analysis.insiderAlignmentIntelligence}
            t={t}
          />

          <Divider tone="hairline" />
          <RegulatoryIntelligencePanel
            regulatoryFilings={analysis.regulatoryFilings}
            riskFactor={analysis.riskFactorIntelligence}
            legalProceedings={analysis.legalProceedingsIntelligence}
            t={t}
          />

          {/* Atlas Intelligence Sprint 7 (Monitoring & Change Detection,
              Deliverable 13). Deliberately one compact line, not a section
              -- reuses Evidence Timeline/Materiality above for the full
              picture; this only reprioritizes/frames it. `latestChangeReason`
              is a server-generated English sentence (matching how every
              other `daily_brief_agenda` signal reason already works, since
              it can carry verbatim investor-authored CaseCondition
              predicate text that cannot be translated) -- deliberately not
              shown here, where the rest of the page is fully translated;
              the status badge alone is enough for a compact line, and the
              same reason already surfaces, in full, on the Daily Brief
              agenda item. */}
          {analysis.monitoring && (
            <Inline gap="metadata" align="center">
              <StatusBadge
                label={t(MONITORING_STATUS_KEY[analysis.monitoring.status])}
                tone={MONITORING_STATUS_TONE[analysis.monitoring.status]}
              />
            </Inline>
          )}

          {/* Atlas Intelligence Sprint 8/9 (Automated Monitoring Operations
              / Data Ingestion & Automatic Refresh, Deliverable 15/6/7).
              Deliberately a separate line from the Monitoring status badge
              above -- operational freshness ("has Atlas recomputed this
              recently, and did new data even arrive") is never mixed with
              investment status ("what did Atlas conclude"). */}
          {analysis.operationalFreshness && (
            <StatusBadge
              label={t(DATA_FRESHNESS_STATUS_KEY[analysis.operationalFreshness.dataFreshnessStatus])}
              tone={DATA_FRESHNESS_STATUS_TONE[analysis.operationalFreshness.dataFreshnessStatus]}
            />
          )}

          <Divider tone="hairline" />

          <CompanyHealthAssessmentSection cards={companyHealthCards} t={t} />

          <Divider tone="hairline" />

          <InterpretedFinancialEvidenceSection financialHistory={analysis.financialHistory} t={t} locale={locale} />

          <Divider tone="hairline" />

          <CompanyOverviewSection companyProfile={analysis.companyProfile} marketSnapshot={analysis.marketSnapshot} t={t} locale={locale} />
        </Stack>
      </ExpandableDetail>
    </Stack>
  );
}

/**
 * Business -- Portfolio Context (new subsection: the fuller, uncapped
 * version of Executive Summary's compact Portfolio Impact facts --
 * "Details on Demand" applied literally. The summary shows at most one
 * concentration-relevance fact; this always shows the holding's own
 * weight, the portfolio's actual largest position (by ticker and
 * weight, not just a yes/no flag), concentration level, and cash
 * exposure -- the full picture the summary line only gestures at), then
 * Growth/Capital Allocation highlighted, then the remaining four
 * business categories.
 */
/**
 * Company Overview + Financials (Investment Case Engine v1 slice;
 * extended Company Data Foundation v1) -- the automatically-populated
 * Company Identity, Financial History, and current Market Data this
 * sprint adds. Renders only real, already-ingested `BusinessRecord`
 * data (see `atlas/alpha/investment_case/company_profile.py`/
 * `financial_history.py`); a company with nothing ingested yet shows
 * the same honest empty state doctrine already established elsewhere
 * on this page, never a fabricated placeholder. A missing value is
 * always the em-dash placeholder below, never rendered as 0 or blank
 * (which would visually imply zero).
 *
 * `FinancialsTable` and its formatting helpers now live in
 * `../investmentCase/FinancialsTable` (Workspace Migration, Foundation
 * extraction), imported above.
 */

/**
 * Company Overview (Figma-fidelity rebuild) -- identity fields and
 * current market snapshot only; Financials moved into its own
 * `FinancialsSection`, paired with `ValuationScenariosSection`
 * (matching the approved screen's own Financials | Valuation Scenarios
 * two-column layout, distinct from this Company Overview | Business
 * Analysis pairing). Founded/CEO/Employees are shown on the approved
 * screen but have no real source anywhere in this codebase (no such
 * fields exist on `CompanyProfileView`) -- each renders the literal
 * "—" every other missing value on this page already uses, never a
 * fabricated fact.
 */
function CompanyOverviewSection({
  companyProfile,
  marketSnapshot,
  t,
  locale,
}: {
  companyProfile: CompanyProfileView | null;
  marketSnapshot: MarketSnapshotView | null;
  t: Translate;
  locale: string;
}) {
  const hasAnyData = companyProfile !== null || marketSnapshot !== null;
  const notAvailable = t("investmentCase.atlasView.notAvailable");

  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.analysis.companyOverview.heading")}</Label>
      {!hasAnyData && <StatusText label={t("investmentCase.analysis.companyOverview.empty")} />}
      {companyProfile && (
        <Stack gap="metadata">
          <Inline gap="inter-section" wrap>
            <Text as="p">
              <Text as="span" color="tertiary">
                {t("investmentCase.analysis.companyOverview.foundedLabel")}:{" "}
              </Text>
              {notAvailable}
            </Text>
            <Text as="p">
              <Text as="span" color="tertiary">
                {t("investmentCase.analysis.companyOverview.employeesLabel")}:{" "}
              </Text>
              {notAvailable}
            </Text>
          </Inline>
          <Inline gap="inter-section" wrap>
            <Text as="p">
              <Text as="span" color="tertiary">
                {t("investmentCase.analysis.companyOverview.ceoLabel")}:{" "}
              </Text>
              {notAvailable}
            </Text>
            {companyProfile.country && (
              <Text as="p">
                <Text as="span" color="tertiary">
                  {t("investmentCase.analysis.companyOverview.countryLabel")}:{" "}
                </Text>
                {companyProfile.country}
              </Text>
            )}
          </Inline>
          {companyProfile.fiscalYearEnd && (
            <Text as="p" color="tertiary">
              {t("investmentCase.analysis.companyOverview.fiscalYearEndLabel")}: {companyProfile.fiscalYearEnd}
            </Text>
          )}
          {companyProfile.description && (
            <Text color="secondary" as="p">
              {companyProfile.description}
            </Text>
          )}
        </Stack>
      )}

      {marketSnapshot && (
        <Stack gap="metadata">
          <Divider tone="hairline" />
          <Label>{t("investmentCase.analysis.financials.marketSnapshotHeading")}</Label>
          <Inline gap="inter-section" wrap style={{ fontVariantNumeric: "tabular-nums" }}>
            <Text as="p">
              <Text as="span" color="tertiary">
                {t("investmentCase.analysis.financials.sharePriceLabel")}:{" "}
              </Text>
              {formatFinancialValue(marketSnapshot.sharePrice, marketSnapshot.currency, locale)}
            </Text>
            <Text as="p">
              <Text as="span" color="tertiary">
                {t("investmentCase.analysis.financials.sharesOutstandingLabel")}:{" "}
              </Text>
              {formatShareCount(marketSnapshot.sharesOutstanding, locale)}
            </Text>
            <Text as="p">
              <Text as="span" color="tertiary">
                {t("investmentCase.analysis.financials.marketCapLabel")}:{" "}
              </Text>
              {formatFinancialValue(marketSnapshot.marketCap, marketSnapshot.currency, locale)}
            </Text>
          </Inline>
        </Stack>
      )}
    </Stack>
  );
}

/** The three `OpenQuestionKind` members that are specifically about
 * missing evidence -- a presentational split of the one existing
 * `analysis.openQuestions` list, not a new domain concept: the backend
 * already defines exactly these six kinds. */
const EVIDENCE_GAP_QUESTION_KINDS: OpenQuestionKind[] = [
  "no_evidence_recorded_for_case",
  "observation_without_evidence",
  "decision_without_linked_observation",
];

/**
 * Evidence (Figma-fidelity rebuild) -- the approved screen's own
 * compact single row: Coverage / Missing / Latest, plus a "View all
 * evidence" link into the More Details tab (where `EvidenceDetailSection`
 * below lives).
 *
 * UX Refinement Sprint (F-04) correction: this row previously showed
 * both `analysis.confidence` (as "Quality") and
 * `analysis.evidenceQuality.coverage` (as "Coverage") side by side, on
 * the assumption below that they were "two distinct real fields." They
 * are not -- traced to source in `atlas/analysis_engine/pipeline.py`'s
 * `assemble_analysis`: `confidence = decision_output.business_evaluation
 * .evidence_quality.coverage`, and `CanonicalAnalysis.business` is
 * `decision_output.business_evaluation` verbatim, so `analysis.confidence`
 * IS `analysis.evidenceQuality.coverage`, always, by construction --
 * exactly the "single fact split into two labels" this comment
 * previously claimed did not apply here. Now shown once, under
 * "Coverage." Missing reuses the same `EVIDENCE_GAP_QUESTION_KINDS`-
 * filtered count `EvidenceDetailSection` computes in full below. Latest
 * reads `currentThesis.latestDecisionReason`/`latestObservationStatement`
 * -- the same real "most recent investor input" fact already used
 * elsewhere on this page, never a fabricated activity summary.
 */
function EvidenceSection({
  analysis,
  linkedHolding,
  onViewMoreDetails,
  t,
}: {
  analysis: InvestmentCaseAnalysisView;
  linkedHolding: AlphaHoldingView | null;
  onViewMoreDetails: () => void;
  t: Translate;
}) {
  const missingCount = analysis.openQuestions.filter((q) => EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind)).length;
  const latest = analysis.currentThesis.latestDecisionReason ?? analysis.currentThesis.latestObservationStatement;

  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.analysis.evidence.heading")}</Label>
      <Inline gap="inter-section" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" wrap>
          <Text as="span" color="secondary">
            {t("investmentCase.analysis.evidence.coverageLabel")}: {t(CONFIDENCE_KEY[analysis.confidence])}
          </Text>
          <Text as="span" color="secondary">
            {t("investmentCase.analysis.evidence.missingEvidenceHeading")}: {missingCount}
          </Text>
          {latest && (
            <Text as="span" color="secondary">
              {t("investmentCase.analysis.evidence.latestLabel")}: {latest}
            </Text>
          )}
        </Inline>
        {linkedHolding && (
          <Link
            href="#"
            style={ACCENT_LINK_STYLE}
            onClick={(event) => {
              event.preventDefault();
              onViewMoreDetails();
            }}
          >
            {t("investmentCase.analysis.evidence.viewAll")}
          </Link>
        )}
      </Inline>
    </Stack>
  );
}


const GROWTH_TREND_KEY: Record<AnalysisMetricTrend, TranslationKey> = {
  strong_metric: "investmentCase.atlasView.growth.trend.strong_metric",
  weak_metric: "investmentCase.atlasView.growth.trend.weak_metric",
  mixed_metric: "investmentCase.atlasView.growth.trend.mixed_metric",
};

/**
 * Product Sprint 7 (Investment Case Excellence, Deliverable 2 -- Remove
 * Noise) -- this section used to restate Thesis/Strengths/Risks/Growth
 * status/Valuation Context in full, every one of them a second (or
 * third) rendering of a fact the always-visible view above the tab bar
 * already states: Strengths/Risks in full sentence form live in
 * `InvestmentArgumentSection`; Growth's own status lives in
 * `AtlasReasoningSection`'s Growth card; Valuation's status/current
 * yield/scenario-availability are the exact same three facts
 * `ValuationDetailSection` (this same tab, immediately below) already
 * renders. The bare "Thesis" heading rendered no content under it at
 * all (`atlasThesis.narrative` was deliberately never shown -- see the
 * removed comment that used to sit here). Open Questions moved out of
 * this tab entirely in Deliverable 4 -- it is now its own always-visible
 * column in `InvestmentArgumentSection`, next to Bull/Bear, so rendering
 * it here too would be exactly the duplication this deliverable removes.
 * What's left below is only what remains genuinely unique to this
 * section: Growth's own recent-trend detail (periods considered + trend
 * direction), not shown anywhere else.
 */
function CaseNarrativeDetailSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  const { growthAnalysis } = analysis;

  if (!growthAnalysis.recentTrend) {
    return null;
  }

  return (
    <Stack gap="intra-section">
      <Heading level={3}>{t("investmentCase.atlasView.growth.heading")}</Heading>
      <Text as="p" color="secondary">
        {t("investmentCase.atlasView.growth.recentTrendLabel", {
          periods: growthAnalysis.recentTrend.periodsConsidered.join(" → "),
        })}
        : {t(GROWTH_TREND_KEY[growthAnalysis.recentTrend.trend])}
      </Text>
    </Stack>
  );
}

// CHANGE_DIRECTION_SYMBOL/THESIS_IMPACT_KEY/dimensionLabel/
// describeChange now live in "../changeIntelligence/describeChange"
// (imported above) -- shared with History v1.


/**
 * Portfolio Context (Figma-fidelity rebuild) -- the former Business
 * Analysis subsection (holding weight / largest position / concentration
 * / cash), relocated into the More Details tab. The approved screen's
 * own compact header stat row already carries the holding's own weight
 * ("In your portfolio · current allocation: X%"), and the rest
 * (largest position, concentration, cash) is genuinely Portfolio-level
 * context, not shown anywhere on the approved Investment Case screen --
 * real data, real depth one tab away, not fabricated or deleted.
 */
function PortfolioContextDetail({
  linkedHolding,
  alphaPortfolioStatus,
  t,
}: {
  linkedHolding: AlphaHoldingView;
  alphaPortfolioStatus: AlphaPortfolioStatus;
  t: Translate;
}) {
  const holdings = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.holdings : [];
  const largestHolding = holdings.reduce<AlphaHoldingView | null>(
    (max, h) => (max === null || h.weightPercent > max.weightPercent ? h : max),
    null,
  );
  const cashWeightPercent = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.cashWeightPercent : null;
  const concentrationLevel =
    alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.concentrationLevel : null;

  return (
    <Stack gap="intra-section">
      <Heading level={3}>{t("investmentCase.analysis.business.portfolioContextHeading")}</Heading>
      <Text as="p">
        {t("investmentCase.executiveSummary.portfolioImpact.weight", {
          percent: linkedHolding.weightPercent.toFixed(1),
        })}
      </Text>
      {largestHolding && (
        <Text as="p">
          {t("investmentCase.analysis.business.largestPositionLabel", {
            ticker: largestHolding.ticker,
            percent: largestHolding.weightPercent.toFixed(1),
          })}
        </Text>
      )}
      {concentrationLevel && (
        <Text as="p">
          {t("portfolio.concentration", {
            value: CASE_CONCENTRATION_LEVEL_KEY[concentrationLevel]
              ? t(CASE_CONCENTRATION_LEVEL_KEY[concentrationLevel]!)
              : concentrationLevel,
          })}
        </Text>
      )}
      {cashWeightPercent !== null && (
        <Text as="p">
          {t("investmentCase.executiveSummary.portfolioImpact.cash", { percent: cashWeightPercent.toFixed(1) })}
        </Text>
      )}
    </Stack>
  );
}

/** Valuation -- unchanged content from Phase 1's canonical sections,
 * extracted into its own component for this sprint's four-section
 * structure. FCF Yield named explicitly; the three scenario methods
 * shown honestly as not yet available, never fabricated bear/base/bull
 * assumptions. */
function ValuationDetailSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  const fcfYield = analysis.valuation.findings.find((f) => f.kind === "fcf_yield_relative");
  const scenarioFindings = analysis.valuation.findings.filter((f) => f.kind !== "fcf_yield_relative");

  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.analysis.valuation.heading")}</Label>
      {fcfYield && (
        <Stack gap="metadata">
          <Text as="p">
            {t("investmentCase.analysis.valuation.method.fcf_yield_relative")}:{" "}
            {t(VALUATION_STATUS_KEY[fcfYield.status])}
          </Text>
          {fcfYield.currentYield != null && (
            <Text color="secondary" as="p">
              {t("investmentCase.analysis.valuation.currentYieldLabel")}: {(fcfYield.currentYield * 100).toFixed(1)}%
            </Text>
          )}
          {/* Product Sprint 13 (Company Intelligence Excellence):
              see `isReadableFact`'s own doc comment -- this field
              sometimes holds raw, unresolved evidence-reference ids.
              Product Sprint 14: `capFacts` keeps a fully-resolved,
              many-observation finding (e.g. FCF Yield, evaluated
              across a full price/share-count history) readable. */}
          {capFacts(fcfYield.supportingFacts.filter(isReadableFact)).length > 0 && (
            <Text color="secondary" as="p">
              {t("investmentCase.analysis.business.supportingLabel")}:{" "}
              {capFacts(fcfYield.supportingFacts.filter(isReadableFact)).join(", ")}
            </Text>
          )}
          {fcfYield.missingEvidence.length > 0 && (
            <Text color="secondary" as="p">
              {t("investmentCase.analysis.business.missingLabel")}:{" "}
              {fcfYield.missingEvidence.map((v) => describeGapKind(v, VALUATION_DATA_GAP_KEY, t)).join(", ")}
            </Text>
          )}
        </Stack>
      )}
      {scenarioFindings.length > 0 && (
        <Stack gap="metadata">
          <Text as="p" color="tertiary">
            {t("investmentCase.analysis.valuation.scenarioHeading")}
          </Text>
          <Text color="secondary" as="p">
            {t("investmentCase.analysis.valuation.scenarioNote")}
          </Text>
        </Stack>
      )}
    </Stack>
  );
}

/** Risk -- unchanged content from Phase 1's canonical sections, extracted
 * into its own component. The full four-category vector, each shown
 * independently -- no aggregate, no hidden total. */
function RiskSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.analysis.risk.heading")}</Label>
      <Text color="tertiary" as="p">
        {t("investmentCase.analysis.risk.subheading")}
      </Text>
      {/* Product Sprint 11 (Investment Workflow Excellence, Deliverable
          10 -- Page Density): this rendered one full-width row per
          finding regardless of viewport width, unlike its sibling
          `AtlasReasoningSection` a few sections above -- the same shape
          of data (a handful of short status findings) already reflows
          into a wrapping row there. Matches that exact pattern rather
          than inventing a new one; no information removed, only
          reflowed. */}
      <Inline gap="inter-section" wrap align="start">
        {analysis.risk.findings.map((finding) => {
          // Product Sprint 13 (Company Intelligence Excellence):
          // live-testing found `supportingFacts`/`contradictingFacts`
          // sometimes hold raw, unresolved evidence-reference ids
          // (e.g. `21ea5c...:v1:free_cash_flow:2017-06-30`) rather
          // than prose -- see `isReadableFact`'s own doc comment.
          // Product Sprint 14: `capFacts` keeps a fully-resolved,
          // many-observation finding readable.
          const supportingFacts = capFacts(finding.supportingFacts.filter(isReadableFact));
          const contradictingFacts = capFacts(finding.contradictingFacts.filter(isReadableFact));
          return (
            <Stack key={finding.category} gap="metadata" style={{ flex: "1 1 280px", minWidth: 0 }}>
              <Text as="p">
                {t(RISK_CATEGORY_KEY[finding.category])}: {t(RISK_STATUS_KEY[finding.status])}
              </Text>
              {supportingFacts.length > 0 && (
                <Text color="tertiary" as="p">
                  {t("investmentCase.analysis.business.supportingLabel")}: {supportingFacts.join(", ")}
                </Text>
              )}
              {contradictingFacts.length > 0 && (
                <Text color="tertiary" as="p">
                  {t("investmentCase.analysis.business.contradictingLabel")}: {contradictingFacts.join(", ")}
                </Text>
              )}
              {finding.missingEvidence.length > 0 && (
                <Text color="tertiary" as="p">
                  {t("investmentCase.analysis.business.missingLabel")}:{" "}
                  {finding.missingEvidence.map((v) => describeGapKind(v, RISK_DATA_GAP_KEY, t)).join(", ")}
                </Text>
              )}
            </Stack>
          );
        })}
      </Inline>
    </Stack>
  );
}

/**
 * Evidence Detail (Figma-fidelity rebuild) -- "everything Atlas knows,
 * and what it still doesn't," in one place: Current Thesis, Conviction,
 * and Confidence, Evidence Quality, Observations, Missing Evidence and
 * Open Questions (`analysis.openQuestions` split by
 * `EVIDENCE_GAP_QUESTION_KINDS`). Moved from the primary view into the
 * More Details tab -- the compact `EvidenceSection` above is what the
 * approved screen actually shows there; this is the real depth its own
 * "View all evidence" link leads to.
 */
function EvidenceDetailSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  const hasThesis = analysis.currentThesis.latestDecisionReason || analysis.currentThesis.latestObservationStatement;
  const missingEvidenceQuestions = analysis.openQuestions.filter((q) => EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind));
  const otherOpenQuestions = analysis.openQuestions.filter((q) => !EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind));

  return (
      <Stack gap="intra-section">
        <Label>{t("investmentCase.analysis.evidence.heading")}</Label>

        {/* Current Thesis -- investor-provided only; Atlas never
            fabricates a thesis narrative of its own. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.thesis.heading")}</Heading>
          {!hasThesis && <Text color="secondary">{t("investmentCase.analysis.thesis.none")}</Text>}
          {analysis.currentThesis.latestDecisionReason && (
            <Stack gap="intra-section">
              <Text color="secondary">{t("investmentCase.analysis.thesis.investorDecisionReason")}</Text>
              <Text as="p">{analysis.currentThesis.latestDecisionReason}</Text>
            </Stack>
          )}
          {analysis.currentThesis.latestObservationStatement && (
            <Stack gap="intra-section">
              <Text color="secondary">{t("investmentCase.analysis.thesis.investorObservation")}</Text>
              <Text as="p">{analysis.currentThesis.latestObservationStatement}</Text>
            </Stack>
          )}
          {analysis.isThesisStale && <Text color="tertiary">{t("investmentCase.analysis.thesis.stale")}</Text>}
        </Stack>

        <Divider tone="hairline" />

        {/* Conviction -- reused directly, never recomputed. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.conviction.heading")}</Heading>
          <Text>{t(CONVICTION_LEVEL_KEY[analysis.conviction.level])}</Text>
          {analysis.conviction.reasons.length > 0 && (
            <Stack gap="intra-section">
              <Text color="secondary">{t("investmentCase.analysis.conviction.reasonsHeading")}</Text>
              {analysis.conviction.reasons.map((reason) => (
                <Text key={reason} color="secondary" as="p">
                  {describeGapKind(reason, CONVICTION_REASON_KEY, t)}
                </Text>
              ))}
            </Stack>
          )}
        </Stack>

        <Divider tone="hairline" />

        {/* Confidence -- kept visually distinct from Conviction. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.confidence.heading")}</Heading>
          <Text>{t(CONFIDENCE_KEY[analysis.confidence])}</Text>
          <Text color="secondary" as="p">
            {t("investmentCase.analysis.confidence.explanation")}
          </Text>
        </Stack>

        <Divider tone="hairline" />

        {/* Evidence Quality -- the Observation/Evidence composition behind
            the Confidence level shown above (never restated here -- see
            UX Refinement Sprint F-04: `analysis.confidence` and
            `analysis.evidenceQuality.coverage` are the same value by
            construction, see `assemble_analysis` in
            `atlas/analysis_engine/pipeline.py`), distinct from each
            finding's own supporting/contradicting facts already shown
            inline in Business/Valuation/Risk above. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.evidence.qualityHeading")}</Heading>
          {!analysis.evidenceQuality && (
            <Text color="secondary">{t("investmentCase.analysis.evidence.noneRecorded")}</Text>
          )}
          {analysis.evidenceQuality && (
            <Stack gap="intra-section">
              <Text color="secondary" as="p">
                {t(
                  analysis.evidenceQuality.supportingEvidenceCount === 1
                    ? "investmentCase.analysis.evidence.supportingCountOne"
                    : "investmentCase.analysis.evidence.supportingCountOther",
                  { count: analysis.evidenceQuality.supportingEvidenceCount },
                )}
              </Text>
              {analysis.evidenceQuality.challengingEvidenceCount > 0 && (
                <Text color="tertiary" as="p">
                  {t(
                    analysis.evidenceQuality.challengingEvidenceCount === 1
                      ? "investmentCase.analysis.evidence.challengingCountOne"
                      : "investmentCase.analysis.evidence.challengingCountOther",
                    { count: analysis.evidenceQuality.challengingEvidenceCount },
                  )}
                </Text>
              )}
            </Stack>
          )}
        </Stack>

        <Divider tone="hairline" />

        {/* Observations -- moved from the former standalone "Investor
            Observations" card; optional context, never a prerequisite
            for the analysis above. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.observations.heading")}</Heading>
          {analysis.observationHistory.length === 0 && (
            <Text color="secondary">{t("investmentCase.analysis.observations.empty")}</Text>
          )}
          {analysis.observationHistory.map((entry) => (
            <Stack key={entry.observationId} gap="intra-section">
              <Text as="p">{entry.statement}</Text>
              <Text color="tertiary" as="p">
                {formatRelativeTime(entry.observedAt, t)}
              </Text>
              <Divider tone="hairline" />
            </Stack>
          ))}
        </Stack>

        {missingEvidenceQuestions.length > 0 && (
          <>
            <Divider tone="hairline" />
            <Stack gap="intra-section">
              <Heading level={3}>{t("investmentCase.analysis.evidence.missingEvidenceHeading")}</Heading>
              {missingEvidenceQuestions.map((question, index) => (
                <Text key={index} color="secondary" as="p">
                  {t(OPEN_QUESTION_KEY[question.kind])}
                </Text>
              ))}
            </Stack>
          </>
        )}

        {otherOpenQuestions.length > 0 && (
          <>
            <Divider tone="hairline" />
            <Stack gap="intra-section">
              <Heading level={3}>{t("investmentCase.intelligence.openQuestions.heading")}</Heading>
              {otherOpenQuestions.map((question, index) => (
                <Text key={index} color="secondary" as="p">
                  {t(OPEN_QUESTION_KEY[question.kind])}
                </Text>
              ))}
            </Stack>
          </>
        )}

      </Stack>
  );
}
