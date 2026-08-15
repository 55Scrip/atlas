import { Label, Stack, StatusBadge, Text } from "../foundation";
import type { Translate } from "../changeIntelligence/describeChange";
import {
  VALUATION_SUPPORT_GAP_COPY_KEY,
  VALUATION_SUPPORT_LABEL_KEY,
  VALUATION_SUPPORT_TONE,
  type ValuationSupportGapKind,
  type ValuationSupportStatus,
} from "../status/statusTone";

/**
 * Beta Recommendation Experience implementation sprint (`UX-022` §9): the
 * Figma's Valuation Support card, promoted from a Key-Metrics-row badge
 * (still shown there too, unchanged) to its own standalone card with a
 * one-line real explanation -- the caller (`InvestmentCasePage.tsx`)
 * decides whether Valuation Support is load-bearing for the Direction
 * shown and renders this only then, per `UX-022`'s own placement rule;
 * this component itself makes no such judgment. Label and gap copy are
 * both the exact already-approved, safe presentation-layer text (never
 * "supported"/`.reasoning` verbatim, never a fair-value number) -- see
 * `VALUATION_SUPPORT_LABEL_KEY`/`VALUATION_SUPPORT_GAP_COPY_KEY`'s own
 * docstrings.
 */
export function ValuationSupportCard({
  status,
  gap,
  t,
}: {
  status: ValuationSupportStatus;
  gap: ValuationSupportGapKind | null;
  t: Translate;
}) {
  return (
    <Stack gap="metadata">
      <Label>{t("investmentCase.valuationSupport.cardHeading")}</Label>
      <StatusBadge
        label={t(VALUATION_SUPPORT_LABEL_KEY[status])}
        tone={VALUATION_SUPPORT_TONE[status]}
        style={{ whiteSpace: "normal" }}
      />
      {gap && (
        <Text as="p" color="secondary">
          {t(VALUATION_SUPPORT_GAP_COPY_KEY[gap])}
        </Text>
      )}
    </Stack>
  );
}
