import { StatusBadge } from "../foundation";
import { useTranslation } from "../i18n";
import { PRIORITY_LEVEL_KEY, PRIORITY_LEVEL_TONE, type PriorityLevel } from "../status/statusTone";

/**
 * The one qualitative priority badge (Deliverable 3) -- used identically
 * everywhere the agenda appears (Daily Brief, Portfolio). Never a
 * number: the wire value is already one of `PriorityLevel`'s four
 * string members, rendered through `StatusBadge` exactly like every
 * other categorical status in this codebase.
 */
export function PriorityBadge({ priority }: { priority: PriorityLevel }) {
  const { t } = useTranslation();
  return <StatusBadge label={t(PRIORITY_LEVEL_KEY[priority])} tone={PRIORITY_LEVEL_TONE[priority]} />;
}
