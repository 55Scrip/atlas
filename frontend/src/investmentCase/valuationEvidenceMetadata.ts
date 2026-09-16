/**
 * (Valuation Evidence Communication) The backend's descriptive valuation
 * evidence, as this frontend reads it: how deep and how wide the fiscal
 * history behind the FCF-yield comparison is, how near today's yield sits
 * to classifying differently, how today's free cash flow and capital
 * intensity compare with the prior years', and which share basis each
 * epoch was priced on.
 *
 * Descriptive, never decisional -- exactly as on the backend
 * (`atlas/alpha/investment_case/valuation_evidence_metadata.py`). Nothing
 * here changes a status, a recommendation, a risk level, a fit or a
 * conviction; it only explains the one the engine already reached. The
 * caveats below are therefore *phrased* as context, never as a verdict,
 * and each one is surfaced only when the metadata itself makes it true --
 * a Case with deep history, an ordinary cash-flow year, room to the
 * boundary and an exact share basis shows none of them at all.
 */
import { VALUATION_STATUS_KEY } from "../changeIntelligence/describeChange";
import type { AnalysisValuationStatus } from "../changeIntelligence/describeChange";
import type { TranslationKey } from "../i18n";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

export interface ValuationHistoryEvidenceView {
  validPriorCount: number;
  minimumPriorCount: number;
  atMinimumDepth: boolean;
  spanYears: number | null;
  firstPriorFiscalPeriod: string | null;
  latestPriorFiscalPeriod: string | null;
  missingFiscalYears: number[];
  yieldMinimum: number | null;
  yieldMedian: number | null;
  yieldMaximum: number | null;
  yieldDispersion: number | null;
  typicalYearOverYearMove: number | null;
}

export interface ValuationBoundaryEvidenceView {
  currentYield: number | null;
  nearestClassification: string | null;
  boundaryYield: number | null;
  distance: number | null;
  distancePercent: number | null;
  closerThanTypicalMove: boolean | null;
}

export interface CurrentCashFlowEvidenceView {
  currentFreeCashFlow: number | null;
  priorYearFreeCashFlow: number | null;
  recentMedianFreeCashFlow: number | null;
  historicalMedianFreeCashFlow: number | null;
  recentYearsCompared: number;
  versusPriorYear: number | null;
  versusRecentMedian: number | null;
  versusHistoricalMedian: number | null;
  recentRange: number[] | null;
  positionVersusRecent: string | null;
}

export interface CapitalIntensityEvidenceView {
  currentCapitalExpenditure: number | null;
  currentRevenue: number | null;
  currentIntensity: number | null;
  priorIntensityMinimum: number | null;
  priorIntensityMedian: number | null;
  priorIntensityMaximum: number | null;
  priorYearsCompared: number;
  versusPriorMedian: number | null;
  positionVersusPriorRange: string | null;
  currentOperatingCashFlow: number | null;
  operatingCashFlowVersusPriorYear: number | null;
  capitalExpenditureVersusPriorYear: number | null;
}

export interface DenominatorEvidenceView {
  currentTreatment: string | null;
  priorTreatments: string[];
  allExact: boolean;
}

export interface EdgeObservationView {
  fiscalPeriod: string;
  fiscalYear: number;
  fcfYield: number;
  denominatorQuality: string | null;
  ageYears: number;
  uniquelyOwned: boolean;
}

export interface RangeEdgeEvidenceView {
  lowEdge: EdgeObservationView | null;
  highEdge: EdgeObservationView | null;
  secondLowest: EdgeObservationView | null;
  secondHighest: EdgeObservationView | null;
  distanceToLowEdge: number | null;
  distanceToHighEdge: number | null;
  distanceToSecondLowest: number | null;
  distanceToSecondHighest: number | null;
  priorsAtOrBelowCurrent: number;
  priorsAtOrAboveCurrent: number;
  singleLowEdgeDependency: boolean;
  singleHighEdgeDependency: boolean;
  lowEdgeGap: number | null;
  highEdgeGap: number | null;
  medianHistoryGap: number | null;
}

export interface ValuationEvidenceMetadataView {
  history: ValuationHistoryEvidenceView;
  boundary: ValuationBoundaryEvidenceView;
  currentCashFlow: CurrentCashFlowEvidenceView;
  capitalIntensity: CapitalIntensityEvidenceView;
  denominator: DenominatorEvidenceView;
  rangeEdge: RangeEdgeEvidenceView | null;
}

const BOUNDED_TREATMENT = "issuer_bounded";

/**
 * How many caveats the compact valuation card shows. `valuationEvidenceCaveats`
 * returns everything the evidence supports -- for a thin, inexact, near-boundary
 * Case that is genuinely five sentences -- and five stacked lines would turn a
 * 30-second status card into a paragraph. The card takes the first few, in the
 * order below (how much each should move a reader's confidence in the
 * classification: the depth of the comparison, then its numerator, then how
 * near the class is to flipping, then its denominator, then the context behind
 * an unusual numerator); the rest stay in the Investment Case's valuation
 * disclosure, which lists them all. Nothing is dropped, only deferred.
 */
export const MAX_CARD_CAVEATS = 3;

function percent(value: number, locale: string, digits = 1): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function ratio(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 }).format(value);
}

function classificationLabel(classification: string | null, t: Translate): string | null {
  if (classification === null) return null;
  const key = VALUATION_STATUS_KEY[classification as AnalysisValuationStatus];
  return key === undefined ? null : t(key);
}

/**
 * Which share basis the earlier market values rest on, named from the
 * treatments the engine actually recorded rather than asserted. Exact
 * when every epoch priced every class off its own listing; bounded when
 * any epoch's contribution is an evidence-derived interval (the stronger
 * caveat, so it wins); equivalent otherwise. `null` when no epoch carries
 * a treatment at all -- silence beats an unfounded claim.
 */
export function shareBasisKey(denominator: DenominatorEvidenceView): TranslationKey | null {
  const treatments = [
    ...(denominator.currentTreatment === null ? [] : [denominator.currentTreatment]),
    ...denominator.priorTreatments,
  ];
  if (treatments.length === 0) return null;
  if (denominator.allExact) return "investmentCase.analysis.valuation.shareCountExact";
  if (treatments.includes(BOUNDED_TREATMENT)) return "investmentCase.analysis.valuation.shareCountBounded";
  return "investmentCase.analysis.valuation.shareCountEquivalent";
}

/**
 * The short, only-when-relevant lines shown beside the valuation card.
 * Each is a fact about the evidence -- minimum depth, a cash-flow year
 * outside its own recent range, a boundary nearer than this history's own
 * typical move, an inexact share basis, capital intensity above every
 * compared year. None of them is a threshold invented here: depth reuses
 * the engine's own `minimumPriorCount`, position reuses the engine's own
 * range comparisons, and nearness reuses the history's own median
 * year-over-year move. An empty array is the normal case.
 */
export function valuationEvidenceCaveats(
  metadata: ValuationEvidenceMetadataView | null | undefined,
  t: Translate,
): string[] {
  if (!metadata) return [];
  const caveats: string[] = [];
  const { history, boundary, currentCashFlow, capitalIntensity, denominator, rangeEdge } = metadata;

  /* (Range Edge Disclosure) Leads, because it is the fact that most changes
     how the conclusion should be read: the Case is inside its historical
     range, but only the single year owning that range's end puts it there.
     It never contradicts the classification and never calls the edge year an
     outlier -- that year is valid evidence, and is named, not discounted. */
  if (rangeEdge?.singleLowEdgeDependency && rangeEdge.lowEdge !== null) {
    caveats.push(
      t("investmentCase.reasoning.valuation.caveat.singleLowEdge", { year: rangeEdge.lowEdge.fiscalYear }),
    );
  }
  if (rangeEdge?.singleHighEdgeDependency && rangeEdge.highEdge !== null) {
    caveats.push(
      t("investmentCase.reasoning.valuation.caveat.singleHighEdge", { year: rangeEdge.highEdge.fiscalYear }),
    );
  }
  if (history.atMinimumDepth) {
    caveats.push(t("investmentCase.reasoning.valuation.caveat.minimumHistory", { count: history.validPriorCount }));
  }
  if (currentCashFlow.positionVersusRecent === "below_range") {
    caveats.push(
      t("investmentCase.reasoning.valuation.caveat.cashFlowBelowRecent", { count: currentCashFlow.recentYearsCompared }),
    );
  }
  if (currentCashFlow.positionVersusRecent === "above_range") {
    caveats.push(
      t("investmentCase.reasoning.valuation.caveat.cashFlowAboveRecent", { count: currentCashFlow.recentYearsCompared }),
    );
  }
  const nearest = classificationLabel(boundary.nearestClassification, t);
  if (boundary.closerThanTypicalMove === true && nearest !== null) {
    caveats.push(t("investmentCase.reasoning.valuation.caveat.nearBoundary", { classification: nearest }));
  }
  if (shareBasisKey(denominator) !== null && !denominator.allExact) {
    caveats.push(t("investmentCase.reasoning.valuation.caveat.shareBasisNotExact"));
  }
  if (capitalIntensity.positionVersusPriorRange === "above_range") {
    caveats.push(t("investmentCase.reasoning.valuation.caveat.capitalIntensityAbove"));
  }
  return caveats;
}

/**
 * The same evidence at full detail, for the Investment Case's existing
 * valuation disclosure: the prior-year yield range, the distance to a
 * different classification, this period's cash flow against its own
 * history, and capital intensity against the compared years. Every line
 * is omitted when the figures behind it are absent -- a company whose
 * statements carry no capital expenditure simply shows no capital line,
 * never a fabricated one.
 */
export function valuationEvidenceDetails(
  metadata: ValuationEvidenceMetadataView | null | undefined,
  t: Translate,
  locale: string,
): string[] {
  if (!metadata) return [];
  const lines: string[] = [];
  const { history, boundary, currentCashFlow, capitalIntensity, rangeEdge } = metadata;

  /* Who owns each end of the observed range, and how many years agree with
     today's position inside it -- the figures behind the qualifier above. */
  if (rangeEdge?.lowEdge && rangeEdge.highEdge && rangeEdge.secondLowest) {
    lines.push(
      t("investmentCase.analysis.valuation.rangeEdges", {
        lowYear: rangeEdge.lowEdge.fiscalYear,
        low: percent(rangeEdge.lowEdge.fcfYield, locale, 2),
        highYear: rangeEdge.highEdge.fiscalYear,
        high: percent(rangeEdge.highEdge.fcfYield, locale, 2),
        secondLowYear: rangeEdge.secondLowest.fiscalYear,
        secondLow: percent(rangeEdge.secondLowest.fcfYield, locale, 2),
      }),
    );
  }
  if (rangeEdge && boundary.currentYield !== null) {
    lines.push(
      t("investmentCase.analysis.valuation.corroboration", {
        below: rangeEdge.priorsAtOrBelowCurrent,
        count: history.validPriorCount,
        current: percent(boundary.currentYield, locale, 2),
      }),
    );
  }

  if (history.yieldMinimum !== null && history.yieldMaximum !== null && history.yieldMedian !== null) {
    lines.push(
      t("investmentCase.analysis.valuation.dispersion", {
        low: percent(history.yieldMinimum, locale),
        high: percent(history.yieldMaximum, locale),
        median: percent(history.yieldMedian, locale),
      }),
    );
  }
  const nearest = classificationLabel(boundary.nearestClassification, t);
  if (boundary.distancePercent !== null && nearest !== null) {
    lines.push(
      t("investmentCase.analysis.valuation.boundaryDistance", {
        percent: ratio(boundary.distancePercent, locale),
        classification: nearest,
      }),
    );
  }
  if (currentCashFlow.versusPriorYear !== null && currentCashFlow.versusRecentMedian !== null) {
    lines.push(
      t("investmentCase.analysis.valuation.cashFlowVsHistory", {
        versusPrior: ratio(currentCashFlow.versusPriorYear, locale),
        versusRecent: ratio(currentCashFlow.versusRecentMedian, locale),
        count: currentCashFlow.recentYearsCompared,
      }),
    );
  }
  if (
    capitalIntensity.currentIntensity !== null &&
    capitalIntensity.priorIntensityMedian !== null &&
    capitalIntensity.priorIntensityMinimum !== null &&
    capitalIntensity.priorIntensityMaximum !== null
  ) {
    lines.push(
      t("investmentCase.analysis.valuation.capitalIntensity", {
        current: percent(capitalIntensity.currentIntensity, locale),
        median: percent(capitalIntensity.priorIntensityMedian, locale),
        count: capitalIntensity.priorYearsCompared,
        low: percent(capitalIntensity.priorIntensityMinimum, locale),
        high: percent(capitalIntensity.priorIntensityMaximum, locale),
      }),
    );
  }
  return lines;
}
