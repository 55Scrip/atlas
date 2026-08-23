/**
 * Product Utilization Sprint 1 (Investment Case Experience Activation).
 * Field-for-field mirrors of `RiskFactorIntelligenceView`/
 * `LegalProceedingsIntelligenceView` (Capability Expansion Sprints
 * 17/18) -- see `managementIntelligenceApi.ts`'s own top comment for
 * the shared narrowing convention this file also follows.
 */

export interface RiskDisclosureView {
  categories: string[];
  text: string;
  source: string;
  accessionNumber: string;
  filedAt: string;
}

export interface RiskCategorySummaryView {
  kind: string;
  disclosures: RiskDisclosureView[];
}

export interface RiskChangeObservationView {
  kind: string;
  category: string;
}

export interface RiskFactorIntelligenceView {
  categories: RiskCategorySummaryView[];
  changes: RiskChangeObservationView[];
  filingsConsidered: string[];
}

export interface LegalProceedingDisclosureView {
  categories: string[];
  text: string;
  source: string;
  accessionNumber: string;
  filedAt: string;
}

export interface ProceedingCategorySummaryView {
  kind: string;
  disclosures: LegalProceedingDisclosureView[];
}

export interface LegalChangeObservationView {
  kind: string;
  category: string;
}

export interface LegalProceedingsIntelligenceView {
  categories: ProceedingCategorySummaryView[];
  changes: LegalChangeObservationView[];
  filingsConsidered: string[];
}
