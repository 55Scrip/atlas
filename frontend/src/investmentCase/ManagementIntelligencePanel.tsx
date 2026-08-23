import { Inline, Label, Stack, StatusBadge, StatusText, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "./ExpandableDetail";
import { FilingContentEmptyNote } from "./FilingContentEmptyNote";
import {
  EXECUTIVE_COMPENSATION_RELEVANT_FORM_TYPES,
  filingContentStatus,
  GOVERNANCE_RELEVANT_FORM_TYPES,
  OWNERSHIP_RELEVANT_FORM_TYPES,
} from "./filingContentStatus";
import { humanizeEnumValue } from "./humanizeEnumValue";
import type {
  ExecutiveChangeIntelligenceView,
  ExecutiveCompensationIntelligenceView,
  ExecutiveTrackRecordIntelligenceView,
  GovernanceIntelligenceView,
  InsiderAlignmentIntelligenceView,
  OwnershipIntelligenceView,
  RegulatoryFilingView,
} from "./managementIntelligenceApi";

const ROLE_CATEGORY_KEY: Record<string, TranslationKey> = {
  ceo: "managementIntelligence.role.ceo",
  cfo: "managementIntelligence.role.cfo",
  coo: "managementIntelligence.role.coo",
  chair: "managementIntelligence.role.chair",
  executive_chair: "managementIntelligence.role.executiveChair",
  president: "managementIntelligence.role.president",
  cto: "managementIntelligence.role.cto",
  cio: "managementIntelligence.role.cio",
  general_counsel: "managementIntelligence.role.generalCounsel",
  board_director: "managementIntelligence.role.boardDirector",
  other_executive: "managementIntelligence.role.otherExecutive",
};

const LEADERSHIP_EVENT_KEY: Record<string, TranslationKey> = {
  appointment: "managementIntelligence.event.appointment",
  departure: "managementIntelligence.event.departure",
  resignation: "managementIntelligence.event.resignation",
  retirement: "managementIntelligence.event.retirement",
  termination: "managementIntelligence.event.termination",
  promotion: "managementIntelligence.event.promotion",
  interim_appointment: "managementIntelligence.event.interimAppointment",
  permanent_appointment: "managementIntelligence.event.permanentAppointment",
  board_appointment: "managementIntelligence.event.boardAppointment",
  board_departure: "managementIntelligence.event.boardDeparture",
  role_change: "managementIntelligence.event.roleChange",
};

const TREND_KEY: Record<string, TranslationKey> = {
  increasing: "managementIntelligence.trend.increasing",
  decreasing: "managementIntelligence.trend.decreasing",
  stable: "managementIntelligence.trend.stable",
  insufficient_history: "managementIntelligence.trend.insufficientHistory",
};

const TREND_TONE: Record<string, "positive" | "caution" | "neutral"> = {
  increasing: "positive",
  decreasing: "caution",
  stable: "neutral",
  insufficient_history: "neutral",
};

const ALIGNMENT_OBSERVATION_KEY: Record<string, TranslationKey> = {
  executive_owns_stock: "managementIntelligence.alignmentObservation.ownsStock",
  executive_has_no_disclosed_ownership: "managementIntelligence.alignmentObservation.noDisclosedOwnership",
  executive_has_equity_awards: "managementIntelligence.alignmentObservation.hasEquityAwards",
  equity_compensation_disclosed: "managementIntelligence.alignmentObservation.equityCompensationDisclosed",
  cash_only_compensation_disclosed: "managementIntelligence.alignmentObservation.cashOnlyCompensationDisclosed",
  ownership_increasing: "managementIntelligence.alignmentObservation.ownershipIncreasing",
  ownership_decreasing: "managementIntelligence.alignmentObservation.ownershipDecreasing",
  ownership_stable: "managementIntelligence.alignmentObservation.ownershipStable",
};

function translateOrHumanize(map: Record<string, TranslationKey>, value: string, t: Translate): string {
  const key = map[value];
  return key ? t(key) : humanizeEnumValue(value);
}

/**
 * Product Utilization Sprint 1 (Investment Case Experience Activation).
 * Surfaces six already-computed, already-tested capabilities that had
 * no Investment Case presence at all before this sprint (Capability
 * Expansion Sprints 10/11/15/16/19/20/21) -- see this sprint's own
 * Final Report for the full activation matrix. No new computation: every
 * value below is read directly from the existing API response.
 *
 * Progressive disclosure (Phase 4): each sub-section leads with a
 * summary line, then an `ExpandableDetail` for the full, per-record
 * evidence -- the same "summary, then full evidence" shape
 * `KnowledgeCoveragePanel`/`CompanyHealthAssessmentSection` already use.
 *
 * Empty states (Phase 7): Governance/Ownership/Executive Compensation/
 * Insider Alignment are all real, but honestly empty in this build --
 * no production path yet reads filing *content* (Integration Sprint 1's
 * own documented, disclosed limitation). `FilingContentEmptyNote`
 * distinguishes "Atlas knows this filing exists but hasn't read it"
 * from "Atlas doesn't know of a relevant filing yet" -- never one
 * generic "no data" message for two different real states. Executives/
 * Leadership Changes is a *different* capability (earnings-call
 * derived, already active) with its own, simpler empty reason.
 */
export function ManagementIntelligencePanel({
  regulatoryFilings,
  executiveChange,
  trackRecord,
  governance,
  ownership,
  executiveCompensation,
  insiderAlignment,
  t,
}: {
  regulatoryFilings: RegulatoryFilingView[];
  executiveChange: ExecutiveChangeIntelligenceView;
  trackRecord: ExecutiveTrackRecordIntelligenceView;
  governance: GovernanceIntelligenceView;
  ownership: OwnershipIntelligenceView;
  executiveCompensation: ExecutiveCompensationIntelligenceView;
  insiderAlignment: InsiderAlignmentIntelligenceView;
  t: Translate;
}) {
  const tenureByName = new Map(trackRecord.tenures.map((tenure) => [tenure.executive.name, tenure]));
  const alignmentStatus = filingContentStatus(
    regulatoryFilings, [...OWNERSHIP_RELEVANT_FORM_TYPES, ...EXECUTIVE_COMPENSATION_RELEVANT_FORM_TYPES],
    insiderAlignment.filingsConsidered,
  );
  const governanceStatus = filingContentStatus(regulatoryFilings, GOVERNANCE_RELEVANT_FORM_TYPES, governance.filingsConsidered);
  const ownershipStatus = filingContentStatus(regulatoryFilings, OWNERSHIP_RELEVANT_FORM_TYPES, ownership.filingsConsidered);
  const compensationStatus = filingContentStatus(
    regulatoryFilings, EXECUTIVE_COMPENSATION_RELEVANT_FORM_TYPES, executiveCompensation.filingsConsidered,
  );

  return (
    <Stack gap="intra-section">
      <Label>{t("managementIntelligence.panel.heading")}</Label>

      {/* Executive Change / Track Record -- earnings-call derived, a
          different evidence source from the five sections below it. */}
      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("managementIntelligence.executives.heading")}
        </Text>
        {executiveChange.executives.length === 0 ? (
          <StatusText label={t("managementIntelligence.executives.empty")} tone="neutral" />
        ) : (
          <>
            <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
              {executiveChange.executives.map((executive) => {
                const tenure = tenureByName.get(executive.name);
                return (
                  <li key={executive.name}>
                    <Inline gap="metadata" align="center">
                      <Text as="span" style={{ fontWeight: 600 }}>{executive.name}</Text>
                      <Text as="span" color="secondary">{translateOrHumanize(ROLE_CATEGORY_KEY, executive.roleCategory, t)}</Text>
                      {executive.isInterim && (
                        <StatusBadge label={t("managementIntelligence.executives.interim")} tone="caution" />
                      )}
                      {tenure && tenure.findings.some((f) => f.kind === "leadership_transition_during_tenure") && (
                        <StatusBadge label={t("managementIntelligence.executives.transitionObserved")} tone="neutral" />
                      )}
                    </Inline>
                  </li>
                );
              })}
            </ul>
            {executiveChange.leadershipChanges.length > 0 && (
              <ExpandableDetail
                summaryLabel={t(
                  executiveChange.leadershipChanges.length === 1
                    ? "managementIntelligence.executives.changesExpandLabelOne"
                    : "managementIntelligence.executives.changesExpandLabelOther",
                  { count: executiveChange.leadershipChanges.length },
                )}
              >
                <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
                  {executiveChange.leadershipChanges.map((event, index) => (
                    <li key={`${event.executiveName}-${index}`}>
                      <Text as="span">
                        {event.executiveName} — {translateOrHumanize(LEADERSHIP_EVENT_KEY, event.eventType, t)}
                      </Text>
                    </li>
                  ))}
                </ul>
              </ExpandableDetail>
            )}
          </>
        )}
      </Stack>

      {/* Insider Alignment -- the headline synthesis (Capability
          Expansion Sprint 21): links Ownership + Executive Compensation
          to each named executive. Leads the remaining sub-sections since
          it is the most decision-relevant single view; Ownership and
          Executive Compensation below expose the same underlying
          evidence at full detail. */}
      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("managementIntelligence.alignment.heading")}
        </Text>
        {insiderAlignment.profiles.length === 0 ? (
          <FilingContentEmptyNote status={alignmentStatus} t={t} />
        ) : (
          <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
            {insiderAlignment.profiles.map((profile) => (
              <li key={profile.executive.name}>
                <Stack gap="metadata">
                  <Inline gap="metadata" align="center">
                    <Text as="span" style={{ fontWeight: 600 }}>{profile.executive.name}</Text>
                    {profile.ownership.holdingCount > 0 && (
                      <StatusBadge
                        label={translateOrHumanize(TREND_KEY, profile.ownership.trend, t)}
                        tone={TREND_TONE[profile.ownership.trend] ?? "neutral"}
                      />
                    )}
                  </Inline>
                  {profile.observations.length > 0 && (
                    <Text as="span" color="secondary">
                      {profile.observations.map((o) => translateOrHumanize(ALIGNMENT_OBSERVATION_KEY, o.kind, t)).join(" · ")}
                    </Text>
                  )}
                </Stack>
              </li>
            ))}
          </ul>
        )}
      </Stack>

      {/* Governance */}
      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("managementIntelligence.governance.heading")}
        </Text>
        {governance.boardComposition.directors.length === 0 && governance.committees.length === 0 ? (
          <FilingContentEmptyNote status={governanceStatus} t={t} />
        ) : (
          <>
            <Inline gap="metadata" align="center">
              <Text as="span">
                {t(
                  governance.boardComposition.directors.length === 1
                    ? "managementIntelligence.governance.directorCountOne"
                    : "managementIntelligence.governance.directorCountOther",
                  { count: governance.boardComposition.directors.length },
                )}
              </Text>
              {governance.boardComposition.chairDisclosed && (
                <StatusBadge label={t("managementIntelligence.governance.chairDisclosed")} tone="neutral" />
              )}
              {governance.votingStructure.dualClassDisclosed && (
                <StatusBadge label={t("managementIntelligence.governance.dualClass")} tone="caution" />
              )}
            </Inline>
            {governance.committees.length > 0 && (
              <ExpandableDetail
                summaryLabel={t(
                  governance.committees.length === 1
                    ? "managementIntelligence.governance.committeesExpandLabelOne"
                    : "managementIntelligence.governance.committeesExpandLabelOther",
                  { count: governance.committees.length },
                )}
              >
                <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
                  {governance.committees.map((committee, index) => (
                    <li key={`${committee.kind}-${index}`}>
                      <Text as="span">
                        {humanizeEnumValue(committee.kind)} ({committee.members.length})
                      </Text>
                    </li>
                  ))}
                </ul>
              </ExpandableDetail>
            )}
          </>
        )}
      </Stack>

      {/* Ownership */}
      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("managementIntelligence.ownership.heading")}
        </Text>
        {ownership.disclosures.length === 0 ? (
          <FilingContentEmptyNote status={ownershipStatus} t={t} />
        ) : (
          <ExpandableDetail
            summaryLabel={t(
              ownership.disclosures.length === 1
                ? "managementIntelligence.ownership.disclosuresExpandLabelOne"
                : "managementIntelligence.ownership.disclosuresExpandLabelOther",
              { count: ownership.disclosures.length },
            )}
          >
            <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
              {ownership.disclosures
                .filter((d) => d.ownerName !== null)
                .map((disclosure, index) => (
                  <li key={`${disclosure.ownerName}-${index}`}>
                    <Text as="span">
                      {disclosure.ownerName}
                      {disclosure.disclosedPercentage ? ` — ${disclosure.disclosedPercentage}` : ""}
                      {disclosure.disclosedShareCount ? ` (${disclosure.disclosedShareCount})` : ""}
                    </Text>
                  </li>
                ))}
            </ul>
          </ExpandableDetail>
        )}
      </Stack>

      {/* Executive Compensation */}
      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("managementIntelligence.compensation.heading")}
        </Text>
        {executiveCompensation.records.length === 0 ? (
          <FilingContentEmptyNote status={compensationStatus} t={t} />
        ) : (
          <ExpandableDetail
            summaryLabel={t(
              executiveCompensation.records.length === 1
                ? "managementIntelligence.compensation.recordsExpandLabelOne"
                : "managementIntelligence.compensation.recordsExpandLabelOther",
              { count: executiveCompensation.records.length },
            )}
          >
            <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
              {executiveCompensation.records.map((record, index) => (
                <li key={`${record.executiveName}-${record.reportingYear}-${index}`}>
                  <Text as="span">
                    {record.executiveName}
                    {record.reportingYear ? ` (${record.reportingYear})` : ""}
                    {record.total ? ` — ${t("managementIntelligence.compensation.total")}: ${record.total}` : ""}
                  </Text>
                </li>
              ))}
            </ul>
          </ExpandableDetail>
        )}
      </Stack>
    </Stack>
  );
}
