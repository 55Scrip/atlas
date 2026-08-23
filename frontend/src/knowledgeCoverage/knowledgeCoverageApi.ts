import type {
  DimensionCoverageLevel,
  EvidenceDominance,
  EvidenceFreshness,
  KnowledgeDomain,
  KnowledgeDomainGroup,
  MissingKnowledgeReason,
} from "../status/statusTone";

/**
 * Automatic Investment Case Builder Foundation. Field-for-field mirror
 * of `atlas.alpha.investment_case.api.schemas.KnowledgeDomainCoverageView`/
 * `InvestmentCaseKnowledgeCoverageView` (camelCase via the shared Core
 * `CamelModel`).
 */
export interface KnowledgeDomainCoverageView {
  domain: KnowledgeDomain;
  group: KnowledgeDomainGroup;
  level: DimensionCoverageLevel;
  freshness: EvidenceFreshness;
  dominance: EvidenceDominance;
  missingReasons: MissingKnowledgeReason[];
}

export interface InvestmentCaseKnowledgeCoverageView {
  domains: KnowledgeDomainCoverageView[];
  availableCount: number;
  partiallyAvailableCount: number;
  applicableCount: number;
  totalDomainCount: number;
  notApplicableCount: number;
  missingDomains: KnowledgeDomain[];
  notApplicableDomains: KnowledgeDomain[];
  /** `round(availableCount / applicableCount * 100)`, computed once on
   * the backend at the API serialization boundary, always shipped
   * alongside `availableCount`/`applicableCount` -- never recompute a
   * second formula here. */
  coveragePercent: number;
}
