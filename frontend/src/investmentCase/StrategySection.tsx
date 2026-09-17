import { Text } from "../foundation";
import type { TranslationKey } from "../i18n";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * Strategy -- a real destination, deliberately empty.
 *
 * Atlas has no company-strategy representation. The repository audit
 * behind this sprint classified the capability as **B** (partial
 * strategy-relevant evidence, no coherent strategy model):
 *
 * - `atlas/core/application/strategy_signature/` recognizes coherence
 *   among the *investor's own* decision patterns (ATLAS-006). It says
 *   nothing about a company.
 * - `atlas/alpha/knowledge_strategy/` is research planning -- which
 *   knowledge domains are still missing for a ticker.
 * - `CommentaryCategory.STRATEGIC_PRIORITIES` (`earnings_call.py`) tags
 *   earnings-call statements, and `CommunicationConsistency
 *   .strategic_emphasis_shifted` reports that the emphasis among those
 *   tags moved. That is real evidence *about* strategy talk; it is not
 *   a model of how the company creates value.
 * - `business_quality_assessment/moat.py` says so itself: market share,
 *   brand, network effects, switching costs, ecosystem lock-in,
 *   regulatory barriers, distribution advantages and technology
 *   leadership are named, in that module, as things Atlas has no data
 *   source for.
 *
 * What a Strategy chapter has to answer -- how capital becomes
 * capability, how capability reaches customers, and how that turns into
 * money -- none of those four can answer. Dressing business-quality
 * scores or a handful of tagged quotations as "strategy" would be
 * exactly the fabrication this codebase refuses everywhere else, so the
 * chapter states its own absence and stops.
 *
 * It still exists, and still owns `#strategy`, because the architecture
 * is what this sprint is for: the Strategy Intelligence sprint fills
 * this component in, and every link already pointing here keeps
 * working.
 */
export function StrategySection({ t }: { t: Translate }) {
  /* Product Convergence Sprint 1B (Investment Case Compression): this
     rendered two paragraphs -- an "not yet available" line plus a
     paragraph about what Atlas does not yet model -- for 184px of
     vertical space saying nothing Atlas knows about the company.
     A stable deep-link destination does not need a large card. The
     chapter's status badge says "Not yet assessed" and that is the
     whole honest answer; the reasoning behind it belongs in this
     module's docstring, where an engineer reads it, not in the
     investor's default reading path. */
  return (
    <Text as="p" color="tertiary">
      {t("investmentCase.strategy.unavailableShort")}
    </Text>
  );
}
