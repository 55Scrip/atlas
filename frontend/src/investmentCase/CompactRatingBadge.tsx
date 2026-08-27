import { StatusBadge } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { AtlasRating } from "./atlasRatingModel";
import { RATING_TIER_LABEL_KEY, RATING_TIER_TONE } from "./SevenCategoriesSection";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * Atlas UX Phase 7B (Product Model Propagation) -- the same rated
 * pillar `SevenCategoriesSection`'s `RatingTile` renders on Investment
 * Case, compressed into one small badge for a table row or list card
 * where a full tile has no room. Same source (`atlasRatingModel.ts`),
 * same tier tone/label maps -- a ticker's Investment/Portfolio/Evidence
 * rating reads identically here as on its own Investment Case, never a
 * second, differently-scaled presentation of the same number. `score
 * === null` (`missing`/`not_applicable`) renders an em dash rather than
 * the full "Not rated yet" sentence, matching this codebase's existing
 * compact-cell convention (e.g. Watchlist's own "notAvailable" glyph)
 * -- never a fabricated placeholder number.
 */
export function CompactRatingBadge({ labelKey, rating, t }: { labelKey: TranslationKey; rating: AtlasRating; t: Translate }) {
  const label = `${t(labelKey)} ${rating.score !== null ? rating.score.toFixed(1) : "—"}`;
  return <StatusBadge label={label} tone={RATING_TIER_TONE[rating.tier]} title={t(RATING_TIER_LABEL_KEY[rating.tier])} />;
}
