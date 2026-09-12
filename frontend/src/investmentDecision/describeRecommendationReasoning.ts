import type { TranslationKey } from "../i18n";
import type {
  CanonicalEngine,
  ChangeTriggerKind,
  ContractedVolumeContextView,
  ForwardGuidanceContextView,
  ForwardGuidanceSubject,
  ForwardHorizonKind,
  FinancialRiskObservationView,
  FinancialRiskSignalBasisView,
  ForwardReasoningContextView,
  GuidanceRevisionKind,
  InvestmentReasonKind,
  InvestmentReasonView,
  KeyUnknownView,
  RiskDriverBasisView,
  RiskLevel,
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

/** Period labels: the period-end year where that is unambiguous within
 * the series, otherwise the full period-end date. */
function periodLabels(observations: FinancialRiskObservationView[]): string[] {
  const years = observations.map((o) => o.period.slice(0, 4));
  const unique = new Set(years).size === years.length;
  return observations.map((o, i) => (unique ? (years[i] ?? o.period) : o.period));
}

/** One firing signal, in its own figures. Only `high` conditions can be
 * part of an elevated basis; anything else returns `null` and is never
 * shown as a cause. */
function firingSignalLabel(signal: FinancialRiskSignalBasisView, t: Translate, locale: string): string | null {
  const labels = periodLabels(signal.observations);
  const figures = signal.observations.map(
    (o, i) => `${labels[i] ?? o.period}: ${formatReportedAmount(o.value, o.unit, locale)}`,
  );
  switch (signal.condition) {
    case "total_debt_increased_every_period":
      return t("investmentReasoning.riskBasis.debtIncreased", { series: figures.join(" → ") });
    case "latest_free_cash_flow_negative":
      return figures[0] ? t("investmentReasoning.riskBasis.cashNegative", { figure: figures[0] }) : null;
    case "capital_allocation_weak":
      return t("investmentReasoning.riskBasis.capitalAllocationWeak");
    default:
      return null;
  }
}

/**
 * Why "elevated financial risk" is shown -- or `null` when it is not.
 *
 * When Financial Risk itself is high: every signal its rule rests on, in
 * the evaluator's own order, each with its own figures -- none dropped,
 * none ranked -- followed by the one sentence that bounds it (reported
 * history, not leverage ratios, coverage, liquidity or ratings).
 *
 * When only Valuation Risk is high, the driver does not rest on the
 * company's finances at all, and the line says exactly that, with the
 * level Financial Risk actually has.
 */
export function riskBasisLabel(
  basis: RiskDriverBasisView | null | undefined,
  t: Translate,
  locale: string,
): string | null {
  if (!basis || basis.elevatedCategories.length === 0) return null;
  const financial = basis.financialRisk;
  if (!basis.elevatedCategories.includes("financial_risk")) {
    return t("investmentReasoning.riskBasis.valuationOnly", { level: t(RISK_LEVEL_KEY[financial.level]) });
  }
  const parts = financial.determining
    .map((name) => financial.signals.find((s) => s.signal === name))
    .filter((s): s is FinancialRiskSignalBasisView => s !== undefined)
    .map((s) => firingSignalLabel(s, t, locale))
    .filter((label): label is string => label !== null);
  if (parts.length === 0) return null;
  const sentences = [t("investmentReasoning.riskBasis.financial", { basis: parts.join("; ") })];
  if (basis.elevatedCategories.includes("valuation_risk")) sentences.push(t("investmentReasoning.riskBasis.alsoValuation"));
  sentences.push(t("investmentReasoning.riskBasis.scope"));
  return sentences.join(" ");
}
