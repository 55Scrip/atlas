/**
 * Product Utilization Sprint 1 (Investment Case Experience Activation).
 * Field-for-field mirrors of the backend Views these already-computed
 * capabilities serialize as (`atlas.alpha.investment_case.api.schemas`),
 * camelCase via the shared Core `CamelModel` -- the same convention
 * `knowledgeCoverageApi.ts` already established. No new backend field
 * is introduced here; every shape below already exists on
 * `InvestmentCaseAnalysisView` and was simply unreachable from the
 * frontend until this sprint.
 *
 * A few deeply-nested, currently-always-empty "framework, not dataset"
 * backend sub-objects are deliberately narrowed here rather than
 * mirrored field-for-field (e.g. `GovernancePolicyView`'s own
 * `kind`/`description` are folded into a single `label` this file
 * never actually renders differently; `EquityIncentiveView`/
 * `CashIncentiveView`/`PerformanceIncentiveView` inside an incentive
 * program are represented only by their own `kind`, since no other
 * field is populated in this build) -- this keeps the type surface
 * proportional to what the UI actually shows today, without dropping
 * any field the UI needs.
 */

export interface RegulatoryFilingView {
  formType: string;
  filedAt: string;
  accessionNumber: string;
  filingUrl: string;
  periodOfReport: string | null;
}

// -- Executive Change / Track Record (Capability Expansion Sprints 10/11) --

export interface ExecutiveIdentityView {
  name: string;
  roleCategory: string;
  rawTitle: string | null;
  company: string | null;
  isInterim: boolean;
  firstObservedDate: string;
  lastObservedDate: string;
  sourceTranscripts: string[];
  statementCount: number;
}

export interface LeadershipChangeEventView {
  eventType: string;
  executiveName: string;
  roleCategory: string;
  priorRoleCategory: string | null;
  effectiveDate: string | null;
  announcementDate: string | null;
  observedDate: string;
  sourceTranscript: string;
  provenance: string;
}

export interface ExecutiveChangeIntelligenceView {
  executives: ExecutiveIdentityView[];
  leadershipChanges: LeadershipChangeEventView[];
}

export interface TrackRecordFindingView {
  kind: string;
  evidenceCount: number;
}

export interface ExecutiveTenureRecordView {
  executive: ExecutiveIdentityView;
  evidenceCompleteness: string;
  findings: TrackRecordFindingView[];
}

export interface ExecutiveTrackRecordIntelligenceView {
  tenures: ExecutiveTenureRecordView[];
}

// -- Governance Intelligence (Capability Expansion Sprint 15/16) ------------

export interface DirectorView {
  name: string;
  isChair: boolean;
  isLeadIndependentDirector: boolean;
  disclosedIndependence: boolean | null;
  committeeAssignments: string[];
  accessionNumber: string;
  filedAt: string;
}

export interface CommitteeView {
  kind: string;
  disclosedName: string;
  members: DirectorView[];
  chair: DirectorView | null;
}

export interface VotingStructureView {
  dualClassDisclosed: boolean;
  controlledCompanyDisclosed: boolean;
  shareClassCount: number;
}

export interface GovernanceIntelligenceView {
  boardComposition: {
    chairDisclosed: boolean;
    leadIndependentDirectorDisclosed: boolean;
    directors: DirectorView[];
  };
  committees: CommitteeView[];
  votingStructure: VotingStructureView;
  changeCount: number;
  observationCount: number;
  filingsConsidered: string[];
}

// -- Ownership Intelligence (Capability Expansion Sprint 19) ----------------

export interface OwnershipDisclosureView {
  ownerName: string | null;
  categories: string[];
  disclosedPercentage: string | null;
  disclosedShareCount: string | null;
  accessionNumber: string;
  filedAt: string;
}

export interface OwnershipChangeObservationView {
  kind: string;
  ownerName: string;
  filedAt: string;
}

export interface OwnershipIntelligenceView {
  disclosures: OwnershipDisclosureView[];
  changes: OwnershipChangeObservationView[];
  filingsConsidered: string[];
}

// -- Executive Compensation Intelligence (Capability Expansion Sprint 20) --

export interface ExecutiveCompensationRecordView {
  executiveName: string;
  disclosedRole: string | null;
  reportingYear: string | null;
  salary: string | null;
  bonus: string | null;
  stockAwards: string | null;
  optionAwards: string | null;
  total: string | null;
  currency: string | null;
  accessionNumber: string;
  filedAt: string;
}

export interface CompensationChangeObservationView {
  kind: string;
  executiveName: string;
  previousValue: string | null;
  currentValue: string | null;
}

export interface ExecutiveCompensationIntelligenceView {
  records: ExecutiveCompensationRecordView[];
  changes: CompensationChangeObservationView[];
  filingsConsidered: string[];
}

// -- Insider Alignment Intelligence (Capability Expansion Sprint 21) -------

export interface EquityCompensationExposureView {
  hasEquityAwards: boolean;
  equityIncentiveKinds: string[];
  hasCashCompensation: boolean;
  disclosedComponents: string[];
}

export interface AlignmentObservationView {
  kind: string;
  executiveName: string;
  accessionNumber: string | null;
  filedAt: string | null;
}

export interface ExecutiveAlignmentProfileView {
  executive: ExecutiveIdentityView;
  ownership: {
    holdingCount: number;
    trend: string;
  };
  equityCompensation: EquityCompensationExposureView;
  observations: AlignmentObservationView[];
}

export interface InsiderAlignmentIntelligenceView {
  profiles: ExecutiveAlignmentProfileView[];
  filingsConsidered: string[];
}
