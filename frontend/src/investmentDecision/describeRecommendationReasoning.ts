import type { TranslationKey } from "../i18n";
import type {
  CanonicalEngine,
  ChangeTriggerKind,
  ContractedVolumeContextView,
  ForwardGuidanceContextView,
  ForwardGuidanceSubject,
  ForwardHorizonKind,
  DebtBurdenObservationView,
  ForwardReasoningContextView,
  GuidanceRevisionKind,
  InvestmentReasonKind,
  InvestmentReasonView,
  KeyUnknownView,
  RiskDriverBasisView,
  RiskLevel,
  SignalContributionView,
  UnestablishedEconomics,
} from "./reasoningContract";

/**
 * Closed backend vocabularies -> investor language. The same role
 * `describeInvestmentDecision.ts` plays for actions and qualifiers,
 * and the same rule: this module only looks tokens up. It derives
 * nothing, ranks nothing, and merges nothing -- ordering is the
 * backend's own `_ENGINE_PRECEDENCE`, and it arrives already applied.
 */

export const REASON_KIND_KEY: Record<InvestmentReasonKind, TranslationKey> = {
  growth_strong: "investmentReasoning.reason.growthStrong",
  growth_moderate: "investmentReasoning.reason.growthModerate",
  growth_weak: "investmentReasoning.reason.growthWeak",
  capital_allocation_strong: "investmentReasoning.reason.capitalAllocationStrong",
  capital_allocation_moderate: "investmentReasoning.reason.capitalAllocationModerate",
  capital_allocation_weak: "investmentReasoning.reason.capitalAllocationWeak",
  valuation_undervalued: "investmentReasoning.reason.valuationUndervalued",
  valuation_fairly_valued: "investmentReasoning.reason.valuationFairlyValued",
  valuation_expensive: "investmentReasoning.reason.valuationExpensive",
  valuation_supported: "investmentReasoning.reason.valuationSupported",
  valuation_not_supported: "investmentReasoning.reason.valuationNotSupported",
  financial_risk_elevated: "investmentReasoning.reason.financialRiskElevated",
  financial_risk_not_elevated: "investmentReasoning.reason.financialRiskNotElevated",
};

export const ENGINE_KEY: Record<CanonicalEngine, TranslationKey> = {
  growth: "investmentReasoning.engine.growth",
  capital_allocation: "investmentReasoning.engine.capitalAllocation",
  valuation: "investmentReasoning.engine.valuation",
  valuation_support: "investmentReasoning.engine.valuationSupport",
  financial_risk: "investmentReasoning.engine.financialRisk",
  business_quality: "investmentReasoning.engine.businessQuality",
  industry_context: "investmentReasoning.engine.industryContext",
  expected_return: "investmentReasoning.engine.expectedReturn",
};

export const CHANGE_TRIGGER_KEY: Record<ChangeTriggerKind, TranslationKey> = {
  reduced_risk: "investmentReasoning.trigger.reducedRisk",
  more_attractive_valuation: "investmentReasoning.trigger.moreAttractiveValuation",
  improved_growth_evidence: "investmentReasoning.trigger.improvedGrowthEvidence",
  improved_capital_allocation_evidence: "investmentReasoning.trigger.improvedCapitalAllocationEvidence",
  lower_valuation: "investmentReasoning.trigger.lowerValuation",
  financial_risk_becomes_elevated: "investmentReasoning.trigger.financialRiskBecomesElevated",
  valuation_becomes_expensive: "investmentReasoning.trigger.valuationBecomesExpensive",
  valuation_support_lost: "investmentReasoning.trigger.valuationSupportLost",
  growth_deteriorates: "investmentReasoning.trigger.growthDeteriorates",
  capital_allocation_deteriorates: "investmentReasoning.trigger.capitalAllocationDeteriorates",
  no_credible_trigger_identified: "investmentReasoning.trigger.noCredibleTrigger",
};

export function reasonKindLabel(
  reason: InvestmentReasonView,
  t: (key: TranslationKey) => string,
): string {
  return t(REASON_KIND_KEY[reason.kind]);
}

/**
 * A key unknown is a *kind* plus the engine it belongs to -- rendered
 * together, because "input missing" means something quite different
 * for Valuation Support than for Growth. `not_connected_to_direction`
 * is deliberately not surfaced: it describes Atlas's own engine
 * wiring, not an unknown about the company.
 */
export function keyUnknownLabel(
  unknown: KeyUnknownView,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string | null {
  if (unknown.kind === "not_connected_to_direction") return null;
  const engine = t(ENGINE_KEY[unknown.engine]);
  return unknown.kind === "analysis_input_missing"
    ? t("investmentReasoning.unknown.inputMissing", { engine })
    : t("investmentReasoning.unknown.unresolved", { engine });
}

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

const GUIDANCE_SUBJECT_KEY: Record<ForwardGuidanceSubject, TranslationKey> = {
  revenue: "investmentReasoning.forward.subject.revenue",
  adjusted_ebitda: "investmentReasoning.forward.subject.adjustedEbitda",
  free_cash_flow: "investmentReasoning.forward.subject.freeCashFlow",
  capital_expenditure: "investmentReasoning.forward.subject.capitalExpenditure",
};

const GUIDANCE_REVISION_KEY: Record<GuidanceRevisionKind, TranslationKey> = {
  raised: "investmentReasoning.forward.guidance.raised",
  lowered: "investmentReasoning.forward.guidance.lowered",
  reaffirmed: "investmentReasoning.forward.guidance.reaffirmed",
};

const HORIZON_KEY: Record<ForwardHorizonKind, TranslationKey> = {
  fiscal_year: "investmentReasoning.forward.horizon.fiscalYear",
  calendar_year: "investmentReasoning.forward.horizon.calendarYear",
  unspecified_year: "investmentReasoning.forward.horizon.year",
};

const UNESTABLISHED_KEY: Record<UnestablishedEconomics, TranslationKey> = {
  price: "investmentReasoning.forward.unknown.price",
  revenue_contribution: "investmentReasoning.forward.unknown.revenueContribution",
  earnings_contribution: "investmentReasoning.forward.unknown.earningsContribution",
  cash_flow_contribution: "investmentReasoning.forward.unknown.cashFlowContribution",
};

const ALL_ECONOMICS: UnestablishedEconomics[] = [
  "price",
  "revenue_contribution",
  "earnings_contribution",
  "cash_flow_contribution",
];

/** One verified guidance revision, in its own figures. A management-
 * defined measure is always qualified, and "reaffirmed" reads as
 * unchanged -- nothing here says better or worse. */
export function guidanceContextLabel(item: ForwardGuidanceContextView, t: Translate): string {
  const measure =
    t(GUIDANCE_SUBJECT_KEY[item.subject]) +
    (item.measureDefinedByManagement ? t("investmentReasoning.forward.subject.managementDefined") : "");
  const line = t(GUIDANCE_REVISION_KEY[item.revision], {
    horizon: t(HORIZON_KEY[item.horizonKind], { year: item.horizonPeriod }),
    measure,
    value: item.valueText,
    prior: item.priorValueText ?? t("investmentReasoning.forward.guidance.priorUnknown"),
  });
  return item.revisionCount > 1
    ? `${line} (${t("investmentReasoning.forward.guidance.revisionCount", { count: item.revisionCount })})`
    : line;
}

function periodSpan(items: ContractedVolumeContextView[]): string {
  const periods = items.map((i) => i.sourcePeriod).filter((p): p is string => p !== null).sort();
  const first = periods[0];
  const last = periods[periods.length - 1];
  if (first === undefined || last === undefined) return "";
  return first === last ? first : `${first}–${last}`;
}

/**
 * Contracted customer volume, observationally. One observation is shown
 * with its own stated quantities; several are summarised by the
 * customer names they state, how many source observations there are,
 * and the plain warning that one agreement can appear in more than one
 * of them. Nothing is counted as contracts and nothing is summed.
 */
export function contractedVolumeLabel(context: ForwardReasoningContextView, t: Translate): string | null {
  const items = context.contractedVolume;
  if (items.length === 0) return null;
  const item = items.length === 1 ? items[0] : undefined;
  if (item) {
    let details = item.quantityTexts.join(t("investmentReasoning.forward.volume.and"));
    if (item.termYears !== null) details += t("investmentReasoning.forward.volume.term", { years: item.termYears });
    if (item.deliveryStartYears.length > 0)
      details += t("investmentReasoning.forward.volume.deliveryFrom", { years: item.deliveryStartYears.join(", ") });
    return t("investmentReasoning.forward.volume.single", {
      customer: item.counterpartyText ?? t("investmentReasoning.forward.volume.unnamedCustomer"),
      details,
    });
  }
  const names = [...context.counterpartyTexts];
  if (context.unnamedObservationCount > 0) names.push(t("investmentReasoning.forward.volume.unnamedCustomer"));
  const terms = [...new Set(items.map((i) => i.termYears).filter((y): y is number => y !== null))].sort(
    (a, b) => a - b,
  );
  const line = t("investmentReasoning.forward.volume.multiple", {
    names: names.join(", "),
    count: items.length,
    periods: periodSpan(items),
  });
  return terms.length > 0
    ? `${line}${t("investmentReasoning.forward.volume.statedTerms", { terms: terms.join(", ") })}`
    : line;
}

/** Every forward-context line, guidance first, then contracted volume --
 * the backend's own order, never sorted by how favourable it sounds. */
export function forwardContextLabels(context: ForwardReasoningContextView | null | undefined, t: Translate): string[] {
  if (!context) return [];
  const volume = contractedVolumeLabel(context, t);
  return [...context.guidance.map((g) => guidanceContextLabel(g, t)), ...(volume ? [volume] : [])];
}

/** The economics contracted volume does not establish. All four at once
 * read as one sentence; any other set, one per aspect. */
export function forwardUnknownLabels(context: ForwardReasoningContextView | null | undefined, t: Translate): string[] {
  const aspects = context?.unestablishedEconomics ?? [];
  if (aspects.length === 0) return [];
  if (ALL_ECONOMICS.every((a) => aspects.includes(a))) return [t("investmentReasoning.forward.unknown.allEconomics")];
  return aspects.map((a) => t(UNESTABLISHED_KEY[a]));
}

const RISK_LEVEL_KEY: Record<RiskLevel, TranslationKey> = {
  not_evaluated: "investmentReasoning.riskBasis.level.notEvaluated",
  insufficient_input: "investmentReasoning.riskBasis.level.insufficientInput",
  not_applicable: "investmentReasoning.riskBasis.level.notApplicable",
  low: "investmentReasoning.riskBasis.level.low",
  moderate: "investmentReasoning.riskBasis.level.moderate",
  high: "investmentReasoning.riskBasis.level.high",
};

/** A reported amount as the fact states it, compacted for reading
 * ("14,4 md US$" / "$14.4B"). An ISO currency code renders as currency;
 * any other unit is kept beside the number, never dropped or guessed. */
export function formatReportedAmount(value: number, unit: string, locale: string): string {
  const compact = { notation: "compact", minimumFractionDigits: 1, maximumFractionDigits: 1 } as const;
  if (/^[A-Z]{3}$/.test(unit)) {
    try {
      return new Intl.NumberFormat(locale, { ...compact, style: "currency", currency: unit }).format(value);
    } catch {
      // Not a currency Intl knows: fall through to the plain form.
    }
  }
  const number = new Intl.NumberFormat(locale, compact).format(value);
  return unit === "unspecified" ? number : `${number} ${unit}`;
}

/** "4,2×" -- one decimal, the locale's own separator. */
export function formatMultiple(ratio: number, locale: string): string {
  return `${new Intl.NumberFormat(locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(ratio)}×`;
}

/** The period-end year, unless two observations share one -- then the
 * full period-end date, so no label is ambiguous. */
function periodLabel(observation: DebtBurdenObservationView, all: DebtBurdenObservationView[]): string {
  const year = observation.period.slice(0, 4);
  return all.filter((o) => o.period.slice(0, 4) === year).length > 1 ? observation.period : year;
}

/** Level first: what the latest aligned figure says. */
function financialLevelSentence(basis: RiskDriverBasisView, t: Translate, locale: string): string | null {
  const financial = basis.financialRisk;
  const latest = financial.latest;
  if (!latest) return null;
  const period = periodLabel(latest, financial.history);
  switch (financial.condition) {
    case "debt_burden_high":
      return latest.ratio === null
        ? null
        : t("investmentReasoning.riskBasis.debtBurdenHigh", { multiple: formatMultiple(latest.ratio, locale), period });
    case "operating_cash_flow_negative":
      return t("investmentReasoning.riskBasis.operatingCashFlowNegative", {
        period,
        value: formatReportedAmount(latest.operatingCashFlow, latest.unit, locale),
      });
    case "operating_cash_flow_zero":
      return t("investmentReasoning.riskBasis.operatingCashFlowZero", { period });
    default:
      return null;
  }
}

/** Trend second, and only as context: how the same measure stood at the
 * oldest observation Atlas holds. Never changes the level. */
function burdenTrendSentence(basis: RiskDriverBasisView, t: Translate, locale: string): string | null {
  const history = basis.financialRisk.history;
  const first = history[0];
  const latest = basis.financialRisk.latest;
  if (!first || !latest || first === latest || first.ratio === null || latest.ratio === null) return null;
  const key =
    latest.ratio > first.ratio
      ? "investmentReasoning.riskBasis.trendUp"
      : latest.ratio < first.ratio
        ? "investmentReasoning.riskBasis.trendDown"
        : "investmentReasoning.riskBasis.trendFlat";
  return t(key, { multiple: formatMultiple(first.ratio, locale), period: periodLabel(first, history) });
}

/**
 * Why "elevated financial risk" is shown -- or `null` when it is not.
 *
 * When Financial Risk itself is high: the measured level first (debt
 * relative to cash from operations, with its year), the trend second as
 * context, then one sentence bounding what was measured -- reported
 * amounts, not ratings, interest costs, maturities or liquidity. It
 * explains the financial driver only; valuation has its own reason and
 * its own line (`valuationBasisLabel`).
 *
 * Legacy rows only: before the financial and valuation drivers were split,
 * the financial driver could be raised by valuation alone. For such a row
 * the line says so, with the level Financial Risk actually had -- a stored
 * row is never re-read as if the split had produced it. A payload of any
 * other basis version is not read.
 */
export function riskBasisLabel(
  basis: RiskDriverBasisView | null | undefined,
  t: Translate,
  locale: string,
): string | null {
  if (!basis || basis.version !== 2 || basis.elevatedCategories.length === 0) return null;
  const financial = basis.financialRisk;
  if (!basis.elevatedCategories.includes("financial_risk")) {
    return t("investmentReasoning.riskBasis.valuationOnly", { level: t(RISK_LEVEL_KEY[financial.level]) });
  }
  const level = financialLevelSentence(basis, t, locale);
  if (level === null) return null;
  const sentences = [level];
  const trend = burdenTrendSentence(basis, t, locale);
  if (trend) sentences.push(trend);
  sentences.push(t("investmentReasoning.riskBasis.scope"));
  return sentences.join(" ");
}

/**
 * The one quiet line for a Financial Risk that does not apply: Atlas's
 * corporate debt measure is not used for banks, dealers and insurers.
 * Never a warning and never a reassurance; `null` in every other state.
 */
export function financialRiskNotApplicableLabel(
  basis: RiskDriverBasisView | null | undefined,
  t: Translate,
): string | null {
  if (!basis || basis.version !== 2 || basis.financialRisk.level !== "not_applicable") return null;
  // Raised by valuation alone, the against-row's own basis line already says it.
  if (basis.elevatedCategories.length > 0) return null;
  return t("investmentReasoning.riskBasis.notApplicable");
}

function formatYield(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value);
}

/**
 * Why "expensive" is shown: the valuation evaluator's own figures, as the
 * signal summary projects them -- today's FCF yield against the company's
 * own earlier fiscal years. Nothing is recomputed: "lower than every
 * earlier year" is read off the projected percentile, and the count always
 * travels with it. A comparison with the company's own past only -- never
 * peers, intrinsic value or expected return. `null` when the figures are
 * absent.
 *
 * A row carrying `evidenceEligibility` counts fiscal years and says so,
 * with the one methodological limit that matters for a comparison with
 * the past: earlier market values use today's share count. A row stored
 * before that counted market observations and keeps its original wording.
 */
export function valuationBasisLabel(
  signalSummary: SignalContributionView[] | undefined,
  t: Translate,
  locale: string,
): string | null {
  const valuation = (signalSummary ?? []).find((c) => c.engine === "valuation");
  const current = valuation?.currentYield;
  const median = valuation?.historicalMedianYield;
  const count = valuation?.historicalObservationCount;
  const percentile = valuation?.historicalPercentile;
  if (current == null || median == null || count == null || percentile == null) return null;
  const params = { current: formatYield(current, locale), median: formatYield(median, locale), count };
  const byFiscalYear = valuation?.evidenceEligibility != null;
  const body = byFiscalYear
    ? percentile === 0
      ? t("investmentReasoning.valuationBasis.belowAllYears", params)
      : current < median
        ? t("investmentReasoning.valuationBasis.belowMedianYears", params)
        : null
    : percentile === 0
      ? t(count === 1 ? "investmentReasoning.valuationBasis.belowOnly" : "investmentReasoning.valuationBasis.belowAll", params)
      : current < median
        ? t("investmentReasoning.valuationBasis.belowMedian", params)
        : null;
  if (body === null) return null;
  const line = `${t(REASON_KIND_KEY.valuation_expensive)}: ${body}`;
  return byFiscalYear ? `${line} ${t("investmentReasoning.valuationBasis.shareCountProxy")}` : line;
}

/**
 * The one quiet line for a valuation that may not decide: a current FCF
 * yield Atlas can see, against too few earlier fiscal years (or none) to
 * let it move the recommendation -- or a method that does not apply to
 * the business at all. Stated as history depth, never as "fairly valued".
 * `null` for a decision-eligible valuation (no clutter where history is
 * deep), for a legacy row, and when there is no current yield to speak of.
 */
export function valuationEvidenceLabel(
  signalSummary: SignalContributionView[] | undefined,
  t: Translate,
  locale: string,
): string | null {
  const valuation = (signalSummary ?? []).find((c) => c.engine === "valuation");
  const eligibility = valuation?.evidenceEligibility;
  if (eligibility === "not_applicable") return t("investmentReasoning.valuationEvidence.notApplicable");
  const current = valuation?.currentYield;
  if ((eligibility !== "limited" && eligibility !== "insufficient") || current == null) return null;
  const count = valuation?.historicalObservationCount ?? 0;
  const params = { current: formatYield(current, locale), count };
  if (count === 0) return t("investmentReasoning.valuationEvidence.none", params);
  return t(count === 1 ? "investmentReasoning.valuationEvidence.limitedOne" : "investmentReasoning.valuationEvidence.limited", params);
}
