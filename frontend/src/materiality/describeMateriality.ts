import type { Translate } from "../changeIntelligence/describeChange";
import { MATERIALITY_LEVEL_KEY } from "../status/statusTone";
import { stanceReasonSentence } from "../stance/describeStance";
import type { MaterialEvidenceView } from "./materialityApi";

/**
 * Atlas Intelligence -- Materiality & Priority Engine. The sentence for
 * a `MaterialEvidenceView` is `stanceReasonSentence` (Sprint 2)
 * verbatim -- a materiality classification changes which item is shown
 * first, never the words used to describe it. This module adds only
 * the one genuinely new label: the materiality level itself.
 */

export function materialEvidenceSentence(item: MaterialEvidenceView, t: Translate): string {
  return stanceReasonSentence(item.reason, t);
}

export function materialityLevelLabel(item: MaterialEvidenceView, t: Translate): string {
  return t(MATERIALITY_LEVEL_KEY[item.materiality]);
}
