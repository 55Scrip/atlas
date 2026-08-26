import { StatusBadge } from "../foundation";
import { useTranslation } from "../i18n";
import { STANCE_LEVEL_KEY, STANCE_LEVEL_TONE, type StanceLevel } from "../status/statusTone";

/**
 * The one reusable Stance level badge (Atlas Intelligence Sprint 2),
 * used identically wherever a `StanceLevel` appears -- Portfolio,
 * Discovery, Compare -- mirroring `FitBadge`'s own precedent exactly.
 * Never a trade-sizing instruction: the wire value is one of
 * `StanceLevel`'s seven string members, rendered through the same
 * present-tense, non-imperative labels ("View strengthened," never
 * "Buy more") everywhere it appears.
 */
export function StanceBadge({ level, weight = "outline" }: { level: StanceLevel; weight?: "outline" | "strong" }) {
  const { t } = useTranslation();
  return <StatusBadge label={t(STANCE_LEVEL_KEY[level])} tone={STANCE_LEVEL_TONE[level]} weight={weight} />;
}
