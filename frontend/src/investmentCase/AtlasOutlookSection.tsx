import { Divider, Inline, Label, Stack, StatusBadge, StatusText, Text } from "../foundation";
import {
  CHANGE_DIRECTION_SYMBOL,
  describeChange,
  type ChangeFindingView,
  type Translate,
} from "../changeIntelligence/describeChange";
import { CONVICTION_LEVEL_KEY, CONVICTION_TONE, type ConvictionLevel } from "../status/statusTone";
import type { TranslationKey } from "../i18n";

/**
 * Atlas Outlook (Outlook Intelligence Sprint 1; hardened in the
 * Semantic Hardening Pass; Long-Term Expected Return v1 added a real
 * multi-year model). Consumes the real per-horizon `OutlookView`
 * `atlas.analysis_engine.outlook` now computes. See that module's own
 * docstring for the full derivation rules.
 *
 * **Short-Term renders a valuation-implied re-rating range; Long-Term
 * renders an assumption-driven, evidence-gated multi-year range --
 * neither is ever a forecast or a price target.** Short-Term
 * (`assumption.kind === "historical_fcf_yield_reversion"`) holds Free
 * Cash Flow fixed and varies only the market's own multiple. Long-Term
 * (`"historical_growth_with_terminal_reversion"`) additionally compounds
 * a real, realized historical Free Cash Flow growth-rate range -- never
 * an invented forward estimate -- toward the same kind of historical
 * -median terminal yield. `ExpectedReturnField`/`ScenarioField` render
 * different disclosure copy depending on which `assumption.kind` is
 * present, keyed off `growthRate` being non-null (Long-Term) or null
 * (Short-Term), never off which horizon panel happens to be showing --
 * the assumption itself is the source of truth. `expectedReturnLabel`
 * stays shared; an investor reading AAPL's real short-term range should
 * be able to see, without digging, exactly what assumption produced
 * each number and how many historical observations it drew from, not
 * just the percentage.
 *
 * **Calibration Sprint (Part 10): Bull/Base/Bear are two different
 * concepts wearing the same three names.** Short-Term's `bullCaseLabel`
 * /`baseCaseLabel`/`bearCaseLabel` ("Valuation Bull/Base/Bear") are
 * accurate there -- the market's own multiple is the only thing that
 * varies. Long-Term's three scenarios share one terminal valuation and
 * differ *only* on the realized Free Cash Flow growth assumption, so
 * they render under `growthBullCaseLabel`/`growthBaseCaseLabel`/
 * `growthBearCaseLabel` ("Business-Growth Bull/Base/Bear") instead --
 * see `scenarioLabelKey`'s own selection logic, keyed off
 * `assumption.growthRate`, the identical real signal already used for
 * the assumption-disclosure copy above.
 *
 * **Conviction is disclosed as a bounded derivation, not an
 * independent model.** See `atlas.analysis_engine.outlook
 * .HorizonOutlook.conviction`'s own docstring -- the fixed caption
 * under each Conviction badge here is that same disclosure, always
 * shown, never hidden behind a tooltip.
 *
 * **Momentum can be `mixed`.** `ThesisImpact.MIXED` is no longer
 * collapsed into `stable` -- see `outlook.derive_outlook_momentum`'s
 * own docstring.
 *
 * **Momentum and What Changed are still shared across both horizons.**
 * Both derive from the one real, case-wide `ChangeIntelligence`
 * comparison this codebase computes today -- there is no horizon-specific
 * split of "is Atlas's view improving" or "what changed since last
 * time" yet, so showing the identical real fact under each heading
 * would be a duplicate rendering, not two different facts. Key Drivers,
 * by contrast, genuinely differ per horizon now (see `outlook.py`'s own
 * `_short_term_drivers`/`_long_term_drivers`), so each panel renders
 * its own.
 */

export type OutlookGapKind = "no_historical_valuation_range" | "valuation_not_conclusive" | "no_durable_growth_trajectory";
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
  | "margin_trend";
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
  horizonMonthsLow: number;
  horizonMonthsHigh: number;
  assumption: OutlookAssumptionView;
}

export interface OutlookScenarioView {
  kind: ScenarioKind;
  returnPercent: number;
  assumption: OutlookAssumptionView;
  driver: OutlookDriverKind;
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

export interface OutlookView {
  shortTerm: HorizonOutlookView;
  longTerm: HorizonOutlookView;
}

export const GAP_KEY: Record<OutlookGapKind, TranslationKey> = {
  no_historical_valuation_range: "investmentCase.outlook.gap.noHistoricalValuationRange",
  valuation_not_conclusive: "investmentCase.outlook.gap.valuationNotConclusive",
  no_durable_growth_trajectory: "investmentCase.outlook.gap.noDurableGrowthTrajectory",
};

const SCENARIO_LABEL_KEY: Record<ScenarioKind, TranslationKey> = {
  bull: "investmentCase.outlook.bullCaseLabel",
  base: "investmentCase.outlook.baseCaseLabel",
  bear: "investmentCase.outlook.bearCaseLabel",
};

/** Calibration Sprint (Part 10): Long-Term's three scenarios share one
 * terminal valuation and differ *only* on the Free Cash Flow growth
 * assumption -- calling them "Valuation Bull/Base/Bear" (Short-Term's
 * own, accurate label, where valuation genuinely is the only lever)
 * would misrepresent Long-Term as if margins/capital-allocation/
 * valuation were all independently modeled. Selected by
 * `scenario.assumption.growthRate != null`, the same real signal
 * `ExpectedReturnField`/`ScenarioField` already use to distinguish the
 * two assumption kinds -- never by which panel happens to be
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
};

export function formatPercent(value: number): string {
  const percent = value * 100;
  const sign = percent > 0 ? "+" : "";
  return `${sign}${percent.toFixed(1)}%`;
}

/** Unsigned -- an FCF yield is a ratio, never a gain/loss, so it never
 * carries the `formatPercent` +/- convention returns use. */
function formatYield(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function UnavailableField({ label, gap, t }: { label: string; gap: OutlookGapKind; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Label>{label}</Label>
      <StatusText label={t("investmentCase.outlook.notYetComputed")} tone="neutral" />
      <Text as="p" color="tertiary">
        {t(GAP_KEY[gap])}
      </Text>
    </Stack>
  );
}

function ExpectedReturnField({ expectedReturn, t }: { expectedReturn: ExpectedReturnRangeView; t: Translate }) {
  const labelKey =
    expectedReturn.assumption.growthRate != null
      ? "investmentCase.outlook.expectedReturnLabel.growth"
      : "investmentCase.outlook.expectedReturnLabel";
  return (
    <Stack gap="metadata">
      <Label>{t(labelKey)}</Label>
      <Text as="p" style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
        {formatPercent(expectedReturn.lowPercent)} {"→"} {formatPercent(expectedReturn.highPercent)}
      </Text>
      <Text as="p" color="tertiary">
        {t("investmentCase.outlook.returnBasisNote", {
          basis: t(
            expectedReturn.basis === "cumulative"
              ? "investmentCase.outlook.basis.cumulative"
              : "investmentCase.outlook.basis.annualized",
          ),
          low: String(expectedReturn.horizonMonthsLow),
          high: String(expectedReturn.horizonMonthsHigh),
        })}
      </Text>
      <Text as="p" color="tertiary">
        {expectedReturn.assumption.growthRate != null
          ? t("investmentCase.outlook.growthAssumptionNote", {
              growthRate: formatPercent(expectedReturn.assumption.growthRate),
              targetYield: formatYield(expectedReturn.assumption.targetFcfYield),
              years: String(expectedReturn.assumption.horizonYears ?? expectedReturn.horizonMonthsHigh / 12),
            })
          : t("investmentCase.outlook.rerangeAssumptionNote")}
      </Text>
    </Stack>
  );
}

function ScenarioField({ scenario, t }: { scenario: OutlookScenarioView; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Label>{t(scenarioLabelKey(scenario))}</Label>
      <Text as="p" style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
        {formatPercent(scenario.returnPercent)}
      </Text>
      <Text as="p" color="tertiary">
        {scenario.assumption.growthRate != null
          ? t("investmentCase.outlook.scenarioGrowthAssumptionNote", {
              growthRate: formatPercent(scenario.assumption.growthRate),
              targetYield: formatYield(scenario.assumption.targetFcfYield),
            })
          : t("investmentCase.outlook.scenarioAssumptionNote", {
              targetYield: formatYield(scenario.assumption.targetFcfYield),
            })}
      </Text>
    </Stack>
  );
}

function HorizonPanel({
  headingKey,
  horizon,
  t,
}: {
  headingKey: "shortTerm" | "longTerm";
  horizon: HorizonOutlookView;
  t: Translate;
}) {
  return (
    <Stack gap="metadata" style={{ flex: "1 1 280px", minWidth: 0 }}>
      <Text as="p" style={{ fontWeight: 600 }}>
        {t(`investmentCase.outlook.${headingKey}.heading` as const)}
      </Text>

      <Inline gap="inter-section" wrap align="start">
        {horizon.expectedReturn ? (
          <ExpectedReturnField expectedReturn={horizon.expectedReturn} t={t} />
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
        <Stack gap="metadata">
          <Label>{t("investmentCase.outlook.convictionLabel")}</Label>
          <StatusBadge label={t(CONVICTION_LEVEL_KEY[horizon.conviction])} tone={CONVICTION_TONE[horizon.conviction]} />
          <Text as="p" color="tertiary">
            {t("investmentCase.outlook.convictionCaption")}
          </Text>
        </Stack>
      </Inline>

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
          horizon.scenarios.map((scenario) => <ScenarioField key={scenario.kind} scenario={scenario} t={t} />)
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

      <Stack gap="metadata">
        <Label>{t("investmentCase.outlook.momentumLabel")}</Label>
        <StatusText label={t(MOMENTUM_KEY[horizon.momentum])} tone={MOMENTUM_TONE[horizon.momentum]} />
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
    </Stack>
  );
}

export function AtlasOutlookSection({
  outlook,
  latestChanges,
  t,
}: {
  outlook: OutlookView;
  latestChanges: ChangeFindingView[];
  t: Translate;
}) {
  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.outlook.heading")}</Label>

      <Inline gap="inter-section" wrap align="start">
        <HorizonPanel headingKey="shortTerm" horizon={outlook.shortTerm} t={t} />
        <HorizonPanel headingKey="longTerm" horizon={outlook.longTerm} t={t} />
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
