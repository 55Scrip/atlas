import { Inline, Label, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { ExpandableDetail } from "./ExpandableDetail";
import { FilingContentEmptyNote } from "./FilingContentEmptyNote";
import {
  filingContentStatus,
  LEGAL_PROCEEDINGS_RELEVANT_FORM_TYPES,
  RISK_FACTOR_RELEVANT_FORM_TYPES,
} from "./filingContentStatus";
import { humanizeEnumValue } from "./humanizeEnumValue";
import type { RegulatoryFilingView } from "./managementIntelligenceApi";
import type { LegalProceedingsIntelligenceView, RiskFactorIntelligenceView } from "./regulatoryIntelligenceApi";

/**
 * Product Utilization Sprint 1 (Investment Case Experience Activation).
 * Surfaces Risk Factor and Legal Proceedings Intelligence (Capability
 * Expansion Sprints 17/18) plus the filing history Atlas already
 * ingests -- all three had no Investment Case presence before this
 * sprint. Category labels (risk/proceeding kind) are real, closed,
 * disclosed taxonomy -- rendered via `humanizeEnumValue`, the same
 * documented choice `ManagementIntelligencePanel` makes for its own
 * numerous taxonomy enums, not translated individually.
 */
export function RegulatoryIntelligencePanel({
  regulatoryFilings,
  riskFactor,
  legalProceedings,
  t,
}: {
  regulatoryFilings: RegulatoryFilingView[];
  riskFactor: RiskFactorIntelligenceView;
  legalProceedings: LegalProceedingsIntelligenceView;
  t: Translate;
}) {
  const riskStatus = filingContentStatus(regulatoryFilings, RISK_FACTOR_RELEVANT_FORM_TYPES, riskFactor.filingsConsidered);
  const legalStatus = filingContentStatus(
    regulatoryFilings, LEGAL_PROCEEDINGS_RELEVANT_FORM_TYPES, legalProceedings.filingsConsidered,
  );

  return (
    <Stack gap="intra-section">
      <Label>{t("regulatoryIntelligence.panel.heading")}</Label>

      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("regulatoryIntelligence.filings.heading")}
        </Text>
        {regulatoryFilings.length === 0 ? (
          <Text color="tertiary">{t("regulatoryIntelligence.filings.empty")}</Text>
        ) : (
          <ExpandableDetail
            summaryLabel={t(
              regulatoryFilings.length === 1
                ? "regulatoryIntelligence.filings.expandLabelOne"
                : "regulatoryIntelligence.filings.expandLabelOther",
              { count: regulatoryFilings.length },
            )}
          >
            <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
              {regulatoryFilings.map((filing) => (
                <li key={filing.accessionNumber}>
                  <Text as="span">
                    {filing.formType} — {new Date(filing.filedAt).toLocaleDateString()}
                  </Text>
                </li>
              ))}
            </ul>
          </ExpandableDetail>
        )}
      </Stack>

      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("regulatoryIntelligence.riskFactors.heading")}
        </Text>
        {riskFactor.categories.length === 0 ? (
          <FilingContentEmptyNote status={riskStatus} t={t} />
        ) : (
          <>
            <Inline gap="metadata" style={{ flexWrap: "wrap" }}>
              {riskFactor.categories.map((category) => (
                <StatusBadge key={category.kind} label={humanizeEnumValue(category.kind)} tone="neutral" />
              ))}
            </Inline>
            <ExpandableDetail
              summaryLabel={t(
                riskFactor.categories.reduce((sum, c) => sum + c.disclosures.length, 0) === 1
                  ? "regulatoryIntelligence.riskFactors.expandLabelOne"
                  : "regulatoryIntelligence.riskFactors.expandLabelOther",
                { count: riskFactor.categories.reduce((sum, c) => sum + c.disclosures.length, 0) },
              )}
            >
              <Stack gap="metadata">
                {riskFactor.categories.map((category) => (
                  <Stack key={category.kind} gap="metadata">
                    <Text as="span" style={{ fontWeight: 600 }}>{humanizeEnumValue(category.kind)}</Text>
                    <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
                      {category.disclosures.map((disclosure, index) => (
                        <li key={index}>
                          <Text as="span" color="secondary">{disclosure.text}</Text>
                        </li>
                      ))}
                    </ul>
                  </Stack>
                ))}
              </Stack>
            </ExpandableDetail>
          </>
        )}
      </Stack>

      <Stack gap="metadata">
        <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
          {t("regulatoryIntelligence.legalProceedings.heading")}
        </Text>
        {legalProceedings.categories.length === 0 ? (
          <FilingContentEmptyNote status={legalStatus} t={t} />
        ) : (
          <>
            <Inline gap="metadata" style={{ flexWrap: "wrap" }}>
              {legalProceedings.categories.map((category) => (
                <StatusBadge key={category.kind} label={humanizeEnumValue(category.kind)} tone="caution" />
              ))}
            </Inline>
            <ExpandableDetail
              summaryLabel={t(
                legalProceedings.categories.reduce((sum, c) => sum + c.disclosures.length, 0) === 1
                  ? "regulatoryIntelligence.legalProceedings.expandLabelOne"
                  : "regulatoryIntelligence.legalProceedings.expandLabelOther",
                { count: legalProceedings.categories.reduce((sum, c) => sum + c.disclosures.length, 0) },
              )}
            >
              <Stack gap="metadata">
                {legalProceedings.categories.map((category) => (
                  <Stack key={category.kind} gap="metadata">
                    <Text as="span" style={{ fontWeight: 600 }}>{humanizeEnumValue(category.kind)}</Text>
                    <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
                      {category.disclosures.map((disclosure, index) => (
                        <li key={index}>
                          <Text as="span" color="secondary">{disclosure.text}</Text>
                        </li>
                      ))}
                    </ul>
                  </Stack>
                ))}
              </Stack>
            </ExpandableDetail>
          </>
        )}
      </Stack>
    </Stack>
  );
}
