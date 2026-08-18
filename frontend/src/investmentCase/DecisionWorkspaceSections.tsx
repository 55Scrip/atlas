import { Divider, Label, Stack, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import type { DecisionWorkspaceSection } from "./deriveDecisionWorkspace";

/**
 * Decision Workspace v1 -- renders `UX-009`'s own fixed 1-13 section
 * sequence (Current Conclusion through Review Plan; the Final Decision
 * Card and Record Decision action, Sections 12-13, remain the existing,
 * unmodified success/submit UI immediately below this component -- see
 * `InvestmentCasePage.tsx`'s own comment at the call site).
 *
 * Every `UNAVAILABLE_WITH_CURRENT_MODEL` item renders through the same
 * calm, secondary-color, no-fabrication treatment this codebase already
 * established for `ValuationSupportCard`'s own gap copy -- never hidden,
 * never invented. A section whose every item is unavailable
 * (`fullyUnavailable`) shows one line, not a wall of repeated caveats.
 */
export function DecisionWorkspaceSections({
  sections,
  t,
}: {
  sections: DecisionWorkspaceSection[];
  t: Translate;
}) {
  return (
    <Stack gap="inter-section">
      {sections.map((section) => (
        <Stack gap="metadata" key={section.id}>
          <Label>{t(section.titleKey)}</Label>
          {section.fullyUnavailable ? (
            <Text as="p" color="secondary">
              {t("investmentCase.decisionWorkspace.notAvailableYet")}
            </Text>
          ) : (
            <Stack gap="metadata">
              {section.items.map((entry, index) => (
                <Text
                  as="p"
                  key={`${section.id}-${index}`}
                  color={entry.classification === "UNAVAILABLE_WITH_CURRENT_MODEL" ? "secondary" : "primary"}
                >
                  {entry.text}
                </Text>
              ))}
            </Stack>
          )}
          <Divider tone="hairline" />
        </Stack>
      ))}
    </Stack>
  );
}
