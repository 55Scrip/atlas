import { useEffect, useState } from "react";
import { useNavigate, useSearchParams, Link as RouterLink } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { FitBadge } from "../portfolioFit/FitBadge";
import { EVIDENCE_QUALITY_LEVEL_KEY, EVIDENCE_QUALITY_LEVEL_TONE, EVIDENCE_TRANSITION_DIRECTION_TONE, FIT_DIMENSION_KEY } from "../status/statusTone";
import {
  comparePortfolioFit,
  fetchPortfolioFitForHoldings,
  type FitComparisonView,
  type FitDimensionKind,
} from "../portfolioFit/portfolioFitApi";
import { compareStance, type StanceComparisonView } from "../stance/stanceApi";
import { compareEvidenceGraph, type EvidenceGraphComparisonView } from "../evidenceGraph/evidenceGraphCompareApi";
import { compareDecisionReadiness, type DecisionReadinessComparisonView } from "../decisionReadiness/decisionReadinessApi";
import { BLOCKER_KEY, STATUS_KEY, STATUS_TONE } from "../decisionReadiness/describeDecisionReadiness";
import { compareInvestmentDecisions, type DecisionComparisonView } from "../investmentDecision/investmentDecisionApi";
import { ACTION_KEY, ACTION_TONE, codeLabel } from "../investmentDecision/describeInvestmentDecision";
import { compareRecommendationConviction, type ConvictionComparisonView } from "../recommendationConviction/recommendationConvictionApi";
import { STABILITY_KEY, STABILITY_TONE, STRENGTH_KEY, STRENGTH_TONE } from "../recommendationConviction/describeRecommendationConviction";
import { compareDecisionPaths, type DecisionPathComparisonView } from "../decisionPath/decisionPathApi";
import { FINAL_STATE_KEY, FINAL_STATE_TONE } from "../decisionPath/describeDecisionPath";
import { compareOpportunityCost, type AlternativeComparisonView } from "../opportunityCost/opportunityCostApi";
import { compareDecisionMemory, type DecisionMemoryComparisonView } from "../decisionMemory/decisionMemoryApi";
import { compareDecisionExplanation, type DecisionExplanationComparisonView } from "../decisionExplanation/decisionExplanationApi";
import { referenceLabel } from "../decisionExplanation/describeDecisionExplanation";
import { compareDecisionReliability, type ReliabilityComparisonView } from "../decisionReliability/decisionReliabilityApi";
import { comparePortfolioDecision, type PortfolioDecisionComparisonView } from "../portfolioDecision/portfolioDecisionApi";
import { referenceLabel as portfolioDecisionReferenceLabel } from "../portfolioDecision/describePortfolioDecision";
import { referenceCodeLabel } from "../decisionReliability/describeDecisionReliability";
import { StanceBadge } from "../stance/StanceBadge";
import { stanceReasonSentence } from "../stance/describeStance";
import { STANCE_COMPARISON_REASON_KEY } from "../status/statusTone";
import { compareExplanations, type ComparisonEvidenceView } from "../explainability/explainabilityApi";
import { coverageDimensionLabel } from "../coverage/describeCoverage";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { fetchEvidenceQualityForTicker, type EvidenceQualityReportView } from "../evidenceQuality/evidenceQualityApi";
import { fetchEvidenceTimelineForTicker, type EvidenceTimelineEntryPairView } from "../evidenceTimeline/evidenceTimelineApi";
import {
  materialTransitions,
  prominentSourceEvidence,
  sourceEvidenceSentence,
  transitionCategoryLabel,
  transitionSentence,
} from "../evidenceTimeline/describeEvidenceTimeline";
import { fetchMaterialityForTicker, type MaterialityAssessmentView } from "../materiality/materialityApi";
import { materialEvidenceSentence } from "../materiality/describeMateriality";

interface PortfolioSummaryLite {
  largestPositionTicker: string | null;
}

type CompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; comparison: FitComparisonView };

/** Atlas Intelligence Sprint 2 (Recommendation Quality &
 * Actionability, Deliverable 9). */
type StanceCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; comparison: StanceComparisonView };

/** Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
 * Understanding, Deliverable 9). */
type EvidenceGraphCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; comparison: EvidenceGraphComparisonView };

/** Atlas Intelligence Sprint 11 (Decision Readiness & Decision
 * Eligibility, Deliverable 9). */
type DecisionReadinessCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; comparison: DecisionReadinessComparisonView };

/** Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
 * Trace, Deliverable 7). */
type ExplanationCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; comparison: ComparisonEvidenceView };

/** Atlas Intelligence Sprint 4 (Evidence Quality & Conflict
 * Resolution, Deliverable 8). No dedicated backend compare endpoint --
 * both tickers' own `EvidenceQualityReportView` (already exposed via
 * `/evidence-quality/ticker/:ticker`) are fetched side by side and
 * rendered together, never a new comparison concept the backend does
 * not already compute. */
type EvidenceQualityCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; reportA: EvidenceQualityReportView; reportB: EvidenceQualityReportView };

/** Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
 * Understanding, Deliverable 8). Same "no dedicated compare endpoint,
 * fetch both tickers' own real history side by side" shape as Evidence
 * Quality above. Never ranks by history existing -- only informs. */
type EvidenceTimelineCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; entriesA: EvidenceTimelineEntryPairView[]; entriesB: EvidenceTimelineEntryPairView[] };

/** Atlas Intelligence -- Materiality & Priority Engine, Deliverable 8.
 * Same "no dedicated compare endpoint, fetch both tickers' own real
 * assessment side by side" shape as Evidence Quality/Evidence Timeline
 * above. "Do not compare every observation" -- only each company's own
 * single most material supporting/contradicting-or-limiting/missing
 * pick is shown, never the full unranked list this page's own
 * "Jämförelse av underlag" `ExpandableDetail` already exposes one
 * click away. */
type MaterialityCompareStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "error" }
  | { kind: "loaded"; assessmentA: MaterialityAssessmentView; assessmentB: MaterialityAssessmentView };

const DIMENSION_ORDER: FitDimensionKind[] = ["business", "valuation", "risk", "allocation", "expected_contribution", "cash_impact"];

/**
 * Deliverable 5/6 -- side-by-side comparison, and candidate-vs-existing-
 * holding comparison, both through the one existing `GET /portfolio-fit
 * /compare` endpoint (`PortfolioFitService.compare`/`engine.compare_fit`,
 * Product Sprint 4). This page computes no comparison logic of its own
 * -- `comparison.preferredTicker`/`.reasoning` are rendered verbatim.
 *
 * "Vs a similar holding" (named as an example in the sprint brief) is
 * deliberately not offered as a quick pick: no sector/industry field
 * exists on `AlphaHolding` to determine similarity (the same gap
 * `atlas.alpha.portfolio_intelligence`'s own module docstring already
 * disclosed, and Product Sprint 4's own Allocation Fit design note
 * repeats) -- fabricating one would violate this sprint's own "do not
 * fabricate unavailable data" rule. "Vs weakest holding" and "vs
 * largest concentration" are both real, already-available facts
 * (`/portfolio-fit/holdings`'s own sort order; `largestPositionTicker`),
 * plus a manual picker for "vs a specific holding."
 */
export function CompareCandidatesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const tickerA = searchParams.get("a");
  const tickerB = searchParams.get("b");

  const [status, setStatus] = useState<CompareStatus>({ kind: "idle" });
  const [stanceStatus, setStanceStatus] = useState<StanceCompareStatus>({ kind: "idle" });
  const [evidenceGraphCompareStatus, setEvidenceGraphCompareStatus] = useState<EvidenceGraphCompareStatus>({
    kind: "idle",
  });
  const [decisionReadinessCompareStatus, setDecisionReadinessCompareStatus] = useState<DecisionReadinessCompareStatus>({
    kind: "idle",
  });

  /** Atlas Decision Layer Sprint 1 (Investment Decision Synthesis,
   * Deliverable 9). Same idle/loading/error/not-found/loaded pattern as
   * `decisionReadinessCompareStatus` above. */
  const [investmentDecisionCompareStatus, setInvestmentDecisionCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: DecisionComparisonView }
  >({ kind: "idle" });

  /** Atlas Decision Layer Sprint 2 (Recommendation Strength &
   * Conviction, Deliverable 9). Same idle/loading/error/not-found/
   * loaded pattern as `investmentDecisionCompareStatus` above. */
  const [convictionCompareStatus, setConvictionCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: ConvictionComparisonView }
  >({ kind: "idle" });

  /** Atlas Decision Layer Sprint 3 (Decision Path & Required
   * Progress, Deliverable 9). Same idle/loading/error/not-found/
   * loaded pattern as `convictionCompareStatus` above. */
  const [decisionPathCompareStatus, setDecisionPathCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: DecisionPathComparisonView }
  >({ kind: "idle" });

  /** Atlas Decision Layer Sprint 4 (Decision Alternatives &
   * Opportunity Cost, Deliverable 9). Same idle/loading/error/
   * not-found/loaded pattern as `decisionPathCompareStatus` above. */
  const [opportunityCostCompareStatus, setOpportunityCostCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: AlternativeComparisonView }
  >({ kind: "idle" });

  /** Atlas Decision Layer Sprint 5 (Decision Memory, Deliverable 9).
   * Same idle/loading/error/not-found/loaded pattern as
   * `opportunityCostCompareStatus` above. */
  const [decisionMemoryCompareStatus, setDecisionMemoryCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: DecisionMemoryComparisonView }
  >({ kind: "idle" });
  const [explanationStatus, setExplanationStatus] = useState<ExplanationCompareStatus>({ kind: "idle" });

  /** Atlas Decision Layer Sprint 6 (Decision Explanation &
   * Traceability, Deliverable 9). Same idle/loading/error/not-found/
   * loaded pattern as `decisionMemoryCompareStatus` above. */
  const [decisionExplanationCompareStatus, setDecisionExplanationCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: DecisionExplanationComparisonView }
  >({ kind: "idle" });

  /** Atlas Decision Layer Sprint 7 (Decision Reliability, Deliverable
   * 10). Same idle/loading/error/not-found/loaded pattern as
   * `decisionExplanationCompareStatus` above. */
  const [decisionReliabilityCompareStatus, setDecisionReliabilityCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: ReliabilityComparisonView }
  >({ kind: "idle" });

  /** Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis,
   * Deliverable 10). Same idle/loading/error/not-found/loaded pattern
   * as `decisionReliabilityCompareStatus` above. */
  const [portfolioDecisionCompareStatus, setPortfolioDecisionCompareStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "not-found" }
    | { kind: "error" }
    | { kind: "loaded"; comparison: PortfolioDecisionComparisonView }
  >({ kind: "idle" });
  const [evidenceQualityStatus, setEvidenceQualityStatus] = useState<EvidenceQualityCompareStatus>({ kind: "idle" });
  const [evidenceTimelineStatus, setEvidenceTimelineStatus] = useState<EvidenceTimelineCompareStatus>({ kind: "idle" });
  const [materialityStatus, setMaterialityStatus] = useState<MaterialityCompareStatus>({ kind: "idle" });
  const [holdingTickers, setHoldingTickers] = useState<string[]>([]);
  const [weakestHolding, setWeakestHolding] = useState<string | null>(null);
  const [largestConcentration, setLargestConcentration] = useState<string | null>(null);
  const [manualPick, setManualPick] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioFitForHoldings(controller.signal)
      .then((assessments) => {
        setHoldingTickers(assessments.map((a) => a.ticker));
        const evaluated = assessments.filter((a) => a.overall !== "unavailable");
        if (evaluated.length > 0) setWeakestHolding(evaluated[evaluated.length - 1]!.ticker);
      })
      .catch(() => {});
    fetch("/api/alpha-portfolio/status", { signal: controller.signal })
      .then((r) => (r.ok ? (r.json() as Promise<{ summary: PortfolioSummaryLite | null }>) : null))
      .then((body) => setLargestConcentration(body?.summary?.largestPositionTicker ?? null))
      .catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!tickerA || !tickerB) {
      setStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setStatus({ kind: "loading" });
    comparePortfolioFit(tickerA, tickerB, controller.signal)
      .then((comparison) => setStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  useEffect(() => {
    if (!tickerA || !tickerB) {
      setStanceStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setStanceStatus({ kind: "loading" });
    compareStance(tickerA, tickerB, controller.signal)
      .then((comparison) => setStanceStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStanceStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
   * Understanding, Deliverable 9). Independent fetch, same pattern as
   * `stanceStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setEvidenceGraphCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setEvidenceGraphCompareStatus({ kind: "loading" });
    compareEvidenceGraph(tickerA, tickerB, controller.signal)
      .then((comparison) =>
        setEvidenceGraphCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setEvidenceGraphCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Intelligence Sprint 11 (Decision Readiness & Decision
   * Eligibility, Deliverable 9). Independent fetch, same pattern as
   * `evidenceGraphCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setDecisionReadinessCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setDecisionReadinessCompareStatus({ kind: "loading" });
    compareDecisionReadiness(tickerA, tickerB, controller.signal)
      .then((comparison) =>
        setDecisionReadinessCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionReadinessCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 1 (Investment Decision Synthesis,
   * Deliverable 9). Independent fetch, same pattern as
   * `decisionReadinessCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setInvestmentDecisionCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setInvestmentDecisionCompareStatus({ kind: "loading" });
    compareInvestmentDecisions(tickerA, tickerB, controller.signal)
      .then((comparison) =>
        setInvestmentDecisionCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setInvestmentDecisionCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 2 (Recommendation Strength &
   * Conviction, Deliverable 9). Independent fetch, same pattern as
   * `investmentDecisionCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setConvictionCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setConvictionCompareStatus({ kind: "loading" });
    compareRecommendationConviction(tickerA, tickerB, controller.signal)
      .then((comparison) => setConvictionCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setConvictionCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 3 (Decision Path & Required
   * Progress, Deliverable 9). Independent fetch, same pattern as
   * `convictionCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setDecisionPathCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setDecisionPathCompareStatus({ kind: "loading" });
    compareDecisionPaths(tickerA, tickerB, controller.signal)
      .then((comparison) => setDecisionPathCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionPathCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 4 (Decision Alternatives &
   * Opportunity Cost, Deliverable 9). Independent fetch, same pattern
   * as `decisionPathCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setOpportunityCostCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setOpportunityCostCompareStatus({ kind: "loading" });
    compareOpportunityCost(tickerA, tickerB, controller.signal)
      .then((comparison) => setOpportunityCostCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setOpportunityCostCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 5 (Decision Memory, Deliverable 9).
   * Independent fetch, same pattern as `opportunityCostCompareStatus`
   * above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setDecisionMemoryCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setDecisionMemoryCompareStatus({ kind: "loading" });
    compareDecisionMemory(tickerA, tickerB, controller.signal)
      .then((comparison) => setDecisionMemoryCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionMemoryCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 6 (Decision Explanation &
   * Traceability, Deliverable 9). Independent fetch, same pattern as
   * `decisionMemoryCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setDecisionExplanationCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setDecisionExplanationCompareStatus({ kind: "loading" });
    compareDecisionExplanation(tickerA, tickerB, controller.signal)
      .then((comparison) =>
        setDecisionExplanationCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionExplanationCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 7 (Decision Reliability, Deliverable
   * 10). Independent fetch, same pattern as
   * `decisionExplanationCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setDecisionReliabilityCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setDecisionReliabilityCompareStatus({ kind: "loading" });
    compareDecisionReliability(tickerA, tickerB, controller.signal)
      .then((comparison) =>
        setDecisionReliabilityCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionReliabilityCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  /** Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis,
   * Deliverable 10). Independent fetch, same pattern as
   * `decisionReliabilityCompareStatus` above. */
  useEffect(() => {
    if (!tickerA || !tickerB) {
      setPortfolioDecisionCompareStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setPortfolioDecisionCompareStatus({ kind: "loading" });
    comparePortfolioDecision(tickerA, tickerB, controller.signal)
      .then((comparison) =>
        setPortfolioDecisionCompareStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioDecisionCompareStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  useEffect(() => {
    if (!tickerA || !tickerB) {
      setExplanationStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setExplanationStatus({ kind: "loading" });
    compareExplanations(tickerA, tickerB, controller.signal)
      .then((comparison) => setExplanationStatus(comparison === null ? { kind: "not-found" } : { kind: "loaded", comparison }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setExplanationStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  useEffect(() => {
    if (!tickerA || !tickerB) {
      setEvidenceQualityStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setEvidenceQualityStatus({ kind: "loading" });
    Promise.all([fetchEvidenceQualityForTicker(tickerA, controller.signal), fetchEvidenceQualityForTicker(tickerB, controller.signal)])
      .then(([reportA, reportB]) =>
        setEvidenceQualityStatus(reportA === null || reportB === null ? { kind: "not-found" } : { kind: "loaded", reportA, reportB }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setEvidenceQualityStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  useEffect(() => {
    if (!tickerA || !tickerB) {
      setEvidenceTimelineStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setEvidenceTimelineStatus({ kind: "loading" });
    Promise.all([fetchEvidenceTimelineForTicker(tickerA, controller.signal), fetchEvidenceTimelineForTicker(tickerB, controller.signal)])
      .then(([entriesA, entriesB]) =>
        setEvidenceTimelineStatus(entriesA === null || entriesB === null ? { kind: "not-found" } : { kind: "loaded", entriesA, entriesB }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setEvidenceTimelineStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  useEffect(() => {
    if (!tickerA || !tickerB) {
      setMaterialityStatus({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    setMaterialityStatus({ kind: "loading" });
    Promise.all([fetchMaterialityForTicker(tickerA, controller.signal), fetchMaterialityForTicker(tickerB, controller.signal)])
      .then(([assessmentA, assessmentB]) =>
        setMaterialityStatus(assessmentA === null || assessmentB === null ? { kind: "not-found" } : { kind: "loaded", assessmentA, assessmentB }),
      )
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setMaterialityStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [tickerA, tickerB]);

  function pickB(ticker: string) {
    setSearchParams((params) => {
      const next = new URLSearchParams(params);
      next.set("b", ticker.toUpperCase());
      return next;
    });
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <RouterLink to="/discovery" style={{ color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" }}>
          {t("discovery.card.backToDiscovery")}
        </RouterLink>

        <Heading level={2}>{t("discovery.compare.heading")}</Heading>
        {/* Product Sprint 9 (Discovery Excellence, Deliverable 10) --
            states plainly what is being compared before anything else
            renders, so a reader who arrived mid-flow (a bookmark, a
            shared link, a Companion deep link) is never unsure. Atlas
            has no real signal for *why* this specific pairing was
            chosen (no origin/reason param exists, nor should one be
            fabricated) -- only the real fact of what's being compared
            is stated. */}
        {tickerA && tickerB && (
          <Text color="secondary" as="p">
            {t("discovery.compare.comparingContext", { tickerA, tickerB })}
          </Text>
        )}

        {!tickerA && <Text color="tertiary">{t("discovery.compare.noCandidateSelected")}</Text>}

        {tickerA && !tickerB && (
          <Stack gap="metadata">
            <Text as="p">{t("discovery.compare.pickSecond", { ticker: tickerA })}</Text>
            <Inline gap="row" wrap align="center">
              {weakestHolding && (
                <Button variant="tertiary" onClick={() => pickB(weakestHolding)}>
                  {t("discovery.compare.vsWeakestHolding", { ticker: weakestHolding })}
                </Button>
              )}
              {largestConcentration && (
                <Button variant="tertiary" onClick={() => pickB(largestConcentration)}>
                  {t("discovery.compare.vsLargestConcentration", { ticker: largestConcentration })}
                </Button>
              )}
            </Inline>
            <Inline gap="row" align="center">
              <select value={manualPick} onChange={(event) => setManualPick(event.target.value)}>
                <option value="">{t("discovery.compare.manualPickPlaceholder")}</option>
                {holdingTickers.map((ticker) => (
                  <option key={ticker} value={ticker}>
                    {ticker}
                  </option>
                ))}
              </select>
              <Button variant="tertiary" disabled={manualPick === ""} onClick={() => pickB(manualPick)}>
                {t("discovery.compare.compareButton")}
              </Button>
            </Inline>
            <Text color="tertiary" as="p">
              {t("discovery.compare.noSimilarHoldingNote")}
            </Text>
          </Stack>
        )}

        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("portfolioFit.section.loading")}
          </Text>
        )}
        {/* Deliverable 13 (Empty States) -- "not enough data yet" and "a
            real fetch failed" are two different, both-real facts; the
            prior version showed identical copy for both, which meant a
            genuine network/backend error was silently presented as if
            it were an honest data gap. */}
        {status.kind === "not-found" && <Text color="tertiary">{t("discovery.compare.insufficientData")}</Text>}
        {status.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("discovery.compare.loadError")}
          </Text>
        )}

        {status.kind === "loaded" && (
          <Stack gap="metadata">
            <Divider tone="hairline" />
            <Inline gap="inter-section" wrap align="start">
              <ComparisonColumn heading={status.comparison.assessmentA.ticker} assessment={status.comparison.assessmentA} />
              <ComparisonColumn heading={status.comparison.assessmentB.ticker} assessment={status.comparison.assessmentB} />
            </Inline>
            {/* Atlas Intelligence Sprint 2 (Recommendation Quality &
                Actionability, Deliverable 9). The higher-level, holistic
                answer ("what should I do") stated first; the existing
                Portfolio Fit conclusion beneath it stays the narrower
                "which fits the portfolio better" detail -- two real,
                distinct, complementary facts, never collapsed into one
                or restated as the same claim twice. Never forces a
                winner: `preferredTicker` is `null` whenever either
                Stance is itself too uncertain to compare, or both are
                genuinely tied -- rendered honestly either way. */}
            {stanceStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("stance.compare.heading")}</Heading>
                <Inline gap="metadata" align="center">
                  <StanceBadge level={stanceStatus.comparison.stanceA.level} />
                  <Text color="tertiary" as="span">
                    {stanceStatus.comparison.tickerA}
                  </Text>
                  <Text color="tertiary" as="span">
                    ·
                  </Text>
                  <StanceBadge level={stanceStatus.comparison.stanceB.level} />
                  <Text color="tertiary" as="span">
                    {stanceStatus.comparison.tickerB}
                  </Text>
                </Inline>
                {stanceStatus.comparison.reasoning.map((reason, index) => (
                  <Text key={index} color="secondary" as="p">
                    {t(STANCE_COMPARISON_REASON_KEY[reason.code], { ticker: reason.ticker ?? "" })}
                  </Text>
                ))}
              </Stack>
            )}

            {/* Atlas Intelligence Sprint 10 (Evidence Graph &
                Dependency Understanding, Deliverable 9). "Ingen
                rekommendation" -- three real, structural counts per
                side, never a preferred ticker. */}
            {evidenceGraphCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("evidenceGraph.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[evidenceGraphCompareStatus.comparison.a, evidenceGraphCompareStatus.comparison.b].map((side) => (
                    <Stack key={side.ticker} gap="metadata">
                      <Text as="span" style={{ fontWeight: 600 }}>
                        {side.ticker}
                      </Text>
                      <Text color="secondary" as="p">
                        {t("evidenceGraph.compare.independentObservationChains", { count: side.independentObservationChains })}
                      </Text>
                      <Text color="secondary" as="p">
                        {t("evidenceGraph.compare.criticalDependencyCount", { count: side.criticalDependencyCount })}
                      </Text>
                      <Text color="secondary" as="p">
                        {t("evidenceGraph.compare.weakLinkCount", { count: side.weakLinkCount })}
                      </Text>
                    </Stack>
                  ))}
                </Inline>
              </Stack>
            )}

            {/* Atlas Intelligence Sprint 11 (Decision Readiness &
                Decision Eligibility, Deliverable 9). "Readiness
                informs. It never ranks" -- both statuses shown
                side-by-side, plus which real blockers differ; no
                preferred ticker is ever stated here. */}
            {decisionReadinessCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("decisionReadiness.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[
                    { ticker: tickerA, readiness: decisionReadinessCompareStatus.comparison.a },
                    { ticker: tickerB, readiness: decisionReadinessCompareStatus.comparison.b },
                  ].map(({ ticker, readiness }) => (
                    <Inline key={readiness.caseId} gap="row" align="center">
                      <Text as="span" style={{ fontWeight: 600 }}>
                        {ticker}
                      </Text>
                      <StatusBadge label={t(STATUS_KEY[readiness.status])} tone={STATUS_TONE[readiness.status]} />
                    </Inline>
                  ))}
                </Inline>
                <Text color="secondary" as="p">
                  {decisionReadinessCompareStatus.comparison.differingBlockerKinds.length > 0
                    ? t("decisionReadiness.compare.differingBlockers", {
                        blockers: decisionReadinessCompareStatus.comparison.differingBlockerKinds
                          .map((kind) => t(BLOCKER_KEY[kind]))
                          .join(" · "),
                      })
                    : t("decisionReadiness.compare.noDifference")}
                </Text>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 1 (Investment Decision
                Synthesis, Deliverable 9). "Decision A, Decision B,
                primary difference, primary shared blocker, primary
                shared strength -- never choose a winner." */}
            {investmentDecisionCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("investmentDecision.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[
                    { ticker: tickerA, decision: investmentDecisionCompareStatus.comparison.a },
                    { ticker: tickerB, decision: investmentDecisionCompareStatus.comparison.b },
                  ].map(({ ticker, decision }) => (
                    <Inline key={decision.caseId} gap="row" align="center">
                      <Text as="span" style={{ fontWeight: 600 }}>
                        {ticker}
                      </Text>
                      <StatusBadge label={t(ACTION_KEY[decision.action])} tone={ACTION_TONE[decision.action]} />
                    </Inline>
                  ))}
                </Inline>
                <Text color="secondary" as="p">
                  {investmentDecisionCompareStatus.comparison.sharedBlockerCodes.length > 0
                    ? t("investmentDecision.compare.sharedBlockers", {
                        items: investmentDecisionCompareStatus.comparison.sharedBlockerCodes
                          .map((code) => codeLabel(code, t))
                          .join(" · "),
                      })
                    : t("investmentDecision.compare.noSharedBlockers")}
                </Text>
                <Text color="secondary" as="p">
                  {investmentDecisionCompareStatus.comparison.sharedSupportingReasonCodes.length > 0
                    ? t("investmentDecision.compare.sharedStrengths", {
                        items: investmentDecisionCompareStatus.comparison.sharedSupportingReasonCodes
                          .map((code) => codeLabel(code, t))
                          .join(" · "),
                      })
                    : t("investmentDecision.compare.noSharedStrengths")}
                </Text>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 2 (Recommendation Strength
                & Conviction, Deliverable 9). Four independent factual
                comparisons, each honest on tie -- never an overall
                "winner." */}
            {convictionCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("recommendationConviction.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[
                    { ticker: tickerA, conviction: convictionCompareStatus.comparison.a },
                    { ticker: tickerB, conviction: convictionCompareStatus.comparison.b },
                  ].map(({ ticker, conviction }) => (
                    <Inline key={conviction.caseId} gap="row" align="center">
                      <Text as="span" style={{ fontWeight: 600 }}>
                        {ticker}
                      </Text>
                      <StatusBadge label={t(STRENGTH_KEY[conviction.strength])} tone={STRENGTH_TONE[conviction.strength]} />
                      <StatusBadge label={t(STABILITY_KEY[conviction.stability])} tone={STABILITY_TONE[conviction.stability]} />
                    </Inline>
                  ))}
                </Inline>
                <Text color="secondary" as="p">
                  {convictionCompareStatus.comparison.strongerCaseId
                    ? t("recommendationConviction.compare.stronger", {
                        ticker:
                          (convictionCompareStatus.comparison.strongerCaseId === convictionCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("recommendationConviction.compare.strongerTie")}
                </Text>
                <Text color="secondary" as="p">
                  {convictionCompareStatus.comparison.moreEvidenceLimitedCaseId
                    ? t("recommendationConviction.compare.moreEvidenceLimited", {
                        ticker:
                          (convictionCompareStatus.comparison.moreEvidenceLimitedCaseId === convictionCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("recommendationConviction.compare.evidenceLimitedTie")}
                </Text>
                <Text color="secondary" as="p">
                  {convictionCompareStatus.comparison.moreOperationallyBlockedCaseId
                    ? t("recommendationConviction.compare.moreOperationallyBlocked", {
                        ticker:
                          (convictionCompareStatus.comparison.moreOperationallyBlockedCaseId === convictionCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("recommendationConviction.compare.operationallyBlockedTie")}
                </Text>
                <Text color="secondary" as="p">
                  {convictionCompareStatus.comparison.moreStableCaseId
                    ? t("recommendationConviction.compare.moreStable", {
                        ticker:
                          (convictionCompareStatus.comparison.moreStableCaseId === convictionCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("recommendationConviction.compare.stableTie")}
                </Text>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 3 (Decision Path &
                Required Progress, Deliverable 9). Four independent
                factual comparisons, each honest on tie -- never a
                "better investment" verdict. */}
            {decisionPathCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("decisionPath.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[
                    { ticker: tickerA, path: decisionPathCompareStatus.comparison.a },
                    { ticker: tickerB, path: decisionPathCompareStatus.comparison.b },
                  ].map(({ ticker, path }) => (
                    <Inline key={path.caseId} gap="row" align="center">
                      <Text as="span" style={{ fontWeight: 600 }}>
                        {ticker}
                      </Text>
                      <StatusBadge label={t(FINAL_STATE_KEY[path.finalReachableState])} tone={FINAL_STATE_TONE[path.finalReachableState]} />
                    </Inline>
                  ))}
                </Inline>
                <Text color="secondary" as="p">
                  {decisionPathCompareStatus.comparison.shorterPathCaseId
                    ? t("decisionPath.compare.shorterPath", {
                        ticker:
                          (decisionPathCompareStatus.comparison.shorterPathCaseId === decisionPathCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionPath.compare.shorterPathTie")}
                </Text>
                <Text color="secondary" as="p">
                  {decisionPathCompareStatus.comparison.fewerRemainingBlockersCaseId
                    ? t("decisionPath.compare.fewerBlockers", {
                        ticker:
                          (decisionPathCompareStatus.comparison.fewerRemainingBlockersCaseId === decisionPathCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionPath.compare.fewerBlockersTie")}
                </Text>
                <Text color="secondary" as="p">
                  {decisionPathCompareStatus.comparison.moreOperationallyDependentCaseId
                    ? t("decisionPath.compare.moreOperationallyDependent", {
                        ticker:
                          (decisionPathCompareStatus.comparison.moreOperationallyDependentCaseId === decisionPathCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionPath.compare.operationallyDependentTie")}
                </Text>
                <Text color="secondary" as="p">
                  {decisionPathCompareStatus.comparison.moreEvidenceDependentCaseId
                    ? t("decisionPath.compare.moreEvidenceDependent", {
                        ticker:
                          (decisionPathCompareStatus.comparison.moreEvidenceDependentCaseId === decisionPathCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionPath.compare.evidenceDependentTie")}
                </Text>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 4 (Decision Alternatives &
                Opportunity Cost, Deliverable 9). "Why these companies
                are genuine alternatives... why Atlas refuses to
                choose" -- a fixed disclosure plus the same factual,
                honest-on-tie comparisons every prior Compare section
                already uses. Never a winner. */}
            {opportunityCostCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("opportunityCost.compare.heading")}</Heading>
                <Text color="secondary" as="p">
                  {t("opportunityCost.compare.disclosure")}
                </Text>
                <Text color="secondary" as="p">
                  {opportunityCostCompareStatus.comparison.conviction.strongerCaseId
                    ? t("opportunityCost.compare.strongerConviction", {
                        ticker:
                          (opportunityCostCompareStatus.comparison.conviction.strongerCaseId ===
                          opportunityCostCompareStatus.comparison.conviction.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("opportunityCost.compare.strongerConvictionTie")}
                </Text>
                <Text color="secondary" as="p">
                  {opportunityCostCompareStatus.comparison.path.shorterPathCaseId
                    ? t("opportunityCost.compare.shorterPath", {
                        ticker:
                          (opportunityCostCompareStatus.comparison.path.shorterPathCaseId ===
                          opportunityCostCompareStatus.comparison.path.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("opportunityCost.compare.shorterPathTie")}
                </Text>
                <Text color="secondary" as="p">
                  {opportunityCostCompareStatus.comparison.moreDependencyBlockedCaseId
                    ? t("opportunityCost.compare.moreDependencyBlocked", {
                        ticker:
                          (opportunityCostCompareStatus.comparison.moreDependencyBlockedCaseId ===
                          opportunityCostCompareStatus.comparison.path.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("opportunityCost.compare.dependencyTie")}
                </Text>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 5 (Decision Memory,
                Deliverable 9). Four independent factual comparisons,
                each honest on tie -- never infers superiority. */}
            {decisionMemoryCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("decisionMemory.compare.heading")}</Heading>
                <Text color="secondary" as="p">
                  {decisionMemoryCompareStatus.comparison.moreRecentlyChangedCaseId
                    ? t("decisionMemory.compare.moreRecentlyChanged", {
                        ticker:
                          (decisionMemoryCompareStatus.comparison.moreRecentlyChangedCaseId === decisionMemoryCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionMemory.compare.moreRecentlyChangedTie")}
                </Text>
                <Text color="secondary" as="p">
                  {decisionMemoryCompareStatus.comparison.moreStableCaseId
                    ? t("decisionMemory.compare.moreStable", {
                        ticker:
                          (decisionMemoryCompareStatus.comparison.moreStableCaseId === decisionMemoryCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionMemory.compare.moreStableTie")}
                </Text>
                <Text color="secondary" as="p">
                  {decisionMemoryCompareStatus.comparison.convictionChangedCaseId
                    ? t("decisionMemory.compare.convictionChanged", {
                        ticker:
                          (decisionMemoryCompareStatus.comparison.convictionChangedCaseId === decisionMemoryCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionMemory.compare.convictionChangedTie")}
                </Text>
                <Text color="secondary" as="p">
                  {decisionMemoryCompareStatus.comparison.blockersDisappearedCaseId
                    ? t("decisionMemory.compare.blockersDisappeared", {
                        ticker:
                          (decisionMemoryCompareStatus.comparison.blockersDisappearedCaseId === decisionMemoryCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionMemory.compare.blockersDisappearedTie")}
                </Text>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 6 (Decision Explanation &
                Traceability, Deliverable 9). Shared supporting
                findings, each side's own differing blockers, and
                shared dependencies -- never a winner. */}
            {decisionExplanationCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("decisionExplanation.compare.heading")}</Heading>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionExplanation.compare.sharedSupportingHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionExplanationCompareStatus.comparison.sharedSupporting.length > 0
                      ? decisionExplanationCompareStatus.comparison.sharedSupporting.map((ref) => referenceLabel(ref, t)).join(" · ")
                      : t("decisionExplanation.compare.noSharedSupporting")}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionExplanation.compare.differingBlockingHeading", { ticker: tickerA ?? "" })}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionExplanationCompareStatus.comparison.differingBlockingA.length > 0
                      ? decisionExplanationCompareStatus.comparison.differingBlockingA.map((ref) => referenceLabel(ref, t)).join(" · ")
                      : t("decisionExplanation.compare.noDifferingBlocking", { ticker: tickerA ?? "" })}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionExplanation.compare.differingBlockingHeading", { ticker: tickerB ?? "" })}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionExplanationCompareStatus.comparison.differingBlockingB.length > 0
                      ? decisionExplanationCompareStatus.comparison.differingBlockingB.map((ref) => referenceLabel(ref, t)).join(" · ")
                      : t("decisionExplanation.compare.noDifferingBlocking", { ticker: tickerB ?? "" })}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionExplanation.compare.sharedDependenciesHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionExplanationCompareStatus.comparison.sharedDependencies.length > 0
                      ? decisionExplanationCompareStatus.comparison.sharedDependencies.map((ref) => referenceLabel(ref, t)).join(" · ")
                      : t("decisionExplanation.compare.noSharedDependencies")}
                  </Text>
                </Stack>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 7 (Decision Reliability,
                Deliverable 10). More reliable side (honest tie),
                shared/differing limitations, shared strengths --
                never a winner. */}
            {decisionReliabilityCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("decisionReliability.compare.heading")}</Heading>
                <Text color="secondary" as="p">
                  {decisionReliabilityCompareStatus.comparison.moreReliableCaseId
                    ? t("decisionReliability.compare.moreReliable", {
                        ticker:
                          (decisionReliabilityCompareStatus.comparison.moreReliableCaseId ===
                          decisionReliabilityCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("decisionReliability.compare.moreReliableTie")}
                </Text>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionReliability.compare.sharedLimitingHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionReliabilityCompareStatus.comparison.sharedLimiting.length > 0
                      ? decisionReliabilityCompareStatus.comparison.sharedLimiting.map((ref) => referenceCodeLabel(ref, t)).join(" · ")
                      : t("decisionReliability.compare.noSharedLimiting")}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionReliability.compare.differingLimitingHeading", { ticker: tickerA ?? "" })}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionReliabilityCompareStatus.comparison.differingLimitingA.length > 0
                      ? decisionReliabilityCompareStatus.comparison.differingLimitingA.map((ref) => referenceCodeLabel(ref, t)).join(" · ")
                      : t("decisionReliability.compare.noDifferingLimiting", { ticker: tickerA ?? "" })}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionReliability.compare.differingLimitingHeading", { ticker: tickerB ?? "" })}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionReliabilityCompareStatus.comparison.differingLimitingB.length > 0
                      ? decisionReliabilityCompareStatus.comparison.differingLimitingB.map((ref) => referenceCodeLabel(ref, t)).join(" · ")
                      : t("decisionReliability.compare.noDifferingLimiting", { ticker: tickerB ?? "" })}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("decisionReliability.compare.sharedSupportingHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {decisionReliabilityCompareStatus.comparison.sharedSupporting.length > 0
                      ? decisionReliabilityCompareStatus.comparison.sharedSupporting.map((ref) => referenceCodeLabel(ref, t)).join(" · ")
                      : t("decisionReliability.compare.noSharedSupporting")}
                  </Text>
                </Stack>
              </Stack>
            )}

            {/* Atlas Decision Layer Sprint 8 (Portfolio Decision
                Synthesis, Deliverable 10). Which decision currently
                fits the portfolio better (honest tie), shared
                strengths/weaknesses, shared capital competitors --
                never an overall winner. Shared competitors are shown
                as a real count only: this page has no existing
                ticker lookup for an arbitrary third Case id, and a
                raw technical case id is not investor-facing copy. */}
            {portfolioDecisionCompareStatus.kind === "loaded" && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("portfolioDecision.compare.heading")}</Heading>
                <Text color="secondary" as="p">
                  {portfolioDecisionCompareStatus.comparison.betterPortfolioFitCaseId
                    ? t("portfolioDecision.compare.betterFit", {
                        ticker:
                          (portfolioDecisionCompareStatus.comparison.betterPortfolioFitCaseId ===
                          portfolioDecisionCompareStatus.comparison.a.caseId
                            ? tickerA
                            : tickerB) ?? "",
                      })
                    : t("portfolioDecision.compare.betterFitTie")}
                </Text>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("portfolioDecision.compare.sharedStrengthsHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {portfolioDecisionCompareStatus.comparison.sharedStrengths.length > 0
                      ? portfolioDecisionCompareStatus.comparison.sharedStrengths.map((ref) => portfolioDecisionReferenceLabel(ref, t)).join(" · ")
                      : t("portfolioDecision.compare.noSharedStrengths")}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("portfolioDecision.compare.sharedWeaknessesHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {portfolioDecisionCompareStatus.comparison.sharedWeaknesses.length > 0
                      ? portfolioDecisionCompareStatus.comparison.sharedWeaknesses.map((ref) => portfolioDecisionReferenceLabel(ref, t)).join(" · ")
                      : t("portfolioDecision.compare.noSharedWeaknesses")}
                  </Text>
                </Stack>
                <Stack gap="metadata">
                  <Text as="span" style={{ fontWeight: 600 }}>
                    {t("portfolioDecision.compare.sharedCompetitorsHeading")}
                  </Text>
                  <Text color="secondary" as="p">
                    {portfolioDecisionCompareStatus.comparison.sharedCompetitorCaseIds.length > 0
                      ? t(
                          portfolioDecisionCompareStatus.comparison.sharedCompetitorCaseIds.length === 1
                            ? "portfolioDecision.section.capitalCompetitionSummaryOne"
                            : "portfolioDecision.section.capitalCompetitionSummaryOther",
                          { count: portfolioDecisionCompareStatus.comparison.sharedCompetitorCaseIds.length },
                        )
                      : t("portfolioDecision.compare.noSharedCompetitors")}
                  </Text>
                </Stack>
              </Stack>
            )}

            {/* Atlas Intelligence Sprint 3 (Decision Explainability &
                Evidence Trace, Deliverable 7). The Stance comparison
                above already answers "which view is more favorable" --
                this answers the follow-up "why," per-reason, without
                computing anything new: a real cross-reference of each
                company's own already-classified evidence codes. Tucked
                behind one `ExpandableDetail` so the page stays calm by
                default. */}
            {explanationStatus.kind === "loaded" && tickerA && tickerB && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <ExpandableDetail summaryLabel={t("explainability.compare.heading")}>
                  <Stack gap="inter-section">
                    <Stack gap="metadata">
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("explainability.compare.favoringALabel", { ticker: tickerA })}
                      </Text>
                      {explanationStatus.comparison.favoringA.length > 0 ? (
                        explanationStatus.comparison.favoringA.map((reason, index) => (
                          <Text key={index} color="tertiary" as="p">
                            {stanceReasonSentence(reason, t)}
                          </Text>
                        ))
                      ) : (
                        <Text color="tertiary">{t("explainability.compare.noneFavoring")}</Text>
                      )}
                    </Stack>
                    <Stack gap="metadata">
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("explainability.compare.favoringBLabel", { ticker: tickerB })}
                      </Text>
                      {explanationStatus.comparison.favoringB.length > 0 ? (
                        explanationStatus.comparison.favoringB.map((reason, index) => (
                          <Text key={index} color="tertiary" as="p">
                            {stanceReasonSentence(reason, t)}
                          </Text>
                        ))
                      ) : (
                        <Text color="tertiary">{t("explainability.compare.noneFavoring")}</Text>
                      )}
                    </Stack>
                    <Stack gap="metadata">
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("explainability.compare.sharedLabel")}
                      </Text>
                      {explanationStatus.comparison.shared.length > 0 ? (
                        explanationStatus.comparison.shared.map((reason, index) => (
                          <Text key={index} color="tertiary" as="p">
                            {stanceReasonSentence(reason, t)}
                          </Text>
                        ))
                      ) : (
                        <Text color="tertiary">{t("explainability.compare.noneShared")}</Text>
                      )}
                    </Stack>
                    <Stack gap="metadata">
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("explainability.compare.missingForBothLabel")}
                      </Text>
                      {explanationStatus.comparison.missingForBoth.length > 0 ? (
                        explanationStatus.comparison.missingForBoth.map((dimension) => (
                          <Text key={dimension} color="tertiary" as="p">
                            {coverageDimensionLabel(dimension, t)}
                          </Text>
                        ))
                      ) : (
                        <Text color="tertiary">{t("explainability.compare.noneMissingForBoth")}</Text>
                      )}
                    </Stack>
                  </Stack>
                </ExpandableDetail>
              </Stack>
            )}

            {/* Atlas Intelligence Sprint 4 (Evidence Quality &
                Conflict Resolution, Deliverable 8). If Atlas prefers
                one company over the other (Portfolio Fit's own
                conclusion below, or Stance's above), the investor
                should immediately see whether that preference rests on
                stronger evidence or merely a better-looking conclusion
                -- this section is deliberately placed before the final
                conclusion, not after, so it informs the read rather
                than defending it. */}
            {evidenceQualityStatus.kind === "loaded" && tickerA && tickerB && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("evidenceQuality.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  <Stack gap="metadata">
                    <Text color="tertiary" as="span">
                      {tickerA}
                    </Text>
                    <StatusBadge
                      label={t(EVIDENCE_QUALITY_LEVEL_KEY[evidenceQualityStatus.reportA.quality])}
                      tone={EVIDENCE_QUALITY_LEVEL_TONE[evidenceQualityStatus.reportA.quality]}
                    />
                  </Stack>
                  <Stack gap="metadata">
                    <Text color="tertiary" as="span">
                      {tickerB}
                    </Text>
                    <StatusBadge
                      label={t(EVIDENCE_QUALITY_LEVEL_KEY[evidenceQualityStatus.reportB.quality])}
                      tone={EVIDENCE_QUALITY_LEVEL_TONE[evidenceQualityStatus.reportB.quality]}
                    />
                  </Stack>
                </Inline>
              </Stack>
            )}

            {/* Atlas Intelligence Sprint 5/6 (Evidence Timeline &
                Historical Understanding, Deliverable 8/12). Shows which
                company's evidence changed most recently and which is
                stable -- history informs the read, it never ranks the
                companies (no "winner" is declared here, unlike the
                final conclusion below). Each side reports its own
                honest state independently (empty history / baseline /
                no material change / material transitions + new source
                evidence) -- never a forced side-by-side comparison when
                one or both companies lack sufficient history. */}
            {evidenceTimelineStatus.kind === "loaded" && tickerA && tickerB && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("evidenceTimeline.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[
                    { ticker: tickerA, entries: evidenceTimelineStatus.entriesA },
                    { ticker: tickerB, entries: evidenceTimelineStatus.entriesB },
                  ].map(({ ticker, entries }) => {
                    const latest = entries[entries.length - 1];
                    const prominentTransitions = latest ? materialTransitions(latest.history.transitions) : [];
                    const noHistoricalChange = !latest || (prominentTransitions.length === 0 && latest.history.newSourceEvidence.length === 0);
                    const { shown: shownSourceEvidence, overflowCount: sourceEvidenceOverflow } = latest
                      ? prominentSourceEvidence(latest.history.newSourceEvidence)
                      : { shown: [], overflowCount: 0 };
                    return (
                      <Stack key={ticker} gap="metadata">
                        <Text color="tertiary" as="span">
                          {ticker}
                        </Text>
                        {!latest && <Text color="tertiary">{t("evidenceTimeline.panel.emptyHistory")}</Text>}
                        {latest?.history.isBaseline && <Text color="tertiary">{t("evidenceTimeline.panel.baselineNote")}</Text>}
                        {latest && !latest.history.isBaseline && noHistoricalChange && (
                          <Text color="tertiary">{t("evidenceTimeline.panel.noChangeNote")}</Text>
                        )}
                        {latest && !latest.history.isBaseline && shownSourceEvidence.map((event, index) => (
                          <Text key={index} color="tertiary" as="span">
                            {sourceEvidenceSentence(event, t)}
                          </Text>
                        ))}
                        {latest && !latest.history.isBaseline && sourceEvidenceOverflow > 0 && (
                          <Text color="tertiary" as="span">{t("evidenceTimeline.sourceEvidence.overflowNote", { count: sourceEvidenceOverflow })}</Text>
                        )}
                        {latest && !latest.history.isBaseline && prominentTransitions.map((transition) => (
                          <Inline key={transition.id} gap="metadata" align="center">
                            <StatusBadge
                              label={transitionCategoryLabel(transition.category, t)}
                              tone={EVIDENCE_TRANSITION_DIRECTION_TONE[transition.direction]}
                            />
                            <Text color="tertiary" as="span">
                              {transitionSentence(transition, t)}
                            </Text>
                          </Inline>
                        ))}
                      </Stack>
                    );
                  })}
                </Inline>
              </Stack>
            )}

            {/* Atlas Intelligence -- Materiality & Priority Engine,
                Deliverable 8. Compare what actually matters, not every
                observation: each company's own single most material
                advantage/uncertainty/missing-evidence pick, plus
                whether their two strongest advantages happen to be the
                same real reason (a genuine shared strength, never
                fabricated when they differ). */}
            {materialityStatus.kind === "loaded" && tickerA && tickerB && (
              <Stack gap="metadata">
                <Divider tone="hairline" />
                <Heading level={3}>{t("materiality.compare.heading")}</Heading>
                <Inline gap="inter-section" wrap align="start">
                  {[
                    { ticker: tickerA, assessment: materialityStatus.assessmentA },
                    { ticker: tickerB, assessment: materialityStatus.assessmentB },
                  ].map(({ ticker, assessment }) => (
                    <Stack key={ticker} gap="metadata">
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("materiality.compare.advantageLabel", { ticker })}
                      </Text>
                      <Text color="tertiary" as="p">
                        {assessment.topSupportingEvidence
                          ? materialEvidenceSentence(assessment.topSupportingEvidence, t)
                          : t("materiality.compare.noneAdvantage")}
                      </Text>
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("materiality.compare.uncertaintyLabel")}
                      </Text>
                      <Text color="tertiary" as="p">
                        {assessment.topContradictingEvidence
                          ? materialEvidenceSentence(assessment.topContradictingEvidence, t)
                          : assessment.topLimitingFactor
                            ? materialEvidenceSentence(assessment.topLimitingFactor, t)
                            : t("materiality.compare.noneAdvantage")}
                      </Text>
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("materiality.compare.missingLabel")}
                      </Text>
                      <Text color="tertiary" as="p">
                        {assessment.topMissingEvidence
                          ? coverageDimensionLabel(assessment.topMissingEvidence.dimension, t)
                          : t("materiality.compare.noneAdvantage")}
                      </Text>
                    </Stack>
                  ))}
                </Inline>
                {materialityStatus.assessmentA.topSupportingEvidence &&
                  materialityStatus.assessmentB.topSupportingEvidence &&
                  materialityStatus.assessmentA.topSupportingEvidence.reason.code ===
                    materialityStatus.assessmentB.topSupportingEvidence.reason.code && (
                    <Stack gap="metadata">
                      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
                        {t("materiality.compare.sharedStrengthLabel")}
                      </Text>
                      <Text color="tertiary" as="p">
                        {materialEvidenceSentence(materialityStatus.assessmentA.topSupportingEvidence, t)}
                      </Text>
                    </Stack>
                  )}
              </Stack>
            )}

            <Divider tone="hairline" />
            <Stack gap="metadata">
              <Heading level={3}>
                {status.comparison.preferredTicker
                  ? t("discovery.compare.conclusionPreferred", { ticker: status.comparison.preferredTicker })
                  : t("discovery.compare.conclusionTie")}
              </Heading>
              {status.comparison.reasoning.map((line, index) => (
                <Text key={index} color="secondary" as="p">
                  {line}
                </Text>
              ))}
              {/* Atlas Intelligence Sprint 2 (Deliverable 1 -- live-
                  verification finding): a genuine, live-discovered
                  tension -- Stance above can honestly say "cannot
                  compare" (e.g. both companies too uncertain) in the
                  exact same moment Portfolio Fit below still names a
                  preferred ticker (a real, narrower, dimension-by-
                  dimension fact that does not require the same
                  confidence bar Stance's own gating does). Both claims
                  are individually true; shown back to back with no
                  context they read as a contradiction. This note
                  disambiguates rather than suppressing either real
                  fact -- Portfolio Fit's own logic is untouched. */}
              {stanceStatus.kind === "loaded" &&
                stanceStatus.comparison.preferredTicker === null &&
                status.comparison.preferredTicker !== null && (
                  <Text color="tertiary" as="p">
                    {t("stance.compare.fitScopeNote")}
                  </Text>
                )}
            </Stack>
            {/* Product Sprint 11 (Investment Workflow Excellence,
                Deliverable 1/3/4): previously navigated to Candidate
                Detail -- an unnecessary interruption that just re-showed
                the same Fit dimensions already visible on this page,
                before a second click into the actual Investment Case.
                `assessment.caseId` is already on hand from the same
                `comparePortfolioFit` response driving this whole page,
                so this goes straight to the real decision surface, one
                hop shorter. Also: `variant="tertiary"` regardless of the
                conclusion just stated above them -- after Atlas has said
                "NVDA fits better," the next click should look like the
                obvious one, not a coin flip between two equally-weighted
                buttons. Ties (no `preferredTicker`) keep both tertiary,
                matching "no single obvious next step" for a genuine
                tie. */}
            <Inline gap="row">
              <Button
                variant={status.comparison.preferredTicker === status.comparison.assessmentA.ticker ? "primary" : "tertiary"}
                onClick={() =>
                  navigate(`/investment-case/${status.comparison.assessmentA.caseId}`, {
                    state: { origin: "discovery", ticker: status.comparison.assessmentA.ticker },
                  })
                }
              >
                {t("discovery.compare.openTicker", { ticker: status.comparison.assessmentA.ticker })}
              </Button>
              <Button
                variant={status.comparison.preferredTicker === status.comparison.assessmentB.ticker ? "primary" : "tertiary"}
                onClick={() =>
                  navigate(`/investment-case/${status.comparison.assessmentB.caseId}`, {
                    state: { origin: "discovery", ticker: status.comparison.assessmentB.ticker },
                  })
                }
              >
                {t("discovery.compare.openTicker", { ticker: status.comparison.assessmentB.ticker })}
              </Button>
            </Inline>
          </Stack>
        )}
      </Stack>
    </Container>
  );
}

function ComparisonColumn({ heading, assessment }: { heading: string; assessment: FitComparisonView["assessmentA"] }) {
  const { t } = useTranslation();
  const dimensionByKind = new Map(assessment.dimensions.map((d) => [d.kind, d]));
  return (
    <Surface tier="primary" style={{ flex: "1 1 280px", minWidth: 0 }}>
      <Stack gap="metadata">
        <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
          <Heading level={4}>{heading}</Heading>
          <FitBadge rating={assessment.overall} />
        </Inline>
        {DIMENSION_ORDER.map((kind) => {
          const dimension = dimensionByKind.get(kind);
          return (
            <Inline key={kind} gap="row" align="center" style={{ justifyContent: "space-between" }}>
              <Text as="span" color="secondary">
                {t(FIT_DIMENSION_KEY[kind])}
              </Text>
              <FitBadge rating={dimension?.rating ?? "unavailable"} />
            </Inline>
          );
        })}
      </Stack>
    </Surface>
  );
}
