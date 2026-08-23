import { StatusBadge } from "../foundation";
import { useTranslation } from "../i18n";
import { SIGNAL_NATURE_KEY, SIGNAL_NATURE_TONE, type SignalNature } from "../status/statusTone";

/**
 * Fix Sprint 4 (Daily Brief Signal Quality) -- the one new badge this
 * sprint adds, and the only thing it adds: whether an item's own
 * headline reflects a genuine change ("New") or a state that has
 * simply not stopped being true ("Ongoing"). Same `StatusBadge`
 * mechanism `PriorityBadge` already uses; deliberately a separate
 * badge, not a recolored `PriorityBadge`, since this distinguishes
 * *when* something is true, never how serious it is -- priority
 * already owns that judgment.
 */
export function SignalNatureBadge({ nature }: { nature: SignalNature }) {
  const { t } = useTranslation();
  return <StatusBadge label={t(SIGNAL_NATURE_KEY[nature])} tone={SIGNAL_NATURE_TONE[nature]} />;
}
