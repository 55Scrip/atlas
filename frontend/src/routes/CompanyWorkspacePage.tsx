import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, StatusBadge, StatusText, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { useAlphaWatchlist } from "../discovery/watchlistActions";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import {
  deriveActivity,
  deriveOutstandingWork,
  formatRelativeTime,
  sortActivity,
  type ActivityEvent,
  type DecisionRecord,
  type HoldingLite,
  type OutcomeRecord,
  type TradeLogEntry,
} from "../activity/deriveActivity";
import {
  ANALYSIS_COVERAGE_LEVEL_KEY,
  ANALYSIS_COVERAGE_TONE,
  CONFIDENCE_KEY,
  CONFIDENCE_TONE,
  CONVICTION_LEVEL_KEY,
  CONVICTION_TONE,
  MISSING_EVALUATION_COPY_KEY,
  OUTLOOK_ALIGNMENT_KEY,
  REVIEW_PRIORITY_KEY,
  REVIEW_PRIORITY_TONE,
  RISK_STATUS_TONE,
  type AnalysisCoverageLevel,
  type ConvictionLevel,
  type ConvictionReasonCode,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
  type MissingEvaluationCategory,
  type OutlookRecommendationRelationship,
  type ReviewPriority,
  type ValuationSupportGapKind,
  type ValuationSupportStatus,
} from "../status/statusTone";
import {
  OPEN_QUESTION_ORIGIN_KEY,
  RISK_CATEGORY_KEY,
  RISK_STATUS_KEY,
  humanize,
  type AnalysisBusinessStatus,
  type AnalysisHighlightKind,
  type AnalysisOpenQuestionOrigin,
  type AnalysisRiskCategory,
  type AnalysisRiskStatus,
  type AnalysisThesisImpact,
  type AnalysisValuationStatus,
  type ChangeFindingView,
  type Translate,
} from "../changeIntelligence/describeChange";
import { deriveLimitingFactors, type LimitingFactor, type OutstandingWorkKind } from "../investmentCase/deriveExecutiveSummary";
import { LimitingFactorsCard } from "../investmentCase/LimitingFactorsCard";
import { HeroCard, STRENGTH_SENTENCE_KEY, CHALLENGE_SENTENCE_KEY, type HeroAnalysisInput } from "../investmentCase/HeroCard";
import { InvestmentArgumentSection } from "../investmentCase/InvestmentArgumentSection";
import type { ReasoningFacts } from "../investmentCase/AtlasReasoningSection";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { WhatChangedSection } from "../investmentCase/WhatChangedSection";
import { AtlasOutlookSection, type OutlookView } from "../investmentCase/AtlasOutlookSection";
import type { CoverageAssessmentView } from "../coverage/coverageApi";
import type { StanceView } from "../stance/stanceApi";

/**
 * Company Workspace v1 (Atlas Beta Company Workspace Implementation
 * Sprint) -- the investor's per-company working surface, reachable for
 * any ticker Atlas already has a Case for (currently: every Portfolio
 * holding and every Watchlist entry -- see this file's own resolution
 * step below). Sits between Portfolio Workspace and Investment Case in
 * the approved flow: Portfolio -> Company -> Investment Case -> Record
 * Decision -> back to Company or Portfolio.
 *
 * Reuses the exact same `GET /api/cases/{caseId}/analysis` payload
 * Investment Case already fetches (`InvestmentCaseAnalysisView`,
 * redeclared locally here the same way `InvestmentCasePage.tsx` already
 * declares its own copy -- no shared export exists for this wire shape
 * yet, so this mirrors the established per-page convention rather than
 * introducing a new one). No new backend endpoint. "Current Picture"
 * reuses `HeroCard` verbatim (the exact same real Decision Support /
 * Conviction / Risk / Valuation Support / Key Metrics construction
 * Investment Case's own header already performs) rather than
 * re-implementing a second version of that derivation.
 *
 * Ticker -> Case resolution: there is no `GET /cases/by-ticker`
 * endpoint (confirmed via backend audit) -- every real Case is reached
 * by `caseId`. This page resolves the ticker client-side against
 * `GET /alpha-portfolio` (Portfolio holdings) and `GET /alpha-watchlist`
 * (Watchlist entries), exactly the same two real, already-used
 * endpoints `DiscoveryPage.tsx`/`DailyBriefPage.tsx` already fetch for
 * the same purpose. A ticker in neither list has no Case to show --
 * this page never calls `POST /alpha-watchlist` itself (a page load
 * must never silently create data).
 */

interface AlphaHoldingLite {
  ticker: string;
  caseId: string | null;
  weightPercent: number;
  valueAbsolute: number | null;
  reconciliationStatus: "NONE" | "UPDATED" | "AWAITING_RECONCILIATION";
}

interface WatchlistEntryLite {
  ticker: string;
  caseId: string;
}

interface CockpitHoldingLite {
  ticker: string;
  analysisCoverage: { level: AnalysisCoverageLevel };
  attention: { priority: ReviewPriority };
}

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

interface MarketSnapshotView {
  asOf: string;
  sharePrice: number | null;
  sharesOutstanding: number | null;
  currency: string | null;
  marketCap: number | null;
}

interface CurrentThesisView {
  latestDecisionReason: string | null;
  latestDecisionType: string | null;
  latestObservationStatement: string | null;
}

interface AtlasThesisView {
  posture: string;
  narrative: string;
  supportingHighlightIds: string[];
  keyUncertaintyOrigins: string[];
}

interface CaseHighlightView {
  kind: AnalysisHighlightKind;
  supportingFindingId: string;
  evidenceReferences: string[];
}

interface BusinessFindingLite {
  kind: string;
  status: AnalysisBusinessStatus;
  /** Product Sprint 13 (Company Intelligence Excellence, Deliverable 6):
   * widened from kind/status only -- same `/api/cases/{caseId}/analysis`
   * payload `InvestmentCasePage.tsx`'s own `BusinessFindingView` already
   * reads these two fields from; this page just hadn't typed them yet. */
  supportingEvidence: string[];
  contradictingEvidence: string[];
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

/** Product Sprint 13: same `analysis.valuation.findings` array
 * `InvestmentCasePage.tsx` already reads for its own `fcfYield` lookup
 * -- only the `kind`/`supportingFacts`/`contradictingFacts` this page
 * needs, not the fuller shape. */
interface ValuationFindingLite {
  kind: string;
  supportingFacts: string[];
  contradictingFacts: string[];
}

interface ValuationContextView {
  fcfYieldStatus: AnalysisValuationStatus;
  currentYield: number | null;
  scenarioAvailable: boolean;
  evidenceReferences: string[];
}

interface OpenQuestionView {
  kind: AnalysisOpenQuestionOrigin | "no_evidence_recorded_for_case" | "observation_without_evidence" | "decision_without_linked_observation";
  reference: string | null;
}

interface RecommendationStateView {
  level: DecisionSupportLevel;
  badgeLabel: string;
  statement: string;
  convictionGateMet: boolean;
  outlookAlignment: { shortTerm: OutlookRecommendationRelationship; longTerm: OutlookRecommendationRelationship };
  missingEvaluations: MissingEvaluationCategory[];
}

interface HoldingContextView {
  held: boolean;
  ticker: string | null;
  weightPercent: number | null;
  valueAbsolute: number | null;
  reconciliationStatus: string | null;
}

interface InvestmentCaseAnalysisView {
  caseId: string;
  holdingContext: HoldingContextView;
  currentThesis: CurrentThesisView;
  isThesisStale: boolean;
  confidence: EvidenceCoverageLevel;
  conviction: { level: ConvictionLevel; reasons: string[] };
  coverage: CoverageAssessmentView;
  stance: StanceView | null;
  businessAnalysis: { findings: BusinessFindingLite[] };
  valuationSupport: { status: ValuationSupportStatus; gap: ValuationSupportGapKind | null };
  risk: { findings: RiskFindingView[] };
  valuation: { findings: ValuationFindingLite[] };
  evidenceQuality: { coverage: EvidenceCoverageLevel } | null;
  openQuestions: OpenQuestionView[];
  recommendation: RecommendationStateView;
  companyProfile: CompanyProfileView | null;
  financialHistory: unknown[];
  marketSnapshot: MarketSnapshotView | null;
  strengths: CaseHighlightView[];
  risks: CaseHighlightView[];
  valuationContext: ValuationContextView;
  atlasThesis: AtlasThesisView;
  outlook: OutlookView;
  changeIntelligenceAvailable: boolean;
  isBaselineCase: boolean;
  latestChanges: ChangeFindingView[];
  thesisChange: AnalysisThesisImpact;
  currentAnalysisAt: string;
}

/** The three `OpenQuestionKind` members that are specifically about
 * missing evidence -- mirrors `InvestmentCasePage.tsx`'s own
 * `EVIDENCE_GAP_QUESTION_KINDS` constant exactly (same backend enum,
 * same split), so this page's "missing evidence" count never disagrees
 * with Investment Case's own count for the same Case. */
const EVIDENCE_GAP_QUESTION_KINDS = [
  "no_evidence_recorded_for_case",
  "observation_without_evidence",
  "decision_without_linked_observation",
];

/** Localization & Language Integrity Sprint: `EVIDENCE_GAP_QUESTION_KINDS`
 * aren't part of `AnalysisOpenQuestionOrigin` (`OPEN_QUESTION_ORIGIN_KEY`
 * only covers that narrower enum), so every question rendered below was
 * silently falling through to `humanize()` -- e.g. the raw
 * "decision without linked observation" enum text, in English only,
 * regardless of the selected language. Reuses the exact translation keys
 * `InvestmentCasePage.tsx`'s own `OPEN_QUESTION_KEY` already defines for
 * these same three kinds -- no new copy authored. */
type EvidenceGapQuestionKind =
  | "no_evidence_recorded_for_case"
  | "observation_without_evidence"
  | "decision_without_linked_observation";

const EVIDENCE_GAP_QUESTION_KEY: Record<EvidenceGapQuestionKind, TranslationKey> = {
  no_evidence_recorded_for_case: "investmentCase.intelligence.openQuestions.noEvidenceRecordedForCase",
  observation_without_evidence: "investmentCase.intelligence.openQuestions.observationWithoutEvidence",
  decision_without_linked_observation: "investmentCase.intelligence.openQuestions.decisionWithoutLinkedObservation",
};

/** Implementation Sprint B2 (Hero Reordering): the exact resolution
 * `EvidenceCoverageCard` below already performs per-question, factored
 * out so the Hero's own "Open question" field (Decision First's own
 * 8th step) can show the *same* real question, translated the same
 * way, rather than a second, parallel resolution. `null` only when the
 * kind matches neither known vocabulary (never happens for real
 * backend data, but keeps this a total function). */
function resolveOpenQuestionKey(kind: OpenQuestionView["kind"]): TranslationKey | null {
  if (kind in EVIDENCE_GAP_QUESTION_KEY) return EVIDENCE_GAP_QUESTION_KEY[kind as EvidenceGapQuestionKind];
  if (kind in OPEN_QUESTION_ORIGIN_KEY) return OPEN_QUESTION_ORIGIN_KEY[kind as AnalysisOpenQuestionOrigin];
  return null;
}

type ResolutionStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "not-found" }
  | { kind: "resolved"; caseId: string; held: boolean; holdingsLite: HoldingLite[] };

type AnalysisFetchStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; report: InvestmentCaseAnalysisView };

type ActivityFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; decisions: DecisionRecord[]; outcomes: OutcomeRecord[]; trades: TradeLogEntry[] };

export function CompanyWorkspacePage() {
  const { ticker } = useParams<{ ticker: string }>();
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const navigate = useNavigate();

  const [resolution, setResolution] = useState<ResolutionStatus>({ kind: "loading" });
  const [analysis, setAnalysis] = useState<AnalysisFetchStatus>({ kind: "idle" });
  const [cockpit, setCockpit] = useState<CockpitHoldingLite | null>(null);
  const [activity, setActivity] = useState<ActivityFetchStatus>({ kind: "loading" });
  const portfolioResource = useAlphaPortfolio();
  const watchlistResource = useAlphaWatchlist();

  useEffect(() => {
    setAnalysis({ kind: "idle" });
    setCockpit(null);

    if (portfolioResource.kind === "loading" || watchlistResource.kind === "loading") {
      setResolution({ kind: "loading" });
      return;
    }
    if (portfolioResource.kind === "error" || watchlistResource.kind === "error") {
      setResolution({ kind: "error" });
      return;
    }

    const portfolio = portfolioResource.data as { exists: boolean; holdings: AlphaHoldingLite[] };
    const watchlist = watchlistResource.entries;
    const holdings = portfolio.exists ? portfolio.holdings : [];
    const holdingMatch = holdings.find((h) => h.ticker === ticker && h.caseId !== null);
    const watchlistMatch = watchlist.find((w) => w.ticker === ticker);
    const caseId = holdingMatch?.caseId ?? watchlistMatch?.caseId ?? null;
    const holdingsLite: HoldingLite[] = holdings.map((h) => ({
      ticker: h.ticker,
      caseId: h.caseId,
      reconciliationStatus: h.reconciliationStatus,
    }));
    if (!caseId) {
      setResolution({ kind: "not-found" });
      return;
    }
    setResolution({ kind: "resolved", caseId, held: holdingMatch !== undefined, holdingsLite });
  }, [ticker, portfolioResource, watchlistResource]);

  useEffect(() => {
    if (resolution.kind !== "resolved" || !resolution.held) return;
    const controller = new AbortController();
    fetch("/api/alpha-portfolio/cockpit", { signal: controller.signal })
      .then((r) => (r.ok ? (r.json() as Promise<{ holdings: CockpitHoldingLite[] }>) : null))
      .then((body) => {
        if (!body) return;
        const match = body.holdings.find((h) => h.ticker === ticker);
        if (match) setCockpit(match);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolution, ticker]);

  useEffect(() => {
    if (resolution.kind !== "resolved") return;
    const controller = new AbortController();
    setAnalysis({ kind: "loading" });
    fetch(`/api/cases/${resolution.caseId}/analysis`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<InvestmentCaseAnalysisView>;
      })
      .then((report) => setAnalysis({ kind: "loaded", report }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setAnalysis({ kind: "error" });
      });
    return () => controller.abort();
  }, [resolution]);

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
      .then(([decisions, outcomes, trades]) => setActivity({ kind: "loaded", decisions, outcomes, trades }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setActivity({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  if (!ticker) {
    return (
      <Container width="wide">
        <Text color="tertiary" role="alert">
          {t("companyWorkspace.notFound")}
        </Text>
      </Container>
    );
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Text color="tertiary" as="span">
          <RouterLink to="/portfolio" style={ACCENT_LINK_STYLE}>
            {t("companyWorkspace.breadcrumbPortfolio")}
          </RouterLink>{" "}
          / {ticker}
        </Text>

        {resolution.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {resolution.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("companyWorkspace.loadError")}
          </Text>
        )}
        {resolution.kind === "not-found" && (
          <Stack gap="inter-section">
            <Text color="tertiary" role="alert">
              {t("companyWorkspace.notFound")}
            </Text>
            <RouterLink to="/portfolio" style={ACCENT_LINK_STYLE}>
              {t("companyWorkspace.backToPortfolio")}
            </RouterLink>
          </Stack>
        )}

        {resolution.kind === "resolved" && analysis.kind !== "error" && (
          <>
            {analysis.kind === "idle" || analysis.kind === "loading" ? (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            ) : (
              <CompanyWorkspaceLoaded
                ticker={ticker}
                report={analysis.report}
                cockpit={cockpit}
                activity={activity}
                holdingsLite={resolution.holdingsLite}
                navigate={navigate}
                t={t}
                locale={locale}
              />
            )}
          </>
        )}
        {resolution.kind === "resolved" && analysis.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("companyWorkspace.loadError")}
          </Text>
        )}
      </Stack>
    </Container>
  );
}

function CompanyWorkspaceLoaded({
  ticker,
  report,
  cockpit,
  activity,
  holdingsLite,
  navigate,
  t,
  locale,
}: {
  ticker: string;
  report: InvestmentCaseAnalysisView;
  cockpit: CockpitHoldingLite | null;
  activity: ActivityFetchStatus;
  holdingsLite: HoldingLite[];
  navigate: ReturnType<typeof useNavigate>;
  t: Translate;
  locale: string;
}) {
  const held = report.holdingContext.held;
  const freshness = formatRelativeTime(report.currentAnalysisAt, t);

  /** Company Workspace's own "not yet analyzed" state (Phase 13): no
   * company profile has been ingested and no financial history exists
   * yet -- the honest signal that Atlas has not gathered real data for
   * this company, distinct from a settled `insufficient_evidence`
   * conclusion reached after real data was actually examined. */
  const notYetAnalyzed = report.companyProfile === null && report.financialHistory.length === 0;

  function openInvestmentCase() {
    navigate(`/investment-case/${report.caseId}`, { state: { origin: "company", ticker } });
  }

  return (
    <Stack gap="intra-section">
      <CompanyHeader ticker={ticker} report={report} cockpit={cockpit} freshness={freshness} t={t} />

      {notYetAnalyzed ? (
        <NotYetAnalyzedState ticker={ticker} report={report} t={t} />
      ) : (
        <Inline gap="inter-section" wrap align="start">
          <div style={{ flex: "3 1 480px", minWidth: 0 }}>
            <Stack gap="inter-section">
              <CurrentPicture
                ticker={ticker}
                report={report}
                activity={activity}
                holdingsLite={holdingsLite}
                t={t}
                locale={locale}
              />
              <Divider tone="hairline" />
              <InvestmentThesis report={report} t={t} />
              <Divider tone="hairline" />
              <WhatChangedSection
                changeIntelligenceAvailable={report.changeIntelligenceAvailable}
                isBaselineCase={report.isBaselineCase}
                latestChanges={report.latestChanges}
                thesisChange={report.thesisChange}
                factsForDimension={(dimension) => {
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
            </Stack>
          </div>
          <div style={{ flex: "1 1 300px", minWidth: 0 }}>
            <Stack gap="inter-section">
              <DecisionSupportCard report={report} onRecordDecision={openInvestmentCase} t={t} />
              <RiskCard report={report} t={t} />
              <EvidenceCoverageCard report={report} t={t} />
              <RecentActivityCard
                caseId={report.caseId}
                activity={activity}
                holdingsLite={holdingsLite}
                openInvestmentCase={openInvestmentCase}
                t={t}
              />
            </Stack>
          </div>
        </Inline>
      )}
    </Stack>
  );
}

function CompanyHeader({
  ticker,
  report,
  cockpit,
  freshness,
  t,
}: {
  ticker: string;
  report: InvestmentCaseAnalysisView;
  cockpit: CockpitHoldingLite | null;
  freshness: string;
  t: Translate;
}) {
  const holding = report.holdingContext;
  const companyName = report.companyProfile?.name;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
          <Inline gap="row" align="baseline" wrap>
            <Heading level={1} style={{ fontWeight: 700 }}>
              {companyName ?? ticker}
            </Heading>
            {companyName && (
              <Text as="span" color="secondary" style={{ fontSize: "var(--type-size-h4)" }}>
                {ticker}
              </Text>
            )}
          </Inline>
          {cockpit && cockpit.attention.priority !== "none" && (
            <Inline gap="row" align="center" wrap>
              <StatusBadge
                label={t(REVIEW_PRIORITY_KEY[cockpit.attention.priority])}
                tone={REVIEW_PRIORITY_TONE[cockpit.attention.priority]}
              />
              <Button variant="tertiary" disabled title={t("companyWorkspace.dismissUnavailable")}>
                {t("companyWorkspace.dismissButton")}
              </Button>
            </Inline>
          )}
        </Inline>

        <Inline gap="inter-section" wrap>
          {holding.held ? (
            <Text as="span" color="secondary">
              {t("companyWorkspace.header.positionValue")}: {holding.valueAbsolute ?? t("portfolio.header.notAvailable")}
              {"  ·  "}
              {t("companyWorkspace.header.positionWeight")}: {holding.weightPercent}%
            </Text>
          ) : (
            <StatusText label={t("companyWorkspace.header.notHeld")} tone="neutral" />
          )}
          {/* Atlas Intelligence Sprint 1: previously read `cockpit
              .analysisCoverage.level`, which only exists for a real
              Portfolio holding (a separate fetch, guarded `cockpit &&`)
              -- a live-tested gap where a Watchlist-only or search-only
              company's own Investment Case showed no coverage badge at
              all. `report.coverage.overallCoverage` is the exact same
              `AnalysisCoverageLevel`, now on Investment Case's own
              response for every Case regardless of holding status. */}
          <StatusText
            label={t(ANALYSIS_COVERAGE_LEVEL_KEY[report.coverage.overallCoverage])}
            tone={ANALYSIS_COVERAGE_TONE[report.coverage.overallCoverage]}
          />
          {report.companyProfile?.sector && (
            <Text as="span" color="tertiary">
              {report.companyProfile.sector}
            </Text>
          )}
        </Inline>

        <Text as="p" color="tertiary">
          {t("companyWorkspace.header.lastUpdated", { when: freshness })}
        </Text>

        {/* Product Sprint 10 (Navigation & Workflow Excellence,
            Deliverable 1/4/10): Company Workspace previously had no path
            to Compare at all -- reuses the exact `?a=<ticker>` route
            every other Tier-1 page already links into, and the exact
            same `investmentCase.header.compareLink` copy Investment
            Case's own identical link already uses, rather than a second,
            differently-worded key for the same action. */}
        <RouterLink to={`/discovery/compare?a=${encodeURIComponent(ticker)}`} style={ACCENT_LINK_STYLE}>
          {t("investmentCase.header.compareLink")}
        </RouterLink>
      </Stack>
    </Surface>
  );
}

function CurrentPicture({
  ticker,
  report,
  activity,
  holdingsLite,
  t,
  locale,
}: {
  ticker: string;
  report: InvestmentCaseAnalysisView;
  activity: ActivityFetchStatus;
  holdingsLite: HoldingLite[];
  t: Translate;
  locale: string;
}) {
  const outstandingWorkKinds =
    activity.kind === "loaded"
      ? deriveOutstandingWork(activity.decisions, activity.outcomes, activity.trades, holdingsLite)
          .filter((item) => item.caseId === report.caseId)
          .map((item) => item.kind)
      : [];

  const growth = report.businessAnalysis.findings.find((f) => f.kind === "growth");
  const capitalAllocation = report.businessAnalysis.findings.find((f) => f.kind === "capital_allocation");
  const longTerm = report.outlook.longTerm;
  const longTermBull = longTerm.scenarios.find((s) => s.kind === "bull");
  const longTermBear = longTerm.scenarios.find((s) => s.kind === "bear");
  const riskFindings = report.risk.findings.map((f) => ({ category: f.category, status: f.status }));
  const valuationSupportStatus = report.valuationSupport.status;
  const valuationSupportGap = report.valuationSupport.gap;
  const limitingFactors: LimitingFactor[] = deriveLimitingFactors({
    riskFindings,
    valuationSupportStatus,
    valuationSupportGap,
  });

  const heroAnalysis: HeroAnalysisInput = {
    recommendationLevel: report.recommendation.level,
    convictionLevel: report.conviction.level,
    valuationSupportStatus,
    growthStatus: (growth ? growth.status : "not_evaluated") as AnalysisBusinessStatus,
    capitalAllocationStatus: (capitalAllocation ? capitalAllocation.status : "not_evaluated") as AnalysisBusinessStatus,
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
    stance: report.stance,
    convictionReasonCodes: report.conviction.reasons as ConvictionReasonCode[],
  };

  // Implementation Sprint B2 (Hero Reordering): the same real question
  // `EvidenceCoverageCard` shows in its own expandable detail, promoted
  // once (the first) into the Hero's own "Open question" step -- never
  // a second, different question invented for the Hero specifically.
  const primaryOpenQuestion = report.openQuestions[0];
  const primaryOpenQuestionKey = primaryOpenQuestion ? resolveOpenQuestionKey(primaryOpenQuestion.kind) : null;

  return (
    <Stack gap="metadata">
      <Label>{t("companyWorkspace.currentPicture.heading")}</Label>
      <HeroCard
        ticker={ticker}
        analysis={heroAnalysis}
        outstandingWorkKinds={outstandingWorkKinds}
        isThesisStale={report.isThesisStale}
        openQuestionCount={report.openQuestions.length}
        primaryOpenQuestionKey={primaryOpenQuestionKey}
        t={t}
        locale={locale}
      />
    </Stack>
  );
}

function InvestmentThesis({ report, t }: { report: InvestmentCaseAnalysisView; t: Translate }) {
  const narrative =
    report.currentThesis.latestDecisionReason ??
    report.currentThesis.latestObservationStatement ??
    (report.atlasThesis.narrative || null);
  const strengthKinds = report.strengths.map((s) => s.kind);
  const riskKinds = report.risks.map((r) => r.kind);

  /** Product Sprint 13 (Company Intelligence Excellence, Deliverable 6):
   * same resolver as `InvestmentCasePage.tsx`'s own `factsForHighlightKind`
   * -- reuses the finding each kind already maps to for its real
   * supporting/contradicting facts, rather than the bare category
   * sentence alone. */
  function factsForKind(kind: AnalysisHighlightKind): ReasoningFacts {
    if (kind === "financial_risk" || kind === "business_risk" || kind === "valuation_risk") {
      const finding = report.risk.findings.find((f) => f.category === kind);
      return { supporting: finding?.supportingFacts ?? [], contradicting: finding?.contradictingFacts ?? [] };
    }
    if (kind === "valuation") {
      const finding = report.valuation.findings.find((f) => f.kind === "fcf_yield_relative");
      return { supporting: finding?.supportingFacts ?? [], contradicting: finding?.contradictingFacts ?? [] };
    }
    const finding = report.businessAnalysis.findings.find((f) => f.kind === kind);
    return { supporting: finding?.supportingEvidence ?? [], contradicting: finding?.contradictingEvidence ?? [] };
  }

  return (
    <Stack gap="metadata">
      <Label>{t("companyWorkspace.thesis.heading")}</Label>
      {narrative ? (
        <Text as="p">{narrative}</Text>
      ) : (
        <Text color="tertiary" as="p">
          {t("companyWorkspace.thesis.empty")}
        </Text>
      )}
      <Inline gap="inter-section" wrap>
        {report.strengths[0] && (
          <Text as="span" color="secondary">
            + {t(STRENGTH_SENTENCE_KEY[report.strengths[0].kind])}
          </Text>
        )}
        {report.risks[0] && (
          <Text as="span" color="secondary">
            − {t(CHALLENGE_SENTENCE_KEY[report.risks[0].kind])}
          </Text>
        )}
      </Inline>
      <ExpandableDetail summaryLabel={t("companyWorkspace.thesis.viewFull")}>
        <InvestmentArgumentSection
          strengthKinds={strengthKinds}
          riskKinds={riskKinds}
          openQuestionOrigins={report.openQuestions
            .filter((q): q is OpenQuestionView & { kind: AnalysisOpenQuestionOrigin } => q.kind in OPEN_QUESTION_ORIGIN_KEY)
            .map((q) => q.kind)}
          factsForKind={factsForKind}
          t={t}
        />
      </ExpandableDetail>
    </Stack>
  );
}

function DecisionSupportCard({
  report,
  onRecordDecision,
  t,
}: {
  report: InvestmentCaseAnalysisView;
  onRecordDecision: () => void;
  t: Translate;
}) {
  const rec = report.recommendation;
  const riskFindings = report.risk.findings.map((f) => ({ category: f.category, status: f.status }));
  const limitingFactors = deriveLimitingFactors({
    riskFindings,
    valuationSupportStatus: report.valuationSupport.status,
    valuationSupportGap: report.valuationSupport.gap,
  });
  const supportingStrengths = report.strengths.slice(0, 2);

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        {/* Status Consolidation (Implementation Sprint B3): the
            Recommendation badge + statement this card used to lead with
            duplicated the exact same `report.recommendation.level`
            HeroCard already shows as the page's own primary message,
            above, in `CurrentPicture`. This card now shows only what
            Hero doesn't -- the fuller decision-support detail below and
            the real "Record Decision" action -- reinforcing the one
            recommendation instead of restating it. */}
        <Label>{t("companyWorkspace.decisionSupport.heading")}</Label>
        {rec.level === "insufficient_evidence" && rec.missingEvaluations.length > 0 && (
          <Stack gap="metadata">
            {rec.missingEvaluations.map((category) => (
              <Text as="p" color="tertiary" key={category}>
                {t(MISSING_EVALUATION_COPY_KEY[category])}
              </Text>
            ))}
          </Stack>
        )}

        <ExpandableDetail summaryLabel={t("companyWorkspace.decisionSupport.viewFull")}>
          <Stack gap="metadata">
            {rec.outlookAlignment.longTerm !== "unavailable" && (
              <Text as="p" color="tertiary">
                {t(OUTLOOK_ALIGNMENT_KEY[rec.outlookAlignment.longTerm])}
              </Text>
            )}
            {limitingFactors.length > 0 && <LimitingFactorsCard factors={limitingFactors} t={t} />}
            {supportingStrengths.length > 0 && (
              <Stack gap="metadata">
                <Text as="p" style={{ fontWeight: 600 }}>
                  {t("companyWorkspace.decisionSupport.supportingHeading")}
                </Text>
                {supportingStrengths.map((s, index) => (
                  <Text as="p" color="secondary" key={`${s.kind}-${index}`}>
                    {t(STRENGTH_SENTENCE_KEY[s.kind])}
                  </Text>
                ))}
              </Stack>
            )}
          </Stack>
        </ExpandableDetail>

        <Divider tone="hairline" />
        <Text as="p" color="tertiary">
          {t("companyWorkspace.decisionSupport.disclaimer")}
        </Text>
        <Button variant="primary" onClick={onRecordDecision}>
          {t("companyWorkspace.decisionSupport.recordButton")}
        </Button>
      </Stack>
    </Surface>
  );
}

/**
 * Risk (Phase 10) -- the real four-category vector
 * (`report.risk.findings`), shown as its own distinct card rather than
 * folded silently into Decision Support's limiting factors -- Conviction/
 * Decision Support/Risk/Analysis Coverage must stay visually distinct
 * (Phase 9). No aggregate risk score exists in the backend and none is
 * computed here; each category renders its own real status.
 */
function RiskCard({ report, t }: { report: InvestmentCaseAnalysisView; t: Translate }) {
  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Label>{t("companyWorkspace.risk.heading")}</Label>
        <Stack gap="row">
          {report.risk.findings.map((finding) => (
            <Inline key={finding.category} gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
              <Text as="span">{t(RISK_CATEGORY_KEY[finding.category])}</Text>
              <StatusBadge label={t(RISK_STATUS_KEY[finding.status])} tone={RISK_STATUS_TONE[finding.status]} />
            </Inline>
          ))}
        </Stack>
      </Stack>
    </Surface>
  );
}

function EvidenceCoverageCard({
  report,
  t,
}: {
  report: InvestmentCaseAnalysisView;
  t: Translate;
}) {
  const missingCount = report.openQuestions.filter((q) => EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind)).length;
  const missingQuestions = report.openQuestions.filter((q) => EVIDENCE_GAP_QUESTION_KINDS.includes(q.kind));

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Label>{t("companyWorkspace.evidence.heading")}</Label>
        <Inline gap="row" wrap>
          <Text as="span" color="secondary">
            {t("companyWorkspace.evidence.coverageLabel")}: {t(CONFIDENCE_KEY[report.confidence])}
          </Text>
        </Inline>
        <Text as="p" color="tertiary">
          {t("investmentCase.analysis.confidence.explanation")}
        </Text>
        {/* Atlas Intelligence Sprint 1: `report.coverage.overallCoverage`
            is the same `AnalysisCoverageLevel` `cockpit.analysisCoverage
            .level` carried, now on Investment Case's own response for
            every Case -- no longer gated on a Portfolio holding. */}
        <Inline gap="row" wrap>
          <Text as="span" color="secondary">
            {t("companyWorkspace.evidence.analysisCoverageLabel")}: {t(ANALYSIS_COVERAGE_LEVEL_KEY[report.coverage.overallCoverage])}
          </Text>
        </Inline>
        <Inline gap="row" wrap>
          <Text as="span" color="secondary">
            {t("companyWorkspace.evidence.missingLabel")}: {missingCount}
          </Text>
        </Inline>
        {missingCount > 0 && (
          <ExpandableDetail summaryLabel={t("companyWorkspace.evidence.viewMissing")}>
            <Stack gap="metadata">
              {missingQuestions.map((q, index) => (
                <Text as="p" color="secondary" key={index}>
                  {(() => {
                    const key = resolveOpenQuestionKey(q.kind);
                    return key ? t(key) : humanize(q.kind);
                  })()}
                </Text>
              ))}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}

const RECENT_ACTIVITY_COUNT = 4;

function RecentActivityCard({
  caseId,
  activity,
  holdingsLite,
  openInvestmentCase,
  t,
}: {
  caseId: string;
  activity: ActivityFetchStatus;
  holdingsLite: HoldingLite[];
  openInvestmentCase: () => void;
  t: Translate;
}) {
  if (activity.kind !== "loaded") return null;

  const events: ActivityEvent[] = sortActivity(
    deriveActivity(activity.decisions, activity.outcomes, activity.trades, holdingsLite).filter(
      (event) => event.caseId === caseId,
    ),
    "newest",
  ).slice(0, RECENT_ACTIVITY_COUNT);

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Label>{t("companyWorkspace.recentActivity.heading")}</Label>
        {events.length === 0 && <Text color="tertiary">{t("companyWorkspace.recentActivity.empty")}</Text>}
        <Stack gap="row">
          {events.map((event) => (
            <Link
              key={`${event.kind}-${event.id}`}
              href="#"
              style={{ color: "var(--color-text-secondary)", textDecoration: "none" }}
              onClick={(clickEvent) => {
                clickEvent.preventDefault();
                openInvestmentCase();
              }}
            >
              {event.summary} · {formatRelativeTime(event.date, t)}
            </Link>
          ))}
        </Stack>
      </Stack>
    </Surface>
  );
}

function NotYetAnalyzedState({ ticker, report, t }: { ticker: string; report: InvestmentCaseAnalysisView; t: Translate }) {
  const holding = report.holdingContext;
  return (
    <Surface tier="primary">
      <Stack gap="inter-section">
        <Heading level={2}>{t("companyWorkspace.notYetAnalyzed.heading")}</Heading>
        <Text as="p" color="secondary">
          {t("companyWorkspace.notYetAnalyzed.explanation")}
        </Text>
        <Stack gap="metadata">
          <Text as="p" style={{ fontWeight: 600 }}>
            {t("companyWorkspace.notYetAnalyzed.knownHeading")}
          </Text>
          <Text as="p" color="secondary">
            {t("companyWorkspace.notYetAnalyzed.knownTicker", { ticker })}
          </Text>
          {holding.held && (
            <Text as="p" color="secondary">
              {t("companyWorkspace.notYetAnalyzed.knownWeight", { percent: holding.weightPercent ?? 0 })}
            </Text>
          )}
        </Stack>
        <Stack gap="metadata">
          <Text as="p" style={{ fontWeight: 600 }}>
            {t("companyWorkspace.notYetAnalyzed.missingHeading")}
          </Text>
          <Text as="p" color="secondary">
            {t("companyWorkspace.notYetAnalyzed.missingBody")}
          </Text>
        </Stack>
        <Text as="p" color="tertiary">
          {t("companyWorkspace.notYetAnalyzed.nextSteps")}
        </Text>
        <RouterLink to="/portfolio" style={ACCENT_LINK_STYLE}>
          {t("companyWorkspace.backToPortfolio")}
        </RouterLink>
      </Stack>
    </Surface>
  );
}
