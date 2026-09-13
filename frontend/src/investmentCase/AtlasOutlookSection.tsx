import { Divider, Inline, Label, Stack, StatusText, Text } from "../foundation";
import { ExpandableDetail } from "./ExpandableDetail";
import {
  CHANGE_DIRECTION_SYMBOL,
  describeChange,
  type ChangeFindingView,
  type Translate,
} from "../changeIntelligence/describeChange";
import type { ConvictionLevel } from "../status/statusTone";
import type { TranslationKey } from "../i18n";

/**
 * Valuation sensitivity (Outlook Intelligence Sprint 1; reframed in
 * Outlook -> Sensitivity). Consumes the per-horizon `OutlookView`
 * `atlas.analysis_engine.outlook` computes; `role` is always
 * `"sensitivity"`. See that module's docstring for the derivation.
 *
 * **Conditional arithmetic, never a forecast.** Re-rating (Short-Term)
 * holds today's free cash flow fixed and re-prices it at the company's
 * own historical FCF yields -- instantaneous, so it shows no horizon.
 * The 4-year sensitivity (Long-Term) compounds the company's own
 * historical FCF growth for exactly four years and re-prices at the
 * historical median yield. The endpoints are named for their assumption
 * ("At median valuation"), never Bull/Base/Bear -- "base" read as "most
 * likely", and no probability exists. The assumption kind is read off
 * `assumption.growthRate` (non-null only for the growth sensitivity),
 * never off which panel is rendering.
 *
 * **Withheld endpoints.** An endpoint anchored on a non-comparable year
 * (near-zero free cash flow) arrives with `returnPercent: null` and a
 * `withheldReason`; it renders the reason and its anchor year, never a
 * number, a zero or a capped value.
 *
 * **Precision** is display-only (`formatPercent`): one decimal below
 * 10%, whole percents from 10% -- the engine's own figure is never
 * rounded or capped for the calculation. Numbers go through
 * `Intl.NumberFormat` in the page's locale, the same way the reasoning
 * section formats its yields, so Swedish reads "+4,3 %" and English
 * "+4.3%".
 *
 * **No score.** Nothing here, and nothing reading this payload, turns
 * an endpoint into an "upside" rating: a sensitivity says what a price
 * implies under stated assumptions, not how attractive it is.
 *
 * No conviction badge: the case-wide Conviction it echoed read as
 * confidence in a forecast. Momentum and What Changed stay case-wide
 * (one real `ChangeIntelligence` comparison), rendered once per horizon
 * and once below respectively.
 */

export type OutlookGapKind =
  | "no_historical_valuation_range"
  | "valuation_not_conclusive"
  | "no_durable_growth_trajectory"
  | "near_zero_fcf_anchor"
  | "valuation_not_applicable";
export type ReturnBasis = "cumulative" | "annualized";
export type ScenarioKind = "bull" | "base" | "bear";
export type OutlookMomentumKind = "strengthening" | "stable" | "mixed" | "weakening" | "unavailable";
export type OutlookDriverKind =
  | "valuation_rerating"
  | "revenue_trend"
  | "growth"
  | "capital_allocation"
  | "financial_risk"
  | "business_risk"
  | "valuation_risk"
  | "fcf_growth_trend"
  | "debt_trend"
  | "margin_trend"
  | "moat"
  | "reinvestment_opportunity";
export type OutlookDriverDirection = "positive" | "negative" | "neutral";

export interface OutlookAssumptionView {
  kind: "historical_fcf_yield_reversion" | "historical_growth_with_terminal_reversion";
  currentFcfYield: number;
  targetFcfYield: number;
  observationCount: number;
  /** Long-Term Expected Return v1: `null` for every Short-Term
   * assumption, always populated together for Long-Term -- see
   * `atlas.analysis_engine.outlook.OutlookAssumption`'s own docstring. */
  growthRate: number | null;
  horizonYears: number | null;
  growthObservationCount: number | null;
}

export interface ExpectedReturnRangeView {
  lowPercent: number;
  highPercent: number;
  basis: ReturnBasis;
  /** `null` for the re-rating (no horizon); exactly 48 for the 4-year
   * sensitivity. */
  horizonMonthsLow: number | null;
  horizonMonthsHigh: number | null;
  assumption: OutlookAssumptionView;
}

export interface OutlookScenarioView {
  kind: ScenarioKind;
  /** `null` exactly when `withheldReason` says why. */
  returnPercent: number | null;
  assumption: OutlookAssumptionView;
  driver: OutlookDriverKind;
  withheldReason: OutlookGapKind | null;
  /** The fiscal period end(s) the endpoint rests on: one year (two when
   * a median straddles two) for the re-rating; window start/end pairs
   * for the 4-year sensitivity. */
  anchorPeriods: string[];
}

export interface OutlookDriverView {
  kind: OutlookDriverKind;
  direction: OutlookDriverDirection;
  sourceFindingId: string | null;
}

export interface HorizonOutlookView {
  horizon: "short_term" | "long_term";
  expectedReturn: ExpectedReturnRangeView | null;
  expectedReturnGap: OutlookGapKind | null;
  scenarios: OutlookScenarioView[];
  scenariosGap: OutlookGapKind | null;
  conviction: ConvictionLevel;
  momentum: OutlookMomentumKind;
  keyDrivers: OutlookDriverView[];
}

/** The only role Outlook has: conditional sensitivity arithmetic. Typed
 * as a literal so a future forecast role could never be rendered with
 * this section's "not a forecast" copy by accident. */
export const OUTLOOK_ROLE = "sensitivity";

export interface OutlookView {
  role: typeof OUTLOOK_ROLE;
  shortTerm: HorizonOutlookView;
  longTerm: HorizonOutlookView;
}

export const GAP_KEY: Record<OutlookGapKind, TranslationKey> = {
  no_historical_valuation_range: "investmentCase.outlook.gap.noHistoricalValuationRange",
  valuation_not_conclusive: "investmentCase.outlook.gap.valuationNotConclusive",
  no_durable_growth_trajectory: "investmentCase.outlook.gap.noDurableGrowthTrajectory",
  near_zero_fcf_anchor: "investmentCase.outlook.gap.nearZeroFcfAnchor",
  valuation_not_applicable: "investmentCase.outlook.gap.valuationNotApplicable",
};

/** The one-word state above a gap's explanation: not applicable and
 * withheld are final states, not "not yet computed". */
const GAP_STATUS_KEY: Record<OutlookGapKind, TranslationKey> = {
  no_historical_valuation_range: "investmentCase.outlook.notYetComputed",
  valuation_not_conclusive: "investmentCase.outlook.notYetComputed",
  no_durable_growth_trajectory: "investmentCase.outlook.notYetComputed",
  near_zero_fcf_anchor: "investmentCase.outlook.withheldStatus",
  valuation_not_applicable: "investmentCase.outlook.notApplicable",
};

const SCENARIO_LABEL_KEY: Record<ScenarioKind, TranslationKey> = {
  bull: "investmentCase.outlook.bullCaseLabel",
  base: "investmentCase.outlook.baseCaseLabel",
  bear: "investmentCase.outlook.bearCaseLabel",
};

/** The 4-year sensitivity's endpoints share one terminal valuation and
 * differ *only* on the growth assumption, so they are named for growth
 * ("At median growth"), the re-rating's for valuation. Selected by
 * `scenario.assumption.growthRate != null` -- never by which panel is
 * rendering. */
const GROWTH_SCENARIO_LABEL_KEY: Record<ScenarioKind, TranslationKey> = {
  bull: "investmentCase.outlook.growthBullCaseLabel",
  base: "investmentCase.outlook.growthBaseCaseLabel",
  bear: "investmentCase.outlook.growthBearCaseLabel",
};

function scenarioLabelKey(scenario: OutlookScenarioView): TranslationKey {
  return scenario.assumption.growthRate != null
    ? GROWTH_SCENARIO_LABEL_KEY[scenario.kind]
    : SCENARIO_LABEL_KEY[scenario.kind];
}

const MOMENTUM_KEY: Record<OutlookMomentumKind, TranslationKey> = {
  strengthening: "investmentCase.outlook.momentum.strengthening",
  stable: "investmentCase.outlook.momentum.stable",
  mixed: "investmentCase.outlook.momentum.mixed",
  weakening: "investmentCase.outlook.momentum.weakening",
  unavailable: "investmentCase.outlook.notYetComputed",
};

const MOMENTUM_TONE: Record<OutlookMomentumKind, "positive" | "caution" | "critical" | "neutral"> = {
  strengthening: "positive",
  stable: "neutral",
  mixed: "caution",
  weakening: "critical",
  unavailable: "neutral",
};

const DRIVER_LABEL_KEY: Record<OutlookDriverKind, TranslationKey> = {
  valuation_rerating: "investmentCase.outlook.driver.valuationRerating",
  revenue_trend: "investmentCase.outlook.driver.revenueTrend",
  growth: "investmentCase.outlook.driver.growth",
  capital_allocation: "investmentCase.outlook.driver.capitalAllocation",
  financial_risk: "investmentCase.outlook.driver.financialRisk",
  business_risk: "investmentCase.outlook.driver.businessRisk",
  valuation_risk: "investmentCase.outlook.driver.valuationRisk",
  fcf_growth_trend: "investmentCase.outlook.driver.fcfGrowthTrend",
  debt_trend: "investmentCase.outlook.driver.debtTrend",
  margin_trend: "investmentCase.outlook.driver.marginTrend",
  moat: "investmentCase.outlook.driver.moat",
  reinvestment_opportunity: "investmentCase.outlook.driver.reinvestmentOpportunity",
};

/** Display precision only: one decimal below 10%, whole percents from
 * 10% (a "+4998.3%" re-rating implied precision the anchor never had).
 * Never a cap -- the magnitude is shown as computed. Signed, in the
 * page's locale; a value that rounds to zero carries no sign. */
export function formatPercent(value: number, locale: string): string {
  // Decided on the one-decimal rounding, so 9.96% reads "+10%", not "+10.0%".
  const digits = Math.abs(Number((value * 100).toFixed(1))) < 10 ? 1 : 0;
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    signDisplay: "exceptZero",
  }).format(value);
}

/** A fiscal period end ("2016-12-31") as its fiscal year ("2016"). */
function fiscalYear(period: string): string {
  return period.slice(0, 4);
}

/** The anchor fiscal years, oldest first (a median's two years arrive
 * in yield order). */
function anchorYears(scenario: OutlookScenarioView): string {
  return [...scenario.anchorPeriods].sort().map(fiscalYear).join(", ");
}

/** Anchor provenance: the re-rating's year(s), or the 4-year windows as
 * "2016–2020", oldest first. */
function describeAnchors(scenario: OutlookScenarioView, t: Translate): string | null {
  if (scenario.anchorPeriods.length === 0) return null;
  if (scenario.assumption.growthRate != null) {
    const windows: string[] = [];
    for (let i = 0; i + 1 < scenario.anchorPeriods.length; i += 2) {
      windows.push(`${fiscalYear(scenario.anchorPeriods[i] ?? "")}–${fiscalYear(scenario.anchorPeriods[i + 1] ?? "")}`);
    }
    return t("investmentCase.outlook.anchorWindow", { periods: windows.sort().join(", ") });
  }
  return t("investmentCase.outlook.anchorYear", { periods: anchorYears(scenario) });
}

/** Unsigned -- an FCF yield is a ratio, never a gain/loss, so it never
 * carries the `formatPercent` +/- convention returns use. */
function formatYield(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value);
}

function UnavailableField({ label, gap, t }: { label: string; gap: OutlookGapKind; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Label>{label}</Label>
      <StatusText label={t(GAP_STATUS_KEY[gap])} tone="neutral" />
      <Text as="p" color="tertiary">
        {t(GAP_KEY[gap])}
      </Text>
    </Stack>
  );
}

function ExpectedReturnField({
  expectedReturn,
  scenarios,
  t,
  locale,
}: {
  expectedReturn: ExpectedReturnRangeView;
  scenarios: OutlookScenarioView[];
  t: Translate;
  locale: string;
}) {
  // A range over the endpoints shown: say so when one is withheld, so
  // "−64 % → +4,3 %" is never read as the withheld endpoint's value.
  const withheld = scenarios.filter((scenario) => scenario.returnPercent === null);
  const isGrowth = expectedReturn.assumption.growthRate != null;
  const years = expectedReturn.assumption.horizonYears ?? (expectedReturn.horizonMonthsHigh ?? 0) / 12;
  const single = expectedReturn.lowPercent === expectedReturn.highPercent;
  return (
    <Stack gap="metadata">
      <Label>{t(isGrowth ? "investmentCase.outlook.expectedReturnLabel.growth" : "investmentCase.outlook.expectedReturnLabel")}</Label>
      <Text as="p" style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
        {single
          ? formatPercent(expectedReturn.lowPercent, locale)
          : `${formatPercent(expectedReturn.lowPercent, locale)} → ${formatPercent(expectedReturn.highPercent, locale)}`}
      </Text>
      {withheld.length > 0 && (
        <Text as="p" color="secondary">
          {t("investmentCase.outlook.partialRangeNote", {
            periods: [...new Set(withheld.flatMap((scenario) => scenario.anchorPeriods.map(fiscalYear)))].sort().join(", "),
          })}
        </Text>
      )}
      <Text as="p" color="tertiary">
        {isGrowth
          ? t("investmentCase.outlook.longTermBasisNote", { years: String(years) })
          : t("investmentCase.outlook.shortTermBasisNote")}
      </Text>
      <Text as="p" color="tertiary">
        {isGrowth
          ? t("investmentCase.outlook.growthAssumptionNote", {
              growthRate: formatPercent(expectedReturn.assumption.growthRate ?? 0, locale),
              targetYield: formatYield(expectedReturn.assumption.targetFcfYield, locale),
              years: String(years),
            })
          : t("investmentCase.outlook.rerangeAssumptionNote")}
      </Text>
    </Stack>
  );
}

function ScenarioField({ scenario, t, locale }: { scenario: OutlookScenarioView; t: Translate; locale: string }) {
  if (scenario.returnPercent === null) {
    // Withheld: the reason names the anchor year. Its assumption (a
    // near-zero yield, "0.0%") would only restate the pathology as if it
    // were a usable input.
    return (
      <Stack gap="metadata">
        <Label>{t(scenarioLabelKey(scenario))}</Label>
        <Text as="p" color="secondary">
          {t("investmentCase.outlook.withheld", { period: anchorYears(scenario) })}
        </Text>
      </Stack>
    );
  }
  const anchors = describeAnchors(scenario, t);
  return (
    <Stack gap="metadata">
      <Label>{t(scenarioLabelKey(scenario))}</Label>
      <Text as="p" style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
        {formatPercent(scenario.returnPercent, locale)}
      </Text>
      <Text as="p" color="tertiary">
        {scenario.assumption.growthRate != null
          ? t("investmentCase.outlook.scenarioGrowthAssumptionNote", {
              growthRate: formatPercent(scenario.assumption.growthRate, locale),
              targetYield: formatYield(scenario.assumption.targetFcfYield, locale),
            })
          : t("investmentCase.outlook.scenarioAssumptionNote", {
              targetYield: formatYield(scenario.assumption.targetFcfYield, locale),
            })}
      </Text>
      {anchors && (
        <Text as="p" color="tertiary">
          {anchors}
        </Text>
      )}
    </Stack>
  );
}

function HorizonPanel({
  headingKey,
  horizon,
  t,
  locale,
}: {
  headingKey: "shortTerm" | "longTerm";
  horizon: HorizonOutlookView;
  t: Translate;
  locale: string;
}) {
  return (
    <Stack gap="metadata" style={{ flex: "1 1 280px", minWidth: 0 }}>
      <Text as="p" style={{ fontWeight: 600 }}>
        {t(`investmentCase.outlook.${headingKey}.heading` as const)}
      </Text>

      <Inline gap="inter-section" wrap align="start">
        {horizon.expectedReturn ? (
          <ExpectedReturnField expectedReturn={horizon.expectedReturn} scenarios={horizon.scenarios} t={t} locale={locale} />
        ) : (
          <UnavailableField
            label={t(
              headingKey === "longTerm"
                ? "investmentCase.outlook.expectedReturnLabel.growth"
                : "investmentCase.outlook.expectedReturnLabel",
            )}
            gap={horizon.expectedReturnGap ?? "valuation_not_conclusive"}
            t={t}
          />
        )}
      </Inline>

      {/* Convergence Sprint 1C: scenarios, their assumption prose and the
          key-driver list are the horizon's *workings*. On a real case they
          ran to roughly two screens per horizon -- three scenario values,
          three assumption sentences and up to a dozen driver bullets --
          ahead of Portfolio Fit and the investment argument. The horizon's
          own result (the sensitivity range and momentum) stays visible;
          the derivation is one click down, unchanged. */}
      <ExpandableDetail summaryLabel={t("investmentCase.outlook.scenarioDetailLabel")}>
        <Stack gap="metadata">
        {horizon.scenarios[0] && (
          <Text as="p" color="tertiary">
            {t(
              horizon.scenarios[0].assumption.growthRate != null
                ? "investmentCase.outlook.growthScenariosCaption"
                : horizon.scenarios[0].assumption.observationCount === 1
                  ? "investmentCase.outlook.scenariosCaptionOne"
                  : "investmentCase.outlook.scenariosCaptionOther",
              {
                count: String(horizon.scenarios[0].assumption.observationCount),
                growthCount: String(horizon.scenarios[0].assumption.growthObservationCount ?? 0),
              },
            )}
          </Text>
        )}
        <Inline gap="inter-section" wrap align="start">
          {horizon.scenarios.length > 0 ? (
            horizon.scenarios.map((scenario) => <ScenarioField key={scenario.kind} scenario={scenario} t={t} locale={locale} />)
          ) : (
            <UnavailableField
              label={
                headingKey === "longTerm"
                  ? `${t("investmentCase.outlook.growthBullCaseLabel")} / ${t("investmentCase.outlook.growthBaseCaseLabel")} / ${t("investmentCase.outlook.growthBearCaseLabel")}`
                  : `${t("investmentCase.outlook.bullCaseLabel")} / ${t("investmentCase.outlook.baseCaseLabel")} / ${t("investmentCase.outlook.bearCaseLabel")}`
              }
              gap={horizon.scenariosGap ?? "no_durable_growth_trajectory"}
              t={t}
            />
          )}
        </Inline>
        </Stack>
        <Stack gap="metadata">
          <Label>{t("investmentCase.outlook.keyDriversLabel")}</Label>
          {horizon.keyDrivers.length === 0 ? (
            <Text color="secondary">{t("investmentCase.outlook.noDrivers")}</Text>
          ) : (
            <Stack gap="metadata">
              {horizon.keyDrivers.map((driver, index) => (
                <Text as="p" key={`${driver.kind}-${index}`}>
                  <span aria-hidden="true">{CHANGE_DIRECTION_SYMBOL[driver.direction]} </span>
                  {t(DRIVER_LABEL_KEY[driver.kind])}
                </Text>
              ))}
            </Stack>
          )}
        </Stack>
      </ExpandableDetail>

      <Stack gap="metadata">
        <Label>{t("investmentCase.outlook.momentumLabel")}</Label>
        <StatusText label={t(MOMENTUM_KEY[horizon.momentum])} tone={MOMENTUM_TONE[horizon.momentum]} />
      </Stack>

    </Stack>
  );
}

export function AtlasOutlookSection({
  outlook,
  latestChanges,
  t,
  locale,
}: {
  outlook: OutlookView;
  latestChanges: ChangeFindingView[];
  t: Translate;
  locale: string;
}) {
  // Every word below describes a sensitivity; a payload claiming any
  // other role is not this section's to render.
  if (outlook.role !== OUTLOOK_ROLE) return null;
  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.outlook.heading")}</Label>
      <Text as="p" color="tertiary">
        {t("investmentCase.outlook.caption")}
      </Text>

      <Inline gap="inter-section" wrap align="start">
        <HorizonPanel headingKey="shortTerm" horizon={outlook.shortTerm} t={t} locale={locale} />
        <HorizonPanel headingKey="longTerm" horizon={outlook.longTerm} t={t} locale={locale} />
      </Inline>

      <Divider tone="hairline" />

      <Label>{t("investmentCase.outlook.whatChangedLabel")}</Label>
      {latestChanges.length === 0 ? (
        <Text color="secondary">{t("investmentCase.outlook.noChanges")}</Text>
      ) : (
        <Stack gap="metadata">
          {latestChanges.slice(0, 5).map((change) => (
            <Text as="p" key={change.id}>
              {describeChange(change, t)}
            </Text>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
