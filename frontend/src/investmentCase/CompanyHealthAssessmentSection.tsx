import { Inline, Label, Stack, StatusBadge, Text } from "../foundation";
import type { StatusTone } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { ExpandableDetail } from "./ExpandableDetail";
import { capFacts, isReadableFact } from "./AtlasReasoningSection";

/**
 * Company Health Assessment (Figma-fidelity rebuild): five expandable
 * cards -- Business Quality, Financial Strength, Management &
 * Governance, Capital Allocation, Competitive Position -- each showing
 * a real status and a short summary by default, with real supporting/
 * contradicting/missing evidence one click away (`supportingEvidence`/
 * `contradictingEvidence`/`missingEvidence`, already on the
 * `BusinessFindingView`/`RiskFindingView` shapes this page already
 * fetches -- nothing new computed, only newly surfaced). Deliberately
 * deeper and more evidence-grounded than `AtlasReasoningSection`'s
 * terse cards above, even where the two draw on the same underlying
 * finding -- see that section's own file header for the reasoning.
 */

export interface CompanyHealthCardInput {
  labelKey: "businessQuality" | "financialStrength" | "managementGovernance" | "capitalAllocation" | "competitivePosition";
  statusLabel: string;
  tone: StatusTone;
  summary: string;
  supportingEvidence: string[];
  contradictingEvidence: string[];
  missingEvidence: string[];
}

function EvidenceList({ heading, items, emptyLabel }: { heading: string; items: string[]; emptyLabel: string }) {
  return (
    <Stack gap="metadata">
      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
        {heading}
      </Text>
      {items.length === 0 ? (
        <Text color="tertiary">{emptyLabel}</Text>
      ) : (
        <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
          {items.map((item, index) => (
            <li key={index}>
              <Text as="span" color="secondary">
                {item}
              </Text>
            </li>
          ))}
        </ul>
      )}
    </Stack>
  );
}

function CompanyHealthCard({ card, t }: { card: CompanyHealthCardInput; t: Translate }) {
  return (
    <Stack gap="metadata" style={{ flex: "1 1 320px", minWidth: 0 }}>
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Text as="p" style={{ fontWeight: 600 }}>
          {t(`investmentCase.companyHealth.${card.labelKey}Label` as const)}
        </Text>
        <StatusBadge label={card.statusLabel} tone={card.tone} />
      </Inline>
      <Text as="p" color="secondary">
        {card.summary}
      </Text>
      <ExpandableDetail summaryLabel={t("investmentCase.companyHealth.expandLabel")}>
        <Stack gap="intra-section">
          {/* Product Sprint 13 (Company Intelligence Excellence):
              live-testing found `supportingEvidence`/`contradictingEvidence`
              sometimes hold raw, unresolved evidence-reference ids
              rather than prose -- see `isReadableFact`'s own doc
              comment. Filtered here, at the one place this page renders
              them as "the evidence" a click reveals, so a raw id is
              never shown as if it were a real cited fact.
              Product Sprint 14: now that resolution genuinely works,
              a Growth/Valuation finding evaluated across a company's
              full history can carry 20-30+ real facts -- `capFacts`
              keeps this readable, matching the same cap
              `AtlasReasoningSection`'s own terse cards use. */}
          <EvidenceList
            heading={t("investmentCase.companyHealth.supportingHeading")}
            items={capFacts(card.supportingEvidence.filter(isReadableFact))}
            emptyLabel={t("investmentCase.companyHealth.noneFound")}
          />
          <EvidenceList
            heading={t("investmentCase.companyHealth.contradictingHeading")}
            items={capFacts(card.contradictingEvidence.filter(isReadableFact))}
            emptyLabel={t("investmentCase.companyHealth.noneFound")}
          />
          <EvidenceList
            heading={t("investmentCase.companyHealth.missingHeading")}
            items={card.missingEvidence}
            emptyLabel={t("investmentCase.companyHealth.noneFound")}
          />
        </Stack>
      </ExpandableDetail>
    </Stack>
  );
}

export function CompanyHealthAssessmentSection({ cards, t }: { cards: CompanyHealthCardInput[]; t: Translate }) {
  return (
    <Stack gap="intra-section">
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Label>{t("investmentCase.companyHealth.heading")}</Label>
      </Inline>
      <Inline gap="inter-section" wrap align="start">
        {cards.map((card) => (
          <CompanyHealthCard key={card.labelKey} card={card} t={t} />
        ))}
      </Inline>
    </Stack>
  );
}
