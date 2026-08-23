import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ALTERNATIVE_KIND_KEY } from "../opportunityCost/describeOpportunityCost";
import { LEVEL_KEY as RELIABILITY_LEVEL_KEY } from "../decisionReliability/describeDecisionReliability";
import { FIT_RATING_KEY } from "../status/statusTone";
import type { FitRating } from "../status/statusTone";
import type {
  PortfolioDecisionCategory,
  PortfolioDecisionReasonView,
  PortfolioDecisionReferenceView,
  PortfolioDecisionReasonSource,
} from "./portfolioDecisionApi";

/**
 * Language Audit (Deliverable 15) -- this module is the one place
 * `PortfolioDecisionCategory`/`PortfolioDecisionReasonView` (closed,
 * backend-internal names) are turned into plain investor language. No
 * portfolio-optimization wording, no AI wording, no prediction, no
 * target-allocation language, no "should always"/"optimal portfolio"
 * anywhere in rendered copy -- every reason routes through one of the
 * four already-translated closed vocabularies this codebase already
 * established (`FIT_RATING_KEY`/`KEY_FINDING_KEY`/`ALTERNATIVE_KIND_KEY`
 * /`RELIABILITY_LEVEL_KEY`), dispatched by `reason.source` -- the
 * exact same "tagged pointer, resolve through the real vocabulary it
 * names" discipline every prior Decision Layer sprint's own
 * `reasonLabel`/`reliabilityReasonLabel` already established. Never a
 * fifth, newly invented one.
 */

export const CATEGORY_KEY: Record<PortfolioDecisionCategory, TranslationKey> = {
  supports_portfolio: "portfolioDecision.category.supportsPortfolio",
  neutral: "portfolioDecision.category.neutral",
  requires_review: "portfolioDecision.category.requiresReview",
  conflicts_with_portfolio: "portfolioDecision.category.conflictsWithPortfolio",
  operationally_limited: "portfolioDecision.category.operationallyLimited",
  unknown: "portfolioDecision.category.unknown",
};

export const CATEGORY_TONE: Record<PortfolioDecisionCategory, StatusTone> = {
  supports_portfolio: "positive",
  neutral: "neutral",
  requires_review: "caution",
  conflicts_with_portfolio: "caution",
  operationally_limited: "caution",
  unknown: "neutral",
};

export const SOURCE_KEY: Record<PortfolioDecisionReasonSource, TranslationKey> = {
  portfolio_fit: "portfolioDecision.source.portfolioFit",
  portfolio_intelligence: "portfolioDecision.source.portfolioIntelligence",
  opportunity_cost: "portfolioDecision.source.opportunityCost",
  decision_reliability: "portfolioDecision.source.decisionReliability",
};

/**
 * Atlas Intelligence Sprint 16 (`atlas.alpha.portfolio_intelligence
 * .models.KeyFindingKind`) has no existing frontend translation map
 * anywhere in this codebase (`deriveDiscussionPrompts.ts` builds ad
 * hoc sentences, never a reusable closed map) -- this is the first
 * one, scoped to only the three members this package's own reasons
 * can ever name.
 */
export const KEY_FINDING_KEY: Partial<Record<string, TranslationKey>> = {
  high_concentration: "portfolioDecision.keyFinding.highConcentration",
  elevated_concentration: "portfolioDecision.keyFinding.elevatedConcentration",
  large_unallocated: "portfolioDecision.keyFinding.largeUnallocated",
};

/**
 * `frontend/src/routes/PortfolioPage.tsx`'s own `CONCENTRATION_LEVEL_KEY`
 * already maps these same four backend values to the same four
 * translation keys, but is module-private to that route file --
 * importing a domain describe module from a page component would be
 * backwards. This is the identical mapping (same keys, same values),
 * declared once more here rather than exported from a route file.
 */
export const CONCENTRATION_LEVEL_KEY: Record<string, TranslationKey> = {
  Low: "portfolio.concentrationLevel.low",
  Moderate: "portfolio.concentrationLevel.moderate",
  Elevated: "portfolio.concentrationLevel.elevated",
  High: "portfolio.concentrationLevel.high",
};

/**
 * One real, already-translated sentence for a reason -- dispatched by
 * `source`, never guessed from the bare code's own shape.
 */
export function portfolioDecisionReasonLabel(reason: PortfolioDecisionReasonView, t: (key: TranslationKey, params?: Record<string, string | number>) => string): string {
  const code = reason.reference.id;
  if (reason.source === "portfolio_fit") return t(FIT_RATING_KEY[code as FitRating]);
  if (reason.source === "portfolio_intelligence") {
    const key = KEY_FINDING_KEY[code];
    return key ? t(key) : code;
  }
  if (reason.source === "opportunity_cost") return t(ALTERNATIVE_KIND_KEY[code as keyof typeof ALTERNATIVE_KIND_KEY]);
  return t(RELIABILITY_LEVEL_KEY[code as keyof typeof RELIABILITY_LEVEL_KEY]);
}

/**
 * A comparison's own shared strength/weakness reference lists
 * (Deliverable 10) carry no `source` tag -- the same shape Sprint 6/7
 * Live Verification each found and fixed for their own comparisons.
 * Tries each of the four closed vocabularies in turn (never
 * ambiguous: the four are disjoint real enums), falling back to the
 * raw code only if genuinely unmatched.
 */
export function referenceLabel(reference: PortfolioDecisionReferenceView, t: (key: TranslationKey, params?: Record<string, string | number>) => string): string {
  const code = reference.id;
  if (code in FIT_RATING_KEY) return t(FIT_RATING_KEY[code as FitRating]);
  if (code in KEY_FINDING_KEY) return t(KEY_FINDING_KEY[code]!);
  if (code in ALTERNATIVE_KIND_KEY) return t(ALTERNATIVE_KIND_KEY[code as keyof typeof ALTERNATIVE_KIND_KEY]);
  if (code in RELIABILITY_LEVEL_KEY) return t(RELIABILITY_LEVEL_KEY[code as keyof typeof RELIABILITY_LEVEL_KEY]);
  return code;
}
