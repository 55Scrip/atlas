import type { FitDimensionView } from "./portfolioFitApi";

/**
 * The one grouping rule "favorable / unfavorable / other" -- extracted
 * from `PortfolioFitSection.tsx` (Product Sprint 4) so Product Sprint 5's
 * `DiscoveryCandidateCard` can answer "strongest positives"/"strongest
 * limitations" (Deliverable 4) from the exact same rule, not a second
 * one. Pure and total: every dimension in `dimensions` appears in
 * exactly one of the three returned groups.
 */
export interface GroupedFitDimensions {
  favorable: FitDimensionView[];
  unfavorable: FitDimensionView[];
  other: FitDimensionView[];
}

export function groupFitDimensions(dimensions: FitDimensionView[]): GroupedFitDimensions {
  return {
    favorable: dimensions.filter((d) => d.rating === "excellent" || d.rating === "good"),
    unfavorable: dimensions.filter((d) => d.rating === "weak" || d.rating === "poor"),
    other: dimensions.filter((d) => d.rating === "neutral" || d.rating === "unavailable"),
  };
}
