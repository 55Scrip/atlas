import type { CSSProperties } from "react";
import { Inline, Label, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { AtlasHorizon, AtlasQualitative, AtlasRating, QualitativeLevel } from "./atlasRatingModel";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * Atlas UX Phase 7A (Semantic Investment Model, Foundation Sprint) --
 * the seven-category bar Investment Case leads with, right after the
 * Hero: Company / Investment / Portfolio / Evidence as a rated 0-10
 * number (`atlasRatingModel.ts`, never fabricated -- "Not rated yet"
 * when the real inputs aren't there), Upside / Risk as the brief's own
 * four qualitative levels (independent of each other -- a case can be
 * Very High Upside *and* Very High Risk at once), Horizon as Outlook's
 * own real short/long-term timeframe. No new analysis anywhere here:
 * every value is a direct read of `atlasRatingModel.ts`'s already-
 * tested derivation over data this page already fetched.
 *
 * Deliberately no per-tile expand affordance -- the rest of the page,
 * now reordered to Outlook -> Investment Argument -> Atlas Reasoning
 * -> Evidence right below this bar, already *is* each rating's full
 * explanation. A second, per-tile disclosure here would just be a
 * second way to reach the same content one scroll away.
 */

const RATING_TIER_TONE: Record<AtlasRating["tier"], StatusTone> = {
  excellent: "positive",
  good: "positive",
  fair: "neutral",
  weak: "caution",
  poor: "critical",
  missing: "neutral",
  not_applicable: "neutral",
};

const RATING_TIER_LABEL_KEY: Record<AtlasRating["tier"], TranslationKey> = {
  excellent: "investmentCase.ratings.tier.excellent",
  good: "investmentCase.ratings.tier.good",
  fair: "investmentCase.ratings.tier.fair",
  weak: "investmentCase.ratings.tier.weak",
  poor: "investmentCase.ratings.tier.poor",
  missing: "investmentCase.ratings.missing",
  not_applicable: "investmentCase.ratings.notApplicable",
};

const QUALITATIVE_TONE: Record<"upside" | "risk", Record<QualitativeLevel, StatusTone>> = {
  upside: { low: "neutral", moderate: "neutral", high: "positive", very_high: "positive" },
  risk: { low: "positive", moderate: "neutral", high: "caution", very_high: "critical" },
};

const QUALITATIVE_LABEL_KEY: Record<QualitativeLevel, TranslationKey> = {
  low: "investmentCase.ratings.qualitative.low",
  moderate: "investmentCase.ratings.qualitative.moderate",
  high: "investmentCase.ratings.qualitative.high",
  very_high: "investmentCase.ratings.qualitative.veryHigh",
};

const QUALITATIVE_FILL: Record<QualitativeLevel, number> = { low: 1, moderate: 2, high: 3, very_high: 4 };

const HORIZON_BUCKET_KEY: Record<Exclude<AtlasHorizon["bucket"], "missing">, TranslationKey> = {
  near_term: "investmentCase.ratings.horizon.nearTerm",
  one_to_two_quarters: "investmentCase.ratings.horizon.oneToTwoQuarters",
  one_to_two_years: "investmentCase.ratings.horizon.oneToTwoYears",
  three_to_five_years: "investmentCase.ratings.horizon.threeToFiveYears",
  long_term: "investmentCase.ratings.horizon.longTerm",
};

const TILE_STYLE: CSSProperties = { flex: "1 1 150px", minWidth: 0 };

function RatingTile({ labelKey, rating, t }: { labelKey: TranslationKey; rating: AtlasRating; t: Translate }) {
  return (
    <div style={TILE_STYLE}>
      <Stack gap="metadata">
        <Label>{t(labelKey)}</Label>
        {rating.score !== null ? (
          <Inline gap="metadata" align="baseline">
            <Text as="span" style={{ fontWeight: 700, fontSize: "var(--type-size-h4)", fontVariantNumeric: "tabular-nums" }}>
              {rating.score.toFixed(1)}
            </Text>
            <Text as="span" color="tertiary">
              / 10
            </Text>
          </Inline>
        ) : (
          <Text as="span" color="tertiary">
            {t(RATING_TIER_LABEL_KEY[rating.tier])}
          </Text>
        )}
        {rating.score !== null && <StatusBadge label={t(RATING_TIER_LABEL_KEY[rating.tier])} tone={RATING_TIER_TONE[rating.tier]} />}
      </Stack>
    </div>
  );
}

function QualitativeDots({ level, kind }: { level: QualitativeLevel; kind: "upside" | "risk" }) {
  const filled = QUALITATIVE_FILL[level];
  const tone = QUALITATIVE_TONE[kind][level];
  const color =
    tone === "positive"
      ? "var(--status-positive, #4a9d6f)"
      : tone === "caution"
        ? "var(--status-caution, #c98a2c)"
        : tone === "critical"
          ? "var(--status-critical, #c9503f)"
          : "var(--color-text-tertiary)";
  return (
    <Inline gap="metadata" aria-hidden="true">
      {[1, 2, 3, 4].map((i) => (
        <span
          key={i}
          style={{
            display: "inline-block",
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: i <= filled ? color : "var(--color-border-hairline)",
          }}
        />
      ))}
    </Inline>
  );
}

function QualitativeTile({
  labelKey,
  kind,
  value,
  t,
}: {
  labelKey: TranslationKey;
  kind: "upside" | "risk";
  value: AtlasQualitative;
  t: Translate;
}) {
  return (
    <div style={TILE_STYLE}>
      <Stack gap="metadata">
        <Label>{t(labelKey)}</Label>
        {value.level !== "missing" ? (
          <>
            <Text as="span" style={{ fontWeight: 700, fontSize: "var(--type-size-h5)" }}>
              {t(QUALITATIVE_LABEL_KEY[value.level])}
            </Text>
            <QualitativeDots level={value.level} kind={kind} />
          </>
        ) : (
          <Text as="span" color="tertiary">
            {t("investmentCase.ratings.missing")}
          </Text>
        )}
      </Stack>
    </div>
  );
}

function HorizonTile({ horizon, t }: { horizon: AtlasHorizon; t: Translate }) {
  return (
    <div style={TILE_STYLE}>
      <Stack gap="metadata">
        <Label>{t("investmentCase.ratings.horizon.label")}</Label>
        {horizon.bucket !== "missing" ? (
          <>
            <Text as="span" style={{ fontWeight: 700, fontSize: "var(--type-size-h5)" }}>
              {t(HORIZON_BUCKET_KEY[horizon.bucket])}
            </Text>
            {horizon.monthsLow !== null && horizon.monthsHigh !== null && (
              <Text as="span" color="tertiary">
                {t("investmentCase.ratings.horizon.monthRange", { low: horizon.monthsLow, high: horizon.monthsHigh })}
              </Text>
            )}
          </>
        ) : (
          <Text as="span" color="tertiary">
            {t("investmentCase.ratings.missing")}
          </Text>
        )}
      </Stack>
    </div>
  );
}

export interface SevenCategoriesInput {
  company: AtlasRating;
  investment: AtlasRating;
  portfolio: AtlasRating;
  evidence: AtlasRating;
  upside: AtlasQualitative;
  risk: AtlasQualitative;
  horizon: AtlasHorizon;
}

export function SevenCategoriesSection({ ratings, t }: { ratings: SevenCategoriesInput; t: Translate }) {
  return (
    <Surface tier="elevated">
      <Inline gap="inter-section" wrap align="start">
        <RatingTile labelKey="investmentCase.ratings.company.label" rating={ratings.company} t={t} />
        <RatingTile labelKey="investmentCase.ratings.investment.label" rating={ratings.investment} t={t} />
        <RatingTile labelKey="investmentCase.ratings.portfolio.label" rating={ratings.portfolio} t={t} />
        <RatingTile labelKey="investmentCase.ratings.evidence.label" rating={ratings.evidence} t={t} />
        <QualitativeTile labelKey="investmentCase.ratings.upside.label" kind="upside" value={ratings.upside} t={t} />
        <QualitativeTile labelKey="investmentCase.ratings.risk.label" kind="risk" value={ratings.risk} t={t} />
        <HorizonTile horizon={ratings.horizon} t={t} />
      </Inline>
    </Surface>
  );
}

/**
 * Case DNA -- exactly one sentence, reusing `deriveHeroTension`'s own
 * already-real, already-tested six-sentence bank (`HERO_WHY_KEY` in
 * `HeroCard.tsx`) rather than a second, independently-worded summary.
 * Passed in pre-resolved (the sentence itself, already translated) so
 * this component owns only presentation, not a second computation of
 * the same tension `HeroCard` already derives from the identical
 * inputs.
 */
export function CaseDnaLine({ sentence, t }: { sentence: string; t: Translate }) {
  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.caseDna.label")}</Label>
      <Text
        as="p"
        style={{
          fontFamily: "var(--type-family-display)",
          fontSize: "var(--type-size-h5)",
          lineHeight: 1.5,
          color: "var(--color-text-primary)",
          maxWidth: "70ch",
        }}
      >
        {sentence}
      </Text>
    </Stack>
  );
}
