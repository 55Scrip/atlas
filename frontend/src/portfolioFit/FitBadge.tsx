import { StatusBadge } from "../foundation";
import { useTranslation } from "../i18n";
import { FIT_RATING_KEY, FIT_RATING_TONE, type FitRating } from "../status/statusTone";

/**
 * The one reusable "Excellent / Good / Neutral / Weak / Poor Fit"
 * badge (Deliverable 3), used identically wherever Portfolio Fit
 * appears -- Investment Case, Discovery, Portfolio. Never a numeric
 * score: the wire value is already one of `FitRating`'s six string
 * members, rendered through `StatusBadge` exactly like every other
 * categorical status in this codebase (Conviction, Risk, Valuation).
 */
export function FitBadge({ rating }: { rating: FitRating }) {
  const { t } = useTranslation();
  return <StatusBadge label={t(FIT_RATING_KEY[rating])} tone={FIT_RATING_TONE[rating]} />;
}
