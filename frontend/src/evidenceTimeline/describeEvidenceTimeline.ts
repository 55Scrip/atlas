import type { AnalysisChangeDirection, Translate } from "../changeIntelligence/describeChange";
import { EVIDENCE_TRANSITION_CATEGORY_KEY, type EvidenceTransitionCategory } from "../status/statusTone";
import type { TranslationKey } from "../i18n";
import type { EvidenceTransitionView, SourceEvidenceEventView } from "./evidenceTimelineApi";

/**
 * Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
 * Understanding, Deliverable 4/10). One plain, investor-language
 * sentence per (category, direction) pair -- the presentation layer
 * owns every sentence, this engine only names the real, already-
 * computed classification. Deliberately avoids "transition"/"event"/
 * "snapshot" vocabulary in the sentences themselves (Deliverable 10's
 * own "avoid timeline jargon, event sourcing terminology" instruction)
 * -- those words are fine as internal/code names, never as investor-
 * facing copy.
 */

const _SENTENCE_KEY: Record<EvidenceTransitionCategory, Record<AnalysisChangeDirection, TranslationKey>> = {
  coverage_changed: {
    positive: "evidenceTimeline.sentence.coverageChanged.positive",
    negative: "evidenceTimeline.sentence.coverageChanged.negative",
    neutral: "evidenceTimeline.sentence.coverageChanged.neutral",
  },
  confidence_changed: {
    positive: "evidenceTimeline.sentence.confidenceChanged.positive",
    negative: "evidenceTimeline.sentence.confidenceChanged.negative",
    neutral: "evidenceTimeline.sentence.confidenceChanged.neutral",
  },
  stance_changed: {
    positive: "evidenceTimeline.sentence.stanceChanged.positive",
    negative: "evidenceTimeline.sentence.stanceChanged.negative",
    neutral: "evidenceTimeline.sentence.stanceChanged.neutral",
  },
  freshness_changed: {
    positive: "evidenceTimeline.sentence.freshnessChanged.positive",
    negative: "evidenceTimeline.sentence.freshnessChanged.negative",
    neutral: "evidenceTimeline.sentence.freshnessChanged.neutral",
  },
  conflict_status_changed: {
    positive: "evidenceTimeline.sentence.conflictStatusChanged.positive",
    negative: "evidenceTimeline.sentence.conflictStatusChanged.negative",
    neutral: "evidenceTimeline.sentence.conflictStatusChanged.neutral",
  },
  evidence_quality_changed: {
    positive: "evidenceTimeline.sentence.evidenceQualityChanged.positive",
    negative: "evidenceTimeline.sentence.evidenceQualityChanged.negative",
    neutral: "evidenceTimeline.sentence.evidenceQualityChanged.neutral",
  },
};

export function transitionSentence(transition: EvidenceTransitionView, t: Translate): string {
  return t(_SENTENCE_KEY[transition.category][transition.direction]);
}

export function transitionCategoryLabel(category: EvidenceTransitionCategory, t: Translate): string {
  return t(EVIDENCE_TRANSITION_CATEGORY_KEY[category]);
}

/**
 * Sprint 6, Deliverable 7 -- materiality governs prominence. Server
 * already computed `isMaterial` per transition
 * (`atlas.alpha.evidence_timeline.engine.is_material_transition`); this
 * is a plain filter over that already-computed flag, never a second
 * materiality judgement made in the frontend.
 */
export function materialTransitions(transitions: EvidenceTransitionView[]): EvidenceTransitionView[] {
  return transitions.filter((transition) => transition.isMaterial);
}

/**
 * Sprint 6, Deliverable 8/12 -- "compact by default". A single capture
 * can genuinely surface many new `(factKind, period)` combinations at
 * once (e.g. several years of a fact kind becoming known together, all
 * real, none fabricated) -- live verification against real portfolio
 * data found this can run to dozens of events. Rather than let a
 * factual-but-honest list overwhelm a compact summary, only the most
 * recent `limit` are shown prominently; the rest are never dropped,
 * only deferred to the full, unfiltered history one click away.
 */
const _MAX_PROMINENT_SOURCE_EVIDENCE_EVENTS = 3;

export function prominentSourceEvidence(
  events: SourceEvidenceEventView[],
  limit = _MAX_PROMINENT_SOURCE_EVIDENCE_EVENTS,
): { shown: SourceEvidenceEventView[]; overflowCount: number } {
  return { shown: events.slice(0, limit), overflowCount: Math.max(0, events.length - limit) };
}

/**
 * `SourceEvidenceEvent.factKind` labels (Sprint 6, Deliverable 2/15) --
 * every `BusinessFactKind`/`ValuationFactKind` member known at the time
 * this map was written (`atlas.analysis_engine.business_facts.contracts
 * .BusinessFactKind`, `atlas.analysis_engine.valuation.facts
 * .ValuationFactKind`). `factKind` is a plain wire string, not a closed
 * frontend enum, so an unmapped value (a future fact kind added on the
 * backend before this map is updated) falls back to a humanized form of
 * the raw string rather than crashing or showing a raw key.
 */
const _FACT_KIND_LABEL_KEY: Record<string, TranslationKey> = {
  revenue: "evidenceTimeline.sourceEvidence.factKind.revenue",
  free_cash_flow: "evidenceTimeline.sourceEvidence.factKind.freeCashFlow",
  capital_expenditure: "evidenceTimeline.sourceEvidence.factKind.capitalExpenditure",
  share_buybacks: "evidenceTimeline.sourceEvidence.factKind.shareBuybacks",
  share_issuance: "evidenceTimeline.sourceEvidence.factKind.shareIssuance",
  dividends: "evidenceTimeline.sourceEvidence.factKind.dividends",
  debt_issuance: "evidenceTimeline.sourceEvidence.factKind.debtIssuance",
  debt_repayment: "evidenceTimeline.sourceEvidence.factKind.debtRepayment",
  operating_income: "evidenceTimeline.sourceEvidence.factKind.operatingIncome",
  net_income: "evidenceTimeline.sourceEvidence.factKind.netIncome",
  eps: "evidenceTimeline.sourceEvidence.factKind.eps",
  cash: "evidenceTimeline.sourceEvidence.factKind.cash",
  total_debt: "evidenceTimeline.sourceEvidence.factKind.totalDebt",
  shares_outstanding: "evidenceTimeline.sourceEvidence.factKind.sharesOutstanding",
  share_price: "evidenceTimeline.sourceEvidence.factKind.sharePrice",
};

function humanizeFactKind(factKind: string): string {
  return factKind.replace(/_/g, " ");
}

export function sourceEvidenceFactKindLabel(factKind: string, t: Translate): string {
  const key = _FACT_KIND_LABEL_KEY[factKind];
  return key ? t(key) : humanizeFactKind(factKind);
}

/**
 * **Source Evidence History** sentence (Deliverable 2/15) -- factual,
 * never interpreted: Atlas received a new `(factKind, period)`
 * combination it did not have before. Deliberately distinct wording
 * from `transitionSentence` above (**Atlas Analysis History**) -- this
 * describes new raw evidence arriving, not a conclusion changing.
 */
export function sourceEvidenceSentence(event: SourceEvidenceEventView, t: Translate): string {
  return t("evidenceTimeline.sourceEvidence.sentence", { kind: sourceEvidenceFactKindLabel(event.factKind, t), period: event.period });
}
