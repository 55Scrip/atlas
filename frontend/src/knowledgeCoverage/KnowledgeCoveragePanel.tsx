import { Inline, Label, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import { DIMENSION_COVERAGE_LEVEL_KEY, DIMENSION_COVERAGE_TONE, type KnowledgeDomainGroup } from "../status/statusTone";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { knowledgeDomainGroupLabel, knowledgeDomainLabel, missingKnowledgeReasonSentence } from "./describeKnowledgeCoverage";
import type { InvestmentCaseKnowledgeCoverageView, KnowledgeDomainCoverageView } from "./knowledgeCoverageApi";

const GROUP_ORDER: readonly KnowledgeDomainGroup[] = [
  "company_overview",
  "financials",
  "governance_ownership",
  "valuation",
  "events_filings",
  "macro_external_exposure",
  "risk_opportunity",
  "case_memory",
];

/**
 * Automatic Investment Case Builder Foundation. A different, lower-level
 * question than `CoveragePanel` above it on the page: not "has Atlas
 * concluded something" (evaluator coverage) but "does Atlas have the
 * raw knowledge to conclude anything at all." Mirrors `CoveragePanel`'s
 * own visual/architectural language exactly -- status badges (never a
 * gradient or bare number standing alone), grouped lists, a collapsed
 * "N not applicable" note for domains this build of Atlas doesn't yet
 * wire a provider for. The one percentage figure this panel shows is
 * always rendered directly beside the real counts it was derived from,
 * never alone -- see `InvestmentCaseKnowledgeCoverageView.coveragePercent`'s
 * own docstring.
 */
export function KnowledgeCoveragePanel({ coverage, t }: { coverage: InvestmentCaseKnowledgeCoverageView; t: Translate }) {
  const notApplicable = coverage.domains.filter((d) => d.level === "not_applicable");
  const byGroup = new Map<KnowledgeDomainGroup, KnowledgeDomainCoverageView[]>();
  for (const domain of coverage.domains) {
    if (domain.level === "not_applicable") continue;
    const list = byGroup.get(domain.group) ?? [];
    list.push(domain);
    byGroup.set(domain.group, list);
  }

  return (
    <Stack gap="intra-section">
      <Inline gap="row" align="center" style={{ justifyContent: "space-between" }}>
        <Label>{t("knowledgeCoverage.panel.heading")}</Label>
      </Inline>

      <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
        {t("knowledgeCoverage.panel.summary", {
          available: coverage.availableCount,
          applicable: coverage.applicableCount,
          percent: coverage.coveragePercent,
        })}
      </Text>

      {GROUP_ORDER.map((group) => {
        const domains = byGroup.get(group);
        if (!domains || domains.length === 0) return null;
        return (
          <Stack key={group} gap="metadata">
            <Text as="p" color="secondary" style={{ fontWeight: 600 }}>
              {knowledgeDomainGroupLabel(group, t)}
            </Text>
            <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
              {domains.map((d) => (
                <li key={d.domain}>
                  <Stack gap="metadata">
                    <Inline gap="metadata" align="center">
                      <Text as="span">{knowledgeDomainLabel(d.domain, t)}</Text>
                      <StatusBadge label={t(DIMENSION_COVERAGE_LEVEL_KEY[d.level])} tone={DIMENSION_COVERAGE_TONE[d.level]} />
                    </Inline>
                    {d.missingReasons.length > 0 && (
                      <Text as="span" color="tertiary">
                        {d.missingReasons.map((r) => missingKnowledgeReasonSentence(r, t)).join(" ")}
                      </Text>
                    )}
                  </Stack>
                </li>
              ))}
            </ul>
          </Stack>
        );
      })}

      {notApplicable.length > 0 && (
        <ExpandableDetail
          summaryLabel={t(
            notApplicable.length === 1
              ? "knowledgeCoverage.panel.notApplicableExpandLabelOne"
              : "knowledgeCoverage.panel.notApplicableExpandLabelOther",
            { count: notApplicable.length },
          )}
        >
          <ul style={{ margin: 0, paddingInlineStart: "1.25rem" }}>
            {notApplicable.map((d) => (
              <li key={d.domain}>
                <Text as="span" color="tertiary">
                  {knowledgeDomainLabel(d.domain, t)}
                </Text>
              </li>
            ))}
          </ul>
        </ExpandableDetail>
      )}
    </Stack>
  );
}
