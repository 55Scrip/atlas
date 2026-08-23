import { useEffect, useState } from "react";
import { useNavigate, useParams, Link as RouterLink } from "react-router-dom";
import { Container, Divider, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { fetchPortfolioFitForTicker, fetchPortfolioFitForHoldings, type PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { DiscoveryCandidateCard } from "./DiscoveryCandidateCard";
import { addTickerToWatchlist, removeTickerFromWatchlist, fetchWatchlist, type WatchlistEntryView } from "./watchlistActions";
import { fetchStanceForTicker, type StanceView } from "../stance/stanceApi";
import { EvidenceGraphSection } from "../evidenceGraph/EvidenceGraphSection";
import { fetchEvidenceGraph, type EvidenceGraphView } from "../evidenceGraph/evidenceGraphApi";
import { DecisionReadinessSection } from "../decisionReadiness/DecisionReadinessSection";
import {
  fetchDecisionReadiness,
  fetchDecisionReadinessChange,
  type DecisionReadinessChangeView,
  type DecisionReadinessView,
} from "../decisionReadiness/decisionReadinessApi";
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
import {
  fetchOpportunityCost,
  fetchOpportunityCostChange,
  type OpportunityCostChangeView,
  type OpportunityCostView,
} from "../opportunityCost/opportunityCostApi";
import { DecisionMemorySection } from "../decisionMemory/DecisionMemorySection";
import { fetchDecisionMemory, type DecisionMemoryView } from "../decisionMemory/decisionMemoryApi";
import { DecisionExplanationSection } from "../decisionExplanation/DecisionExplanationSection";
import { fetchDecisionExplanation, type DecisionExplanationView } from "../decisionExplanation/decisionExplanationApi";
import { DecisionReliabilitySection } from "../decisionReliability/DecisionReliabilitySection";
import { fetchDecisionReliability, type DecisionReliabilityView } from "../decisionReliability/decisionReliabilityApi";
import { PortfolioDecisionSection } from "../portfolioDecision/PortfolioDecisionSection";
import { fetchPortfolioDecision, type PortfolioDecisionView } from "../portfolioDecision/portfolioDecisionApi";

interface AlphaHoldingLite {
  ticker: string;
  caseId: string | null;
}

type FitStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; assessment: PortfolioFitAssessmentView | null };
type WatchlistStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; entries: WatchlistEntryView[] };
type HoldingsStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; holdings: AlphaHoldingLite[] };
type ActionStatus = { kind: "idle" } | { kind: "submitting" } | { kind: "error"; message: string };
type StanceStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; stance: StanceView | null };

/**
 * Deliverable 4/12 -- Discovery Candidate Card's full-page home, and the
 * one entity-scoped route Atlas Companion (Deliverable 11) can attach
 * "Discussing: {ticker}" context to. Everything here composes existing
 * endpoints (`/api/portfolio-fit/ticker/:ticker`, `/api/alpha-watchlist`,
 * `/api/alpha-portfolio`) -- no new backend call.
 */
export function CandidateDetailPage() {
  const { ticker: rawTicker } = useParams<{ ticker: string }>();
  const ticker = (rawTicker ?? "").toUpperCase();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [fitStatus, setFitStatus] = useState<FitStatus>({ kind: "loading" });
  const [watchlistStatus, setWatchlistStatus] = useState<WatchlistStatus>({ kind: "loading" });
  const [holdingsStatus, setHoldingsStatus] = useState<HoldingsStatus>({ kind: "loading" });
  const [actionStatus, setActionStatus] = useState<ActionStatus>({ kind: "idle" });
  /** Deliverable 6 -- the same "vs weakest holding" fact Compare's own
   * quick-pick and Discovery's list page already use, fetched once here
   * too so this page's own Compare button can default to it. */
  const [holdingsFit, setHoldingsFit] = useState<PortfolioFitAssessmentView[]>([]);
  /** Deliverable 3 -- the real Daily Brief Agenda item (if any) that
   * currently flags this exact ticker, sourced from the same shared
   * `group === "watchlist"` slice Discovery's list page reads. */
  const [agendaItem, setAgendaItem] = useState<AgendaItemView | null>(null);
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 7). */
  const [stanceStatus, setStanceStatus] = useState<StanceStatus>({ kind: "loading" });

  function loadFit(controller?: AbortController) {
    setFitStatus({ kind: "loading" });
    fetchPortfolioFitForTicker(ticker, controller?.signal)
      .then((assessment) => setFitStatus({ kind: "loaded", assessment }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setFitStatus({ kind: "error" });
      });
  }

  useEffect(() => {
    const controller = new AbortController();
    setStanceStatus({ kind: "loading" });
    fetchStanceForTicker(ticker, controller.signal)
      .then((stance) => setStanceStatus({ kind: "loaded", stance }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStanceStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [ticker]);

  useEffect(() => {
    const controller = new AbortController();
    loadFit(controller);
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker]);

  useEffect(() => {
    const controller = new AbortController();
    fetchWatchlist(controller.signal)
      .then((entries) => setWatchlistStatus({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setWatchlistStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<{ exists: boolean; holdings: AlphaHoldingLite[] }>;
      })
      .then((body) => setHoldingsStatus({ kind: "loaded", holdings: body.exists ? body.holdings : [] }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setHoldingsStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioFitForHoldings(controller.signal)
      .then((assessments) => setHoldingsFit(assessments))
      .catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefAgenda(controller.signal)
      .then((agenda) => setAgendaItem(agenda.items.find((item) => item.ticker === ticker && item.group === "watchlist") ?? null))
      .catch(() => {});
    return () => controller.abort();
  }, [ticker]);

  const isOnWatchlist = watchlistStatus.kind === "loaded" && watchlistStatus.entries.some((e) => e.ticker === ticker);
  const isHolding = holdingsStatus.kind === "loaded" && holdingsStatus.holdings.some((h) => h.ticker === ticker && h.caseId !== null);
  const resolvedCaseId =
    (watchlistStatus.kind === "loaded" ? watchlistStatus.entries.find((e) => e.ticker === ticker)?.caseId : null) ??
    (holdingsStatus.kind === "loaded" ? holdingsStatus.holdings.find((h) => h.ticker === ticker)?.caseId : null) ??
    null;

  /** Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
   * Understanding, Deliverable 8) -- "hur väl ett nytt case redan
   * stöds av befintlig evidens, vilka beroenden som ännu saknas."
   * Never affects `fitStatus`/ranking -- an independent, read-only
   * fetch reusing the exact same component Investment Case already
   * uses. */
  const [evidenceGraph, setEvidenceGraph] = useState<EvidenceGraphView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setEvidenceGraph(null);
      return;
    }
    const controller = new AbortController();
    fetchEvidenceGraph(resolvedCaseId, controller.signal)
      .then((graph) => setEvidenceGraph(graph))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Intelligence Sprint 11 (Decision Readiness & Decision
   * Eligibility, Deliverable 8) -- "detta måste aldrig ändra ranking,
   * det informerar bara investeraren." Independent, read-only fetch;
   * never touches `fitStatus`/candidate ordering. */
  const [decisionReadiness, setDecisionReadiness] = useState<DecisionReadinessView | null>(null);
  const [decisionReadinessChange, setDecisionReadinessChange] = useState<DecisionReadinessChangeView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setDecisionReadiness(null);
      setDecisionReadinessChange(null);
      return;
    }
    const controller = new AbortController();
    fetchDecisionReadiness(resolvedCaseId, controller.signal)
      .then((readiness) => setDecisionReadiness(readiness))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    fetchDecisionReadinessChange(resolvedCaseId, controller.signal)
      .then((change) => setDecisionReadinessChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 1 (Investment Decision Synthesis,
   * Deliverable 8) -- read-only fetch, never touches `fitStatus`/
   * candidate ordering. */
  const [investmentDecision, setInvestmentDecision] = useState<InvestmentDecisionView | null>(null);
  const [investmentDecisionChange, setInvestmentDecisionChange] = useState<DecisionChangeView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setInvestmentDecision(null);
      setInvestmentDecisionChange(null);
      return;
    }
    const controller = new AbortController();
    fetchInvestmentDecision(resolvedCaseId, controller.signal)
      .then((decision) => setInvestmentDecision(decision))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    fetchInvestmentDecisionChange(resolvedCaseId, controller.signal)
      .then((change) => setInvestmentDecisionChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 2 (Recommendation Strength &
   * Conviction, Deliverable 8) -- read-only fetch, never affects
   * Discovery's own ranking. */
  const [recommendationConviction, setRecommendationConviction] = useState<RecommendationConvictionView | null>(null);
  const [recommendationConvictionChange, setRecommendationConvictionChange] = useState<ConvictionChangeView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setRecommendationConviction(null);
      setRecommendationConvictionChange(null);
      return;
    }
    const controller = new AbortController();
    fetchRecommendationConviction(resolvedCaseId, controller.signal)
      .then((conviction) => setRecommendationConviction(conviction))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    fetchRecommendationConvictionChange(resolvedCaseId, controller.signal)
      .then((change) => setRecommendationConvictionChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 3 (Decision Path & Required
   * Progress, Deliverable 8) -- read-only fetch, never affects
   * Discovery's own ranking. */
  const [decisionPath, setDecisionPath] = useState<DecisionPathView | null>(null);
  const [decisionPathChange, setDecisionPathChange] = useState<DecisionPathChangeView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setDecisionPath(null);
      setDecisionPathChange(null);
      return;
    }
    const controller = new AbortController();
    fetchDecisionPath(resolvedCaseId, controller.signal)
      .then((path) => setDecisionPath(path))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    fetchDecisionPathChange(resolvedCaseId, controller.signal)
      .then((change) => setDecisionPathChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 4 (Decision Alternatives &
   * Opportunity Cost, Deliverable 8) -- read-only fetch, never
   * affects Discovery's own ranking. */
  const [opportunityCost, setOpportunityCost] = useState<OpportunityCostView | null>(null);
  const [opportunityCostChange, setOpportunityCostChange] = useState<OpportunityCostChangeView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setOpportunityCost(null);
      setOpportunityCostChange(null);
      return;
    }
    const controller = new AbortController();
    fetchOpportunityCost(resolvedCaseId, controller.signal)
      .then((oc) => setOpportunityCost(oc))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    fetchOpportunityCostChange(resolvedCaseId, controller.signal)
      .then((change) => setOpportunityCostChange(change))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 5 (Decision Memory, Deliverable 8)
   * -- read-only fetch, never affects Discovery's own ranking. */
  const [decisionMemory, setDecisionMemory] = useState<DecisionMemoryView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setDecisionMemory(null);
      return;
    }
    const controller = new AbortController();
    fetchDecisionMemory(resolvedCaseId, controller.signal)
      .then((memory) => setDecisionMemory(memory))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 6 (Decision Explanation &
   * Traceability, Deliverable 8) -- read-only fetch, never affects
   * Discovery's own ranking. Reuses the same `DecisionExplanationSection`
   * component as Investment Case -- its own default (collapsed) state
   * already IS the compact "top supporting finding, top blocker"
   * reading Deliverable 8 asks for; an "unknown explanation" Case
   * (no readiness result yet) already renders honestly via that same
   * component's `noSupporting`/`noBlocking` fallback text. */
  const [decisionExplanation, setDecisionExplanation] = useState<DecisionExplanationView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setDecisionExplanation(null);
      return;
    }
    const controller = new AbortController();
    fetchDecisionExplanation(resolvedCaseId, controller.signal)
      .then((explanation) => setDecisionExplanation(explanation))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 7 (Decision Reliability, Deliverable
   * 9) -- read-only fetch, never affects Discovery's own ranking.
   * Reuses the same `DecisionReliabilitySection` component as
   * Investment Case -- its own default (collapsed) state already IS
   * the compact "reliability level, primary limitation" reading
   * Deliverable 9 asks for. */
  const [decisionReliability, setDecisionReliability] = useState<DecisionReliabilityView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setDecisionReliability(null);
      return;
    }
    const controller = new AbortController();
    fetchDecisionReliability(resolvedCaseId, controller.signal)
      .then((reliability) => setDecisionReliability(reliability))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  /** Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis,
   * Deliverable 9) -- read-only fetch, never affects Discovery's own
   * ranking. Reuses the same `PortfolioDecisionSection` component as
   * Investment Case -- its own default (collapsed) state already IS
   * the compact "category, primary limitation, capital competition"
   * reading Deliverable 9 asks for. */
  const [portfolioDecision, setPortfolioDecision] = useState<PortfolioDecisionView | null>(null);
  useEffect(() => {
    if (!resolvedCaseId) {
      setPortfolioDecision(null);
      return;
    }
    const controller = new AbortController();
    fetchPortfolioDecision(resolvedCaseId, controller.signal)
      .then((decision) => setPortfolioDecision(decision))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, [resolvedCaseId]);

  function handleAddToWatchlist() {
    setActionStatus({ kind: "submitting" });
    addTickerToWatchlist(ticker).then((result) => {
      if (result.kind === "added") {
        setWatchlistStatus((current) =>
          current.kind === "loaded" ? { kind: "loaded", entries: [...current.entries, result.entry] } : current,
        );
        setActionStatus({ kind: "idle" });
        loadFit();
      } else {
        setActionStatus({ kind: "error", message: t("discovery.card.addFailed") });
      }
    });
  }

  function handleRemoveFromWatchlist() {
    setActionStatus({ kind: "submitting" });
    removeTickerFromWatchlist(ticker).then((ok) => {
      if (ok) {
        setWatchlistStatus((current) =>
          current.kind === "loaded" ? { kind: "loaded", entries: current.entries.filter((e) => e.ticker !== ticker) } : current,
        );
        setActionStatus({ kind: "idle" });
      } else {
        setActionStatus({ kind: "error", message: t("discovery.card.removeFailed") });
      }
    });
  }

  function handleOpenCase() {
    if (fitStatus.kind === "loaded" && fitStatus.assessment !== null) {
      navigate(`/investment-case/${fitStatus.assessment.caseId}`, { state: { origin: "discovery", ticker } });
      return;
    }
    const holding = holdingsStatus.kind === "loaded" ? holdingsStatus.holdings.find((h) => h.ticker === ticker) : null;
    if (holding?.caseId) {
      navigate(`/investment-case/${holding.caseId}`, { state: { origin: "discovery", ticker } });
      return;
    }
    const watchlistEntry = watchlistStatus.kind === "loaded" ? watchlistStatus.entries.find((e) => e.ticker === ticker) : null;
    if (watchlistEntry) {
      navigate(`/investment-case/${watchlistEntry.caseId}`, { state: { origin: "discovery", ticker } });
      return;
    }
    // A Portfolio holding with no Case yet -- the exact same
    // create-and-link sequence Discovery's own "Review a Company" flow
    // already used before this sprint (`POST /api/cases` then
    // `.../case-link`), reused verbatim rather than re-derived.
    if (holding) {
      setActionStatus({ kind: "submitting" });
      fetch("/api/cases", { method: "POST" })
        .then((response) => {
          if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
          return response.json() as Promise<{ caseId: string }>;
        })
        .then((created) =>
          fetch(`/api/alpha-portfolio/holdings/${encodeURIComponent(ticker)}/case-link`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidateCaseId: created.caseId }),
          }).then((linkResponse) => {
            if (!linkResponse.ok) throw new Error(`Backend responded with ${linkResponse.status}`);
            return linkResponse.json() as Promise<{ caseId: string }>;
          }),
        )
        .then((linked) => navigate(`/investment-case/${linked.caseId}`, { state: { origin: "discovery", ticker } }))
        .catch(() => setActionStatus({ kind: "error", message: t("discovery.card.openCaseFailed") }));
    }
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <RouterLink to="/discovery" style={{ color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" }}>
          {t("discovery.card.backToDiscovery")}
        </RouterLink>

        <Divider tone="hairline" />

        {fitStatus.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("portfolioFit.section.loading")}
          </Text>
        )}

        {fitStatus.kind !== "loading" && (
          <DiscoveryCandidateCard
            ticker={ticker}
            reasonKey={isOnWatchlist ? "discovery.card.reason.watchlist" : isHolding ? "discovery.card.reason.holding" : "discovery.card.reason.search"}
            agendaHeadline={agendaItem?.headline ?? null}
            assessment={fitStatus.kind === "loaded" ? fitStatus.assessment : null}
            stance={stanceStatus.kind === "loaded" ? stanceStatus.stance : null}
            isOnWatchlist={isOnWatchlist}
            isHolding={isHolding}
            variant="full"
            onOpenCase={handleOpenCase}
            onAddToWatchlist={isHolding ? undefined : handleAddToWatchlist}
            onRemoveFromWatchlist={isOnWatchlist ? handleRemoveFromWatchlist : undefined}
            onCompare={() => {
              const evaluated = holdingsFit.filter((a) => a.overall !== "unavailable" && a.ticker !== ticker);
              const weakest = evaluated.length > 0 ? evaluated[evaluated.length - 1]!.ticker : null;
              const params = new URLSearchParams({ a: ticker });
              if (weakest) params.set("b", weakest);
              navigate(`/discovery/compare?${params.toString()}`);
            }}
          />
        )}

        {actionStatus.kind === "error" && (
          <Text color="tertiary" role="alert">
            {actionStatus.message}
          </Text>
        )}

        {evidenceGraph && <EvidenceGraphSection graph={evidenceGraph} t={t} />}
        {decisionReadiness && (
          <DecisionReadinessSection readiness={decisionReadiness} change={decisionReadinessChange} t={t} />
        )}
        {investmentDecision && (
          <InvestmentDecisionSection decision={investmentDecision} change={investmentDecisionChange} t={t} />
        )}
        {recommendationConviction && (
          <RecommendationConvictionSection
            conviction={recommendationConviction}
            change={recommendationConvictionChange}
            t={t}
          />
        )}
        {decisionPath && <DecisionPathSection path={decisionPath} change={decisionPathChange} t={t} />}
        {opportunityCost && (
          <OpportunityCostSection opportunityCost={opportunityCost} currentTicker={ticker} change={opportunityCostChange} t={t} />
        )}
        {decisionMemory && <DecisionMemorySection memory={decisionMemory} t={t} />}
        {decisionExplanation && <DecisionExplanationSection explanation={decisionExplanation} t={t} />}
        {decisionReliability && <DecisionReliabilitySection reliability={decisionReliability} t={t} />}
        {portfolioDecision && <PortfolioDecisionSection decision={portfolioDecision} t={t} />}
      </Stack>
    </Container>
  );
}
