import { useEffect, useRef, useState } from "react";
import { Link as RouterLink, useLocation, useParams } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Stack, Surface, Text } from "../foundation";
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
  deriveAssessmentPoints,
  deriveCaseDiscussionKind,
  deriveCaseStatus,
  deriveCurrentPriority,
  deriveOutstandingIssues,
  findMostSevereRisk,
  type AssessmentPoint,
  type CaseDiscussionKind,
  type CaseStatusLevel,
  type CurrentPriorityKind,
  type OutstandingIssueKind,
  type OutstandingWorkKind,
} from "../investmentCase/deriveExecutiveSummary";

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
) {
  setDeleteStatus((current) => ({ ...current, [id]: "deleting" }));

  fetch(url, { method: "DELETE" })
    .then((response) => {
      if (!response.ok && response.status !== 404) {
        throw new Error(`Backend responded with ${response.status}`);
      }
      setRecords((current) => current.filter((record) => !matchesId(record)));
      setDeleteStatus((current) => ({ ...current, [id]: "idle" }));
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

/**
 * Atlas Alpha has no login/session/identity system anywhere in this
 * frontend. The real backend's `Decision.user_id` is required, but per
 * the governing (unimplemented) Decision-Implementation-Design.md, it
 * "has no future semantic role" and is retained only as legacy
 * compatibility metadata — never shown to the investor. This fixed,
 * documented placeholder is used until Atlas Alpha has a real identity
 * system; it is not real user data, and no authentication is added.
 */
const ALPHA_PLACEHOLDER_USER_ID = "00000000-0000-0000-0000-000000000001";

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
type EvidenceCoverageLevel = "not_applicable" | "none" | "partial" | "full";

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

type AnalysisConvictionLevel = "very_high" | "high" | "moderate" | "low" | "insufficient_evidence";
type AnalysisValuationStatus = "not_evaluated" | "insufficient_input" | "undervalued" | "fairly_valued" | "expensive";
type AnalysisRiskCategory = "business_risk" | "financial_risk" | "valuation_risk" | "thesis_risk";
type AnalysisRiskStatus = "not_evaluated" | "insufficient_input" | "low" | "moderate" | "high";
type AnalysisBusinessCategory =
  | "business_model"
  | "competitive_position"
  | "management"
  | "capital_allocation"
  | "growth"
  | "durability";
type AnalysisBusinessStatus = "not_evaluated" | "insufficient_input" | "weak" | "moderate" | "strong";
type AnalysisRecommendationKind = "directional" | "recommendation_withheld";
type AnalysisRecommendationReason = "engine_not_implemented" | "evidence_insufficient";

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

interface RecommendationStateView {
  kind: AnalysisRecommendationKind;
  reason: AnalysisRecommendationReason;
  convictionGateMet: boolean;
}

interface InvestmentCaseAnalysisView {
  caseId: string;
  holdingContext: HoldingContextView;
  currentThesis: CurrentThesisView;
  isThesisStale: boolean;
  confidence: EvidenceCoverageLevel;
  conviction: { level: AnalysisConvictionLevel; reasons: string[] };
  businessAnalysis: { state: string; findings: BusinessFindingView[] };
  valuation: { state: string; findings: ValuationFindingView[] };
  risk: { state: string; findings: RiskFindingView[] };
  evidenceQuality: EvidenceQualityView | null;
  openQuestions: OpenQuestionView[];
  recommendation: RecommendationStateView;
  decisionHistory: DecisionHistoryEntryView[];
  observationHistory: ObservationEntryView[];
  outcomeHistory: OutcomeEntryView[];
  generatedAt: string;
}

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
  const { t } = useTranslation();
  const { caseId } = useParams<{ caseId?: string }>();
  const location = useLocation();
  const origin = (location.state as { origin?: string } | null)?.origin ?? null;
  const originLabelKey: TranslationKey | null =
    origin === "dashboard"
      ? "investmentCase.origin.dashboard"
      : origin === "portfolio"
        ? "investmentCase.origin.portfolio"
        : origin === "history"
          ? "investmentCase.origin.history"
          : origin === "daily-brief"
            ? "investmentCase.origin.dailyBrief"
            : origin === "discovery"
              ? "investmentCase.origin.discovery"
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
  const returnTo: string =
    origin === "dashboard"
      ? "/dashboard"
      : origin === "history"
        ? "/history"
        : origin === "daily-brief"
          ? "/daily-brief"
          : origin === "discovery"
            ? "/discovery"
            : "/portfolio";
  const returnLabelKey: TranslationKey =
    origin === "dashboard"
      ? "investmentCase.returnTo.dashboard"
      : origin === "history"
        ? "investmentCase.returnTo.history"
        : origin === "daily-brief"
          ? "investmentCase.returnTo.dailyBrief"
          : origin === "discovery"
            ? "investmentCase.returnTo.discovery"
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

  const [alphaPortfolioStatus, setAlphaPortfolioStatus] = useState<AlphaPortfolioStatus>({
    kind: "loading",
  });
  const [tradeLogStatus, setTradeLogStatus] = useState<TradeLogFetchStatus>({ kind: "loading" });
  const [pendingAction, setPendingAction] = useState<PositionAction | null>(null);
  const [investmentCaseAnalysis, setInvestmentCaseAnalysis] = useState<InvestmentCaseAnalysisFetchStatus>({
    kind: "loading",
  });

  /** Executive Summary "Discuss this Case" (Investment Case Workspace v2,
   * Sprint 2) -- UI only, same honest-placeholder pattern
   * `PortfolioPage.tsx`'s `TodaysDiscussionsCard` already established:
   * no conversation engine, just a pre-filled input and a static note. */
  const [askInput, setAskInput] = useState("");
  const [askSubmitted, setAskSubmitted] = useState(false);

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
  }, [caseId]);

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

    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<AlphaPortfolioView>;
      })
      .then((view) => setAlphaPortfolioStatus({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setAlphaPortfolioStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });

    return () => controller.abort();
  }, []);

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
  }, []);

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
    );
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

  function closeAction() {
    setPendingAction(null);
    setDecisionCreateStatus((current) => ({
      ...current,
      [CASE_LEVEL_DECISION_KEY]: { kind: "idle" },
    }));
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
    caseLevelDecisionStatus.kind === "success" ? caseLevelDecisionStatus.decision.id : null;
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

  return (
    <Container>
      <Stack gap="inter-section">
        {/* Header — company/security identity is the primary title; the
            Case id is secondary/technical only (never the primary
            identity). Ticker comes from the Alpha portfolio's
            holding-to-case link (`holding.caseId`) — Case itself carries
            no identity of its own (`atlas/core/domain/case/entity.py`). */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <RouterLink to={returnTo}>{t(returnLabelKey)}</RouterLink>
            {originLabelKey && <Text color="tertiary">{t(originLabelKey)}</Text>}
            <Heading level={1}>
              {linkedHolding ? linkedHolding.ticker : t("investmentCase.header.untitled")}
            </Heading>
            {linkedHolding && (
              <Text color="secondary">
                {t("investmentCase.header.inPortfolio")} ·{" "}
                {t("investmentCase.header.currentAllocation", {
                  percent: linkedHolding.weightPercent,
                })}
              </Text>
            )}
            {/* Status (Investment Case Workspace v2, Sprint 2) -- fills
                the slot `investmentCase.status.heading` has reserved
                since an early sprint ("draft, historical, and monitoring
                status indicators in a future commit"). One plain word,
                derived from already-computed workflow/thesis/evidence
                gaps -- see `deriveCaseStatus`'s own doc comment. */}
            {investmentCaseAnalysis.kind === "loaded" && (
              <Text as="p">
                {t("investmentCase.status.heading")}:{" "}
                {t(
                  CASE_STATUS_KEY[
                    deriveCaseStatus({
                      hasOutstandingWork: caseOutstandingWork.length > 0,
                      isThesisStale: investmentCaseAnalysis.report.isThesisStale,
                      openQuestionCount: investmentCaseAnalysis.report.openQuestions.length,
                      evidenceGap:
                        investmentCaseAnalysis.report.evidenceQuality !== null &&
                        (investmentCaseAnalysis.report.evidenceQuality.coverage === "none" ||
                          investmentCaseAnalysis.report.evidenceQuality.coverage === "partial"),
                    })
                  ],
                )}
              </Text>
            )}
            {!linkedHolding && caseId && (
              <Text color="secondary">{t("investmentCase.header.notLinked")}</Text>
            )}
            {!caseId && <Text color="secondary">{t("investmentCase.noCaseSelected")}</Text>}
            {caseId && status.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {caseId && status.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("investmentCase.loadError", { message: status.message })}
              </Text>
            )}
            {caseId && status.kind === "loaded" && (
              <Text color="tertiary">
                {t("investmentCase.header.caseIdLabel", { caseId: status.case.caseId })}
              </Text>
            )}
          </Stack>
        </Surface>

        {caseId && status.kind === "loaded" && (
          <>
            {/* Executive Summary (Investment Case Workspace v2, Sprint 2)
                -- the whole "understand in ~10 seconds, no scrolling"
                section: Atlas Assessment, Current Priority, Portfolio
                Impact, Outstanding Issues, Discuss this Case. Renders
                only once the analysis has loaded; a fetch failure or
                still-loading state never blocks the rest of the page
                (same independent-fetch pattern every other section here
                already uses). Everything from the canonical analysis
                sections onward, below, is unchanged from before this
                sprint. */}
            {investmentCaseAnalysis.kind === "loaded" && (
              <ExecutiveSummaryCard
                analysis={investmentCaseAnalysis.report}
                linkedHolding={linkedHolding}
                alphaPortfolioStatus={alphaPortfolioStatus}
                outstandingWorkKinds={caseOutstandingWork.map((item) => item.kind)}
                askInput={askInput}
                setAskInput={setAskInput}
                askSubmitted={askSubmitted}
                setAskSubmitted={setAskSubmitted}
                t={t}
              />
            )}

            <Divider />

            {/* Canonical analysis -- Business / Valuation / Risk / Evidence
                (Investment Case Workspace v2, Sprint 2, Phase 2): the
                "explain the summary" workspace. Straight from
                `GET /api/cases/{caseId}/analysis`, plus the same
                already-fetched Alpha portfolio data Executive Summary
                uses (for Business's Portfolio Context subsection).
                Renders only once loaded; a fetch failure never blocks
                the rest of the page (same independent-fetch pattern
                every other section here already uses). */}
            {investmentCaseAnalysis.kind === "loaded" && (
              <InvestmentCaseCanonicalSections
                analysis={investmentCaseAnalysis.report}
                linkedHolding={linkedHolding}
                alphaPortfolioStatus={alphaPortfolioStatus}
                t={t}
              />
            )}

            <Divider />

            {/* Last activity (Sprint 4) — factual continuity only: the
                most recent Decision, Outcome, and Trade this Case has,
                each with a relative-time phrase computed from its own
                real timestamp, plus the linked holding's current
                reconciliation status. No AI interpretation, no
                recommendation — see `deriveActivity`. */}
            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>{t("investmentCase.lastActivity.heading")}</Heading>
                {!lastDecisionEvent && !lastOutcomeEvent && !lastTradeEvent && (
                  <Text color="secondary">{t("investmentCase.lastActivity.noneYet")}</Text>
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
            </Surface>

            <Divider />

            {/* Decision Timeline (Sprint 4) — a simple, entirely
                chronological presentation of this Case's own Decision/
                Outcome/Trade events (`deriveActivity`, oldest first, no
                advanced visualization), ending with the current status
                already computed above (`assessmentStatusKey`) rather
                than a duplicated, possibly-inconsistent summary. */}
            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>{t("investmentCase.timeline.heading")}</Heading>
                {caseTimeline.length === 0 && (
                  <Text color="secondary">{t("investmentCase.timeline.empty")}</Text>
                )}
                {caseTimeline.map((event) => (
                  <div key={event.id}>
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
                  </div>
                ))}
                {caseTimeline.length > 0 && (
                  <div>
                    <Text color="secondary">{t("investmentCase.timeline.currentStatus")}</Text>
                    <Text as="p">{t(assessmentStatusKey)}</Text>
                  </div>
                )}
              </Stack>
            </Surface>

            <Divider />

            {/* Outstanding work (Sprint 4) — deterministic state checks
                only (`deriveOutstandingWork`): no scoring, no AI, no
                recommendation. Reconciliation is already covered by the
                Last activity section above, so only the two
                Decision/Outcome-chain checks are shown here to avoid
                repeating the same fact twice. */}
            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>{t("investmentCase.outstandingWork.heading")}</Heading>
                {caseOutstandingWork.filter((item) => item.kind !== "reconciliation-needed").length ===
                  0 && <Text color="secondary">{t("investmentCase.outstandingWork.none")}</Text>}
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
            </Surface>

            <Divider />

            {/* More details — every existing Observation/Evidence/
                Knowledge Reference/Reasoning Trace/Judgment/Decision/
                Outcome record remains fully accessible for Alpha
                inspection and debugging, exactly as before — just
                collapsed by default and visually secondary. A native
                <details> element needs no new state and no new
                Foundation component. */}
            <Surface tier="primary">
              <details>
                <summary>{t("investmentCase.moreDetails.heading")}</summary>
                <Stack gap="inter-section">
                  <Text color="secondary">{t("investmentCase.moreDetails.subheading")}</Text>

                  {caseId && (
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
                            {observation.observedAt}
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
                                        {knowledgeReference.recordedAt}
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
                                        {reasoningTrace.recordedAt}
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
                                        {judgment.recordedAt}
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
                                        {decision.decidedAt}
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
            )}
          </Stack>
              </details>
            </Surface>

            <Divider />

            {/* Decision area — only actions truthful for this security's
                current state. Alpha wires Portfolio holdings only;
                Watchlist and Discovery are explicitly deferred (neither
                exists yet in this application). "Trim" and "Remove" both
                record a SELL Decision (see `ACTION_DECISION_TYPE`
                above); "Leave as is" records a HOLD and never asks for a
                transaction, since none occurred. */}
            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>{t("investmentCase.actions.heading")}</Heading>

                {!linkedHolding && (
                  <Text color="secondary">{t("investmentCase.actions.notLinkedNote")}</Text>
                )}

                {linkedHolding && caseLevelDecisionStatus.kind === "idle" && (
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
                    </Button>
                  </div>
                )}

                {linkedHolding &&
                  pendingAction &&
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

                {linkedHolding && caseLevelDecisionStatus.kind === "success" && (
                  <Stack gap="inter-section">
                    <Text>
                      {t("investmentCase.decision.recorded", {
                        decisionType: DECISION_TYPE_KEY[caseLevelDecisionStatus.decision.decisionType]
                          ? t(DECISION_TYPE_KEY[caseLevelDecisionStatus.decision.decisionType]!)
                          : caseLevelDecisionStatus.decision.decisionType,
                        subject: caseLevelDecisionStatus.decision.subject,
                      })}
                    </Text>

                    {pendingAction === "LEAVE_AS_IS" && (
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

                    {/* Decision-completion continuation (Sprint 8 audit
                        fix #5): a bare "Close" left the investor with no
                        stated next step right after finishing the one
                        thing this page exists for. The origin-aware
                        return link (same computed value as the header's
                        own return link) is always offered; "Open
                        History" is added only once a trade has actually
                        been reported, since that's the moment the full
                        Decision → Outcome → Trade loop completes and
                        seeing it reflected in the permanent record
                        becomes the natural next step. Close remains, for
                        an investor who wants to take another action on
                        this same Case without leaving the page. */}
                    <div>
                      {reportOutcomeStatus.kind === "success" && (
                        <>
                          <RouterLink to="/history">
                            {t("investmentCase.actions.openHistory")}
                          </RouterLink>{" "}
                        </>
                      )}
                      <RouterLink to={returnTo}>{t(returnLabelKey)}</RouterLink>{" "}
                      <Button variant="tertiary" onClick={closeAction}>
                        {t("investmentCase.actions.close")}
                      </Button>
                    </div>
                  </Stack>
                )}
              </Stack>
            </Surface>

            <Divider />

            {/* Continuity footer — worded so the application never claims
                active intelligence that isn't implemented yet. */}
            <Surface tier="primary">
              <Stack gap="inter-section">
                <Text color="secondary">{t("investmentCase.continuity.line1")}</Text>
                <Text color="secondary">{t("investmentCase.continuity.line2")}</Text>
              </Stack>
            </Surface>
          </>
        )}
      </Stack>
    </Container>
  );
}

const CONFIDENCE_KEY: Record<EvidenceCoverageLevel, TranslationKey> = {
  not_applicable: "portfolio.intelligence.confidence.not_applicable",
  none: "portfolio.intelligence.confidence.none",
  partial: "portfolio.intelligence.confidence.partial",
  full: "portfolio.intelligence.confidence.full",
};

const OPEN_QUESTION_KEY: Record<OpenQuestionKind, TranslationKey> = {
  no_evidence_recorded_for_case: "investmentCase.intelligence.openQuestions.noEvidenceRecordedForCase",
  observation_without_evidence: "investmentCase.intelligence.openQuestions.observationWithoutEvidence",
  decision_without_linked_observation:
    "investmentCase.intelligence.openQuestions.decisionWithoutLinkedObservation",
  business_durability_not_assessable: "investmentCase.intelligence.openQuestions.businessDurabilityNotAssessable",
  valuation_thesis_not_documented: "investmentCase.intelligence.openQuestions.valuationThesisNotDocumented",
  portfolio_factor_not_assessable: "investmentCase.intelligence.openQuestions.portfolioFactorNotAssessable",
};

/**
 * Reused verbatim from `PortfolioPage.tsx`'s own enum-value maps
 * (ATLAS-028) -- Portfolio Cockpit and Investment Case read the same
 * `CanonicalAnalysis`, so the Conviction/Valuation/Risk/Business
 * vocabularies must be identical (Phase 47's own cross-surface
 * consistency rule), not just similarly worded.
 */
const CONVICTION_LEVEL_KEY: Record<AnalysisConvictionLevel, TranslationKey> = {
  very_high: "portfolio.cockpit.conviction.very_high",
  high: "portfolio.cockpit.conviction.high",
  moderate: "portfolio.cockpit.conviction.moderate",
  low: "portfolio.cockpit.conviction.low",
  insufficient_evidence: "portfolio.cockpit.conviction.insufficient_evidence",
};

const VALUATION_STATUS_KEY: Record<AnalysisValuationStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.valuation.not_evaluated",
  insufficient_input: "portfolio.cockpit.valuation.insufficient_input",
  undervalued: "portfolio.cockpit.valuation.undervalued",
  fairly_valued: "portfolio.cockpit.valuation.fairly_valued",
  expensive: "portfolio.cockpit.valuation.expensive",
};

const RISK_STATUS_KEY: Record<AnalysisRiskStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.risk.status.not_evaluated",
  insufficient_input: "portfolio.cockpit.risk.status.insufficient_input",
  low: "portfolio.cockpit.risk.status.low",
  moderate: "portfolio.cockpit.risk.status.moderate",
  high: "portfolio.cockpit.risk.status.high",
};

const RISK_CATEGORY_KEY: Record<AnalysisRiskCategory, TranslationKey> = {
  business_risk: "portfolio.cockpit.risk.category.business_risk",
  financial_risk: "portfolio.cockpit.risk.category.financial_risk",
  valuation_risk: "portfolio.cockpit.risk.category.valuation_risk",
  thesis_risk: "portfolio.cockpit.risk.category.thesis_risk",
};

const BUSINESS_STATUS_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.business.not_evaluated",
  insufficient_input: "portfolio.cockpit.business.insufficient_input",
  weak: "portfolio.cockpit.business.weak",
  moderate: "portfolio.cockpit.business.moderate",
  strong: "portfolio.cockpit.business.strong",
};

const BUSINESS_CATEGORY_KEY: Record<AnalysisBusinessCategory, TranslationKey> = {
  business_model: "investmentCase.analysis.business.category.business_model",
  competitive_position: "investmentCase.analysis.business.category.competitive_position",
  management: "investmentCase.analysis.business.category.management",
  capital_allocation: "investmentCase.analysis.business.category.capital_allocation",
  growth: "investmentCase.analysis.business.category.growth",
  durability: "investmentCase.analysis.business.category.durability",
};

const RECOMMENDATION_REASON_KEY: Record<AnalysisRecommendationReason, TranslationKey> = {
  engine_not_implemented: "investmentCase.analysis.recommendation.reason.engine_not_implemented",
  evidence_insufficient: "investmentCase.analysis.recommendation.reason.evidence_insufficient",
};

/** Canonical enum values not worth a dedicated translation entry each
 * (dozens of narrow gap-kind members across Business/Valuation/Risk) are
 * shown as their own raw value with underscores turned into spaces --
 * still specific and honest (Phase 22: "no vague 'more data needed' if
 * the backend knows the specific gap"), matching Phase 41's own rule
 * that canonical enum values may stay English rather than requiring a
 * bespoke phrase for every member. */
function humanize(rawValue: string): string {
  return rawValue.replace(/_/g, " ");
}

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

const CASE_STATUS_KEY: Record<CaseStatusLevel, TranslationKey> = {
  healthy: "investmentCase.status.healthy",
  needs_review: "investmentCase.status.needsReview",
  high_priority: "investmentCase.status.highPriority",
};

/** Reused verbatim from `PortfolioPage.tsx`'s own lookup (ATLAS-028) --
 * same raw `ConcentrationLevel` enum value, same translation keys. */
const CASE_CONCENTRATION_LEVEL_KEY: Record<string, TranslationKey> = {
  Low: "portfolio.concentrationLevel.low",
  Moderate: "portfolio.concentrationLevel.moderate",
  Elevated: "portfolio.concentrationLevel.elevated",
  High: "portfolio.concentrationLevel.high",
};

const ASSESSMENT_CONVICTION_KEY: Record<AnalysisConvictionLevel, TranslationKey> = {
  very_high: "investmentCase.executiveSummary.assessment.conviction.very_high",
  high: "investmentCase.executiveSummary.assessment.conviction.high",
  moderate: "investmentCase.executiveSummary.assessment.conviction.moderate",
  low: "investmentCase.executiveSummary.assessment.conviction.low",
  insufficient_evidence: "investmentCase.executiveSummary.assessment.conviction.insufficient_evidence",
};

/** Only the three statuses `deriveAssessmentPoints` ever attaches to a
 * "valuation" point -- `not_evaluated`/`insufficient_input` are filtered
 * out before a point is created, so this map is deliberately narrower
 * than the full `AnalysisValuationStatus` union. */
const ASSESSMENT_VALUATION_KEY: Record<"undervalued" | "fairly_valued" | "expensive", TranslationKey> = {
  undervalued: "investmentCase.executiveSummary.assessment.valuation.undervalued",
  fairly_valued: "investmentCase.executiveSummary.assessment.valuation.fairly_valued",
  expensive: "investmentCase.executiveSummary.assessment.valuation.expensive",
};

const CURRENT_PRIORITY_KEY: Record<CurrentPriorityKind, TranslationKey> = {
  outcomeMissing: "investmentCase.executiveSummary.priority.outcomeMissing",
  reconciliationNeeded: "investmentCase.executiveSummary.priority.reconciliationNeeded",
  thesisStale: "investmentCase.executiveSummary.priority.thesisStale",
  openQuestion: "investmentCase.executiveSummary.priority.openQuestion",
  none: "investmentCase.executiveSummary.priority.none",
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

function assessmentSentence(point: AssessmentPoint, t: Translate): string {
  switch (point.kind) {
    case "conviction":
      return t(ASSESSMENT_CONVICTION_KEY[point.convictionLevel!]);
    case "valuation":
      return t(ASSESSMENT_VALUATION_KEY[point.valuationStatus as "undervalued" | "fairly_valued" | "expensive"]);
    case "risk":
      return t("investmentCase.executiveSummary.assessment.risk", {
        category: t(RISK_CATEGORY_KEY[point.riskCategory!]),
        status: t(RISK_STATUS_KEY[point.riskStatus!]),
      });
    case "thesisStale":
      return t("investmentCase.executiveSummary.assessment.thesisStale");
    case "insufficientOverall":
      return t("investmentCase.executiveSummary.assessment.insufficientOverall");
  }
}

function discussText(kind: CaseDiscussionKind, convictionLevel: AnalysisConvictionLevel, t: Translate): string {
  switch (kind) {
    case "valuationVsConviction":
      return t("investmentCase.executiveSummary.discuss.valuationVsConviction", {
        conviction: t(CONVICTION_LEVEL_KEY[convictionLevel]),
      });
    case "thesisStale":
      return t("investmentCase.executiveSummary.discuss.thesisStale");
    case "evidenceGap":
      return t("investmentCase.executiveSummary.discuss.evidenceGap");
    case "outstandingWork":
      return t("investmentCase.executiveSummary.discuss.outstandingWork");
    case "generic":
      return t("investmentCase.executiveSummary.discuss.generic");
  }
}

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
  askInput,
  setAskInput,
  askSubmitted,
  setAskSubmitted,
  t,
}: {
  analysis: InvestmentCaseAnalysisView;
  linkedHolding: AlphaHoldingView | null;
  alphaPortfolioStatus: AlphaPortfolioStatus;
  outstandingWorkKinds: OutstandingWorkKind[];
  askInput: string;
  setAskInput: (value: string) => void;
  askSubmitted: boolean;
  setAskSubmitted: (value: boolean) => void;
  t: Translate;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  const fcfYield = analysis.valuation.findings.find((f) => f.kind === "fcf_yield_relative") ?? null;
  const valuationStatus = fcfYield ? fcfYield.status : null;
  const mostSevereRisk = findMostSevereRisk(
    analysis.risk.findings.map((f) => ({ category: f.category, status: f.status })),
  );
  const evidenceGap =
    analysis.evidenceQuality !== null &&
    (analysis.evidenceQuality.coverage === "none" || analysis.evidenceQuality.coverage === "partial");
  const hasOutstandingWork = outstandingWorkKinds.length > 0;

  const assessmentPoints = deriveAssessmentPoints({
    convictionLevel: analysis.conviction.level,
    valuationStatus,
    mostSevereRisk,
    isThesisStale: analysis.isThesisStale,
  });

  const currentPriority = deriveCurrentPriority({
    outstandingWorkKinds,
    isThesisStale: analysis.isThesisStale,
    openQuestionCount: analysis.openQuestions.length,
  });

  const outstandingIssues = deriveOutstandingIssues({
    outstandingWorkKinds,
    isThesisStale: analysis.isThesisStale,
    evidenceGap,
  });

  const discussionKind = deriveCaseDiscussionKind({
    convictionLevel: analysis.conviction.level,
    valuationStatus,
    isThesisStale: analysis.isThesisStale,
    evidenceGap,
    hasOutstandingWork,
  });
  const discuss = discussText(discussionKind, analysis.conviction.level, t);

  const holdings = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.holdings : [];
  const largestHolding = holdings.reduce<AlphaHoldingView | null>(
    (max, h) => (max === null || h.weightPercent > max.weightPercent ? h : max),
    null,
  );
  const isLargestPosition =
    linkedHolding !== null && largestHolding !== null && largestHolding.ticker === linkedHolding.ticker;
  const cashWeightPercent = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.cashWeightPercent : null;
  const concentrationLevel = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.concentrationLevel : null;

  function fillAsk() {
    setAskInput(discuss);
    setAskSubmitted(false);
    inputRef.current?.focus();
  }

  function handleAsk() {
    if (askInput.trim() === "") return;
    setAskSubmitted(true);
  }

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("investmentCase.executiveSummary.heading")}</Heading>

        <div data-trace-source="assessment">
          <Stack gap="metadata">
            <Text color="secondary" as="p">
              {t("investmentCase.assessment.heading")}
            </Text>
            {assessmentPoints.map((point, index) => (
              <Text key={index} as="p">
                {assessmentSentence(point, t)}
              </Text>
            ))}
          </Stack>
        </div>

        <Divider tone="hairline" />

        <div data-trace-source="priority">
          <Inline gap="row" align="center">
            <Text color="secondary" as="p">
              {t("investmentCase.executiveSummary.priority.heading")}:
            </Text>
            <Text as="p">{t(CURRENT_PRIORITY_KEY[currentPriority])}</Text>
          </Inline>
        </div>

        <Divider tone="hairline" />

        <div data-trace-source="portfolioImpact">
          <Text color="secondary" as="p">
            {t("investmentCase.executiveSummary.portfolioImpact.heading")}
          </Text>
          <Inline gap="row" wrap>
            {linkedHolding && (
              <Text as="p">
                {t("investmentCase.executiveSummary.portfolioImpact.weight", {
                  percent: linkedHolding.weightPercent,
                })}
              </Text>
            )}
            {/* Corrective pass (compactness): "largest position" and
                "concentration" both describe the same concentration-
                relevance fact -- showing both is exactly the redundant
                portfolio metric this pass asks to avoid. Largest
                position is the more specific, more decision-relevant of
                the two when true; concentration is the fallback
                context otherwise. At most one of them renders. */}
            {isLargestPosition ? (
              <Text as="p">{t("investmentCase.executiveSummary.portfolioImpact.largestPosition")}</Text>
            ) : (
              concentrationLevel && (
                <Text as="p">
                  {t("portfolio.concentration", {
                    value: CASE_CONCENTRATION_LEVEL_KEY[concentrationLevel]
                      ? t(CASE_CONCENTRATION_LEVEL_KEY[concentrationLevel]!)
                      : concentrationLevel,
                  })}
                </Text>
              )
            )}
            {cashWeightPercent !== null && (
              <Text as="p">
                {t("investmentCase.executiveSummary.portfolioImpact.cash", { percent: cashWeightPercent })}
              </Text>
            )}
          </Inline>
        </div>

        {outstandingIssues.length > 0 && (
          <>
            <Divider tone="hairline" />
            <div data-trace-source="outstandingIssues">
              <Text color="secondary" as="p">
                {t("investmentCase.executiveSummary.outstandingIssues.heading")}
              </Text>
              <Stack gap="metadata">
                {/* Corrective pass (compactness): "Show at most 3 issues
                    ... show '+ N more issues'" -- full, untruncated detail
                    remains exactly where it already was, in the unchanged
                    Outstanding work section further down the page; this
                    is a display cap only, `outstandingIssues` itself is
                    unchanged. */}
                {outstandingIssues.slice(0, MAX_OUTSTANDING_ISSUES_SHOWN).map((issue) => (
                  <Text key={issue} as="p">
                    • {t(OUTSTANDING_ISSUE_KEY[issue])}
                  </Text>
                ))}
                {outstandingIssues.length > MAX_OUTSTANDING_ISSUES_SHOWN && (
                  <Text color="tertiary" as="p">
                    {t("investmentCase.executiveSummary.outstandingIssues.moreCount", {
                      count: outstandingIssues.length - MAX_OUTSTANDING_ISSUES_SHOWN,
                    })}
                  </Text>
                )}
              </Stack>
            </div>
          </>
        )}

        <Divider tone="hairline" />

        <div data-trace-source="discuss">
          <Stack gap="metadata">
            <Text color="secondary" as="p">
              {t("investmentCase.executiveSummary.discuss.heading")}
            </Text>
            <Text as="p">{discuss}</Text>
            <div>
              <Button variant="tertiary" onClick={fillAsk}>
                {t("investmentCase.executiveSummary.discuss.button")}
              </Button>
            </div>
            <Inline gap="row">
              <input
                ref={inputRef}
                value={askInput}
                placeholder={t("investmentCase.executiveSummary.askPlaceholder")}
                onChange={(event) => {
                  setAskInput(event.target.value);
                  setAskSubmitted(false);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") handleAsk();
                }}
                style={{ flex: 1 }}
              />
              <Button variant="primary" onClick={handleAsk}>
                {t("investmentCase.executiveSummary.discuss.askButton")}
              </Button>
            </Inline>
            {askSubmitted && (
              <Text color="tertiary" as="p">
                {t("portfolio.discussions.comingSoonNote")}
              </Text>
            )}
          </Stack>
        </div>
      </Stack>
    </Surface>
  );
}

/**
 * Business / Valuation / Risk / Evidence (Investment Case Workspace v2,
 * Sprint 2, Phase 2) -- the "explain the summary" workspace immediately
 * below Executive Summary. Every value is the exact same
 * `InvestmentCaseAnalysisView` field Phase 1's canonical sections
 * already rendered (nothing recomputed, nothing newly fetched) -- this
 * phase only regroups where each fact lives, per the sprint's own
 * "reduce unnecessary cards... merge sections that belong together"
 * instruction. Four top-level cards, matching the sprint's named list
 * exactly (Decision History/Outcomes below are unchanged, per "keep
 * mostly unchanged"):
 *
 * - **Business** (`BusinessSection`) -- Portfolio Context first (the
 *   deeper explanation Executive Summary's "This is your largest
 *   position" line points to), then Growth/Capital Allocation
 *   highlighted (the only two of the six business categories this
 *   codebase can currently evaluate for real -- see
 *   `atlas/alpha/portfolio_cockpit/models.py`'s own `BusinessSummary`
 *   docstring), then the remaining four categories.
 * - **Valuation** (`ValuationSection`) -- unchanged content (FCF Yield +
 *   scenario placeholder), just its own top-level card as before.
 * - **Risk** (`RiskSection`) -- unchanged content: the real four-category
 *   vector (business/financial/valuation/thesis risk). This sprint's
 *   own example wording ("operational/competitive/macro risk") names
 *   categories this codebase does not evaluate -- reusing existing data
 *   only means the real four stay exactly as they are, not renamed or
 *   padded out to match that wording.
 * - **Evidence** (`EvidenceSection`) -- "everything Atlas knows, and what
 *   it still doesn't" in one place: Current Thesis, Conviction,
 *   Confidence (all three moved here from their own former top-level
 *   cards -- each is fundamentally a judgment about evidence quality,
 *   not a Business/Valuation/Risk fact), Evidence Quality, Observations
 *   (moved from the former standalone "Investor Observations" card),
 *   Missing Evidence and Open Questions (`analysis.openQuestions` split
 *   by kind -- a presentational grouping over the exact same six
 *   existing `OpenQuestionKind` values, never a new domain concept),
 *   and Recommendation (moved here as the closing statement, since its
 *   withheld-reason is itself a statement about evidence/analysis
 *   completeness).
 *
 * The former standalone "compact header badges" card (Conviction/
 * Valuation/Evidence one-liner, added in ATLAS-029 Phase 9 before
 * Executive Summary existed) is removed: Executive Summary's own Atlas
 * Assessment now states the same facts directly under the page header,
 * so the badges had become a duplicate of it.
 */
function InvestmentCaseCanonicalSections({
  analysis,
  linkedHolding,
  alphaPortfolioStatus,
  t,
}: {
  analysis: InvestmentCaseAnalysisView;
  linkedHolding: AlphaHoldingView | null;
  alphaPortfolioStatus: AlphaPortfolioStatus;
  t: Translate;
}) {
  return (
    <Stack gap="inter-section">
      <BusinessSection
        analysis={analysis}
        linkedHolding={linkedHolding}
        alphaPortfolioStatus={alphaPortfolioStatus}
        t={t}
      />
      <ValuationSection analysis={analysis} t={t} />
      <RiskSection analysis={analysis} t={t} />
      <EvidenceSection analysis={analysis} t={t} />

      {/* Decision History (Phase 26) -- kept mostly unchanged, per this
          sprint's own instruction. */}
      <Surface tier="primary">
        <Stack gap="intra-section">
          <Heading level={2}>{t("investmentCase.analysis.decisionHistory.heading")}</Heading>
          {analysis.decisionHistory.length === 0 && (
            <Text color="secondary">{t("investmentCase.analysis.decisionHistory.empty")}</Text>
          )}
          {analysis.decisionHistory.map((entry) => (
            <Stack key={entry.decisionId} gap="intra-section">
              <Text as="p">
                {DECISION_TYPE_KEY[entry.decisionType]
                  ? t(DECISION_TYPE_KEY[entry.decisionType]!)
                  : entry.decisionType}
                {" — "}
                {entry.reason}
              </Text>
              <Text color="tertiary" as="p">
                {entry.decidedAt}
              </Text>
              <Divider tone="hairline" />
            </Stack>
          ))}
        </Stack>
      </Surface>

      {/* Outcomes (Phase 27) -- kept mostly unchanged, per this sprint's
          own instruction. */}
      <Surface tier="primary">
        <Stack gap="intra-section">
          <Heading level={2}>{t("investmentCase.analysis.outcomes.heading")}</Heading>
          {analysis.outcomeHistory.length === 0 && (
            <Text color="secondary">{t("investmentCase.analysis.outcomes.empty")}</Text>
          )}
          {analysis.outcomeHistory.map((entry) => (
            <Stack key={entry.outcomeId} gap="intra-section">
              <Text as="p">{entry.statement}</Text>
              <Text color="tertiary" as="p">
                {entry.occurredAt}
              </Text>
              <Divider tone="hairline" />
            </Stack>
          ))}
        </Stack>
      </Surface>
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
function BusinessSection({
  analysis,
  linkedHolding,
  alphaPortfolioStatus,
  t,
}: {
  analysis: InvestmentCaseAnalysisView;
  linkedHolding: AlphaHoldingView | null;
  alphaPortfolioStatus: AlphaPortfolioStatus;
  t: Translate;
}) {
  const growth = analysis.businessAnalysis.findings.find((f) => f.kind === "growth");
  const capitalAllocation = analysis.businessAnalysis.findings.find((f) => f.kind === "capital_allocation");
  const otherFindings = analysis.businessAnalysis.findings.filter(
    (f) => f.kind !== "growth" && f.kind !== "capital_allocation",
  );

  const holdings = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.holdings : [];
  const largestHolding = holdings.reduce<AlphaHoldingView | null>(
    (max, h) => (max === null || h.weightPercent > max.weightPercent ? h : max),
    null,
  );
  const cashWeightPercent = alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.cashWeightPercent : null;
  const concentrationLevel =
    alphaPortfolioStatus.kind === "loaded" ? alphaPortfolioStatus.view.concentrationLevel : null;

  function renderFinding(finding: BusinessFindingView) {
    return (
      <Stack key={finding.kind} gap="intra-section">
        <Text as="p">
          {t(BUSINESS_CATEGORY_KEY[finding.kind])}: {t(BUSINESS_STATUS_KEY[finding.status])}
        </Text>
        {finding.supportingEvidence.length > 0 && (
          <Text color="secondary" as="p">
            {t("investmentCase.analysis.business.supportingLabel")}: {finding.supportingEvidence.join(", ")}
          </Text>
        )}
        {finding.contradictingEvidence.length > 0 && (
          <Text color="tertiary" as="p">
            {t("investmentCase.analysis.business.contradictingLabel")}: {finding.contradictingEvidence.join(", ")}
          </Text>
        )}
        {finding.missingEvidence.length > 0 && (
          <Text color="secondary" as="p">
            {t("investmentCase.analysis.business.missingLabel")}: {finding.missingEvidence.map(humanize).join(", ")}
          </Text>
        )}
        <Divider tone="hairline" />
      </Stack>
    );
  }

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("investmentCase.analysis.business.heading")}</Heading>

        {linkedHolding && (
          <Stack gap="intra-section">
            <Heading level={3}>{t("investmentCase.analysis.business.portfolioContextHeading")}</Heading>
            <Text as="p">
              {t("investmentCase.executiveSummary.portfolioImpact.weight", {
                percent: linkedHolding.weightPercent,
              })}
            </Text>
            {largestHolding && (
              <Text as="p">
                {t("investmentCase.analysis.business.largestPositionLabel", {
                  ticker: largestHolding.ticker,
                  percent: largestHolding.weightPercent,
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
                {t("investmentCase.executiveSummary.portfolioImpact.cash", { percent: cashWeightPercent })}
              </Text>
            )}
            <Divider tone="hairline" />
          </Stack>
        )}

        {(growth || capitalAllocation) && (
          <Stack gap="intra-section">
            {growth && renderFinding(growth)}
            {capitalAllocation && renderFinding(capitalAllocation)}
          </Stack>
        )}

        {otherFindings.length > 0 && (
          <Stack gap="intra-section">
            <Heading level={3}>{t("investmentCase.analysis.business.otherCategoriesHeading")}</Heading>
            {otherFindings.map(renderFinding)}
          </Stack>
        )}
      </Stack>
    </Surface>
  );
}

/** Valuation -- unchanged content from Phase 1's canonical sections,
 * extracted into its own component for this sprint's four-section
 * structure. FCF Yield named explicitly; the three scenario methods
 * shown honestly as not yet available, never fabricated bear/base/bull
 * assumptions. */
function ValuationSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  const fcfYield = analysis.valuation.findings.find((f) => f.kind === "fcf_yield_relative");
  const scenarioFindings = analysis.valuation.findings.filter((f) => f.kind !== "fcf_yield_relative");

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("investmentCase.analysis.valuation.heading")}</Heading>
        {fcfYield && (
          <Stack gap="intra-section">
            <Text as="p">
              {t("investmentCase.analysis.valuation.method.fcf_yield_relative")}:{" "}
              {t(VALUATION_STATUS_KEY[fcfYield.status])}
            </Text>
            {fcfYield.currentYield != null && (
              <Text color="secondary" as="p">
                {t("investmentCase.analysis.valuation.currentYieldLabel")}: {(fcfYield.currentYield * 100).toFixed(2)}%
              </Text>
            )}
            {fcfYield.supportingFacts.length > 0 && (
              <Text color="secondary" as="p">
                {t("investmentCase.analysis.business.supportingLabel")}: {fcfYield.supportingFacts.join(", ")}
              </Text>
            )}
            {fcfYield.missingEvidence.length > 0 && (
              <Text color="secondary" as="p">
                {t("investmentCase.analysis.business.missingLabel")}: {fcfYield.missingEvidence.map(humanize).join(", ")}
              </Text>
            )}
          </Stack>
        )}
        {scenarioFindings.length > 0 && (
          <Stack gap="intra-section">
            <Heading level={3}>{t("investmentCase.analysis.valuation.scenarioHeading")}</Heading>
            <Text color="secondary" as="p">
              {t("investmentCase.analysis.valuation.scenarioNote")}
            </Text>
          </Stack>
        )}
      </Stack>
    </Surface>
  );
}

/** Risk -- unchanged content from Phase 1's canonical sections, extracted
 * into its own component. The full four-category vector, each shown
 * independently -- no aggregate, no hidden total. */
function RiskSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("investmentCase.analysis.risk.heading")}</Heading>
        <Text color="secondary" as="p">
          {t("investmentCase.analysis.risk.subheading")}
        </Text>
        {analysis.risk.findings.map((finding) => (
          <Stack key={finding.category} gap="intra-section">
            <Text as="p">
              {t(RISK_CATEGORY_KEY[finding.category])}: {t(RISK_STATUS_KEY[finding.status])}
            </Text>
            {finding.supportingFacts.length > 0 && (
              <Text color="secondary" as="p">
                {t("investmentCase.analysis.business.supportingLabel")}: {finding.supportingFacts.join(", ")}
              </Text>
            )}
            {finding.contradictingFacts.length > 0 && (
              <Text color="tertiary" as="p">
                {t("investmentCase.analysis.business.contradictingLabel")}: {finding.contradictingFacts.join(", ")}
              </Text>
            )}
            {finding.missingEvidence.length > 0 && (
              <Text color="secondary" as="p">
                {t("investmentCase.analysis.business.missingLabel")}: {finding.missingEvidence.map(humanize).join(", ")}
              </Text>
            )}
            <Divider tone="hairline" />
          </Stack>
        ))}
      </Stack>
    </Surface>
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
 * Evidence -- "everything Atlas knows, and what it still doesn't," per
 * this sprint's own framing, in one place: Current Thesis, Conviction,
 * and Confidence (moved here from their own former top-level cards --
 * each is fundamentally a judgment about evidence quality, not a
 * Business/Valuation/Risk fact), Evidence Quality, Observations (moved
 * from the former standalone "Investor Observations" card), Missing
 * Evidence and Open Questions (`analysis.openQuestions` split by
 * `EVIDENCE_GAP_QUESTION_KINDS`), and finally Recommendation, moved
 * here as the section's closing statement since its withheld-reason is
 * itself a statement about evidence/analysis completeness.
 */
function EvidenceSection({ analysis, t }: { analysis: InvestmentCaseAnalysisView; t: Translate }) {
  const hasThesis = analysis.currentThesis.latestDecisionReason || analysis.currentThesis.latestObservationStatement;
  const missingEvidenceQuestions = analysis.openQuestions.filter((q) => EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind));
  const otherOpenQuestions = analysis.openQuestions.filter((q) => !EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind));

  return (
    <Surface tier="primary">
      <Stack gap="intra-section">
        <Heading level={2}>{t("investmentCase.analysis.evidence.heading")}</Heading>

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
                  {humanize(reason)}
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

        {/* Evidence Quality -- case-wide Observation/Evidence coverage,
            distinct from each finding's own supporting/contradicting
            facts already shown inline in Business/Valuation/Risk above. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.evidence.qualityHeading")}</Heading>
          {!analysis.evidenceQuality && (
            <Text color="secondary">{t("investmentCase.analysis.evidence.noneRecorded")}</Text>
          )}
          {analysis.evidenceQuality && (
            <Stack gap="intra-section">
              <Text as="p">
                {t("investmentCase.analysis.evidence.coverageLabel")}: {t(CONFIDENCE_KEY[analysis.evidenceQuality.coverage])}
              </Text>
              <Text color="secondary" as="p">
                {t("investmentCase.analysis.evidence.supportingCount", {
                  count: analysis.evidenceQuality.supportingEvidenceCount,
                })}
              </Text>
              {analysis.evidenceQuality.challengingEvidenceCount > 0 && (
                <Text color="tertiary" as="p">
                  {t("investmentCase.analysis.evidence.challengingCount", {
                    count: analysis.evidenceQuality.challengingEvidenceCount,
                  })}
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
                {entry.observedAt}
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

        <Divider tone="hairline" />

        {/* Recommendation -- withheld, honestly, with its real reason.
            Never inferred from Valuation/Conviction/Risk. Closes this
            section since its withheld-reason is itself a statement
            about evidence/analysis completeness. */}
        <Stack gap="intra-section">
          <Heading level={3}>{t("investmentCase.analysis.recommendation.heading")}</Heading>
          <Text>{t("investmentCase.analysis.recommendation.withheld")}</Text>
          <Text color="secondary" as="p">
            {t("investmentCase.analysis.recommendation.reasonLabel")}:{" "}
            {t(RECOMMENDATION_REASON_KEY[analysis.recommendation.reason])}
          </Text>
        </Stack>
      </Stack>
    </Surface>
  );
}
