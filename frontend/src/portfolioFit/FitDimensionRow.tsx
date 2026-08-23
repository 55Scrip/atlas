import { Inline, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { FIT_DIMENSION_KEY } from "../status/statusTone";
import { FitBadge } from "./FitBadge";
import type { FitDimensionView } from "./portfolioFitApi";

/**
 * One dimension's own name + badge + reasoning, extracted from
 * `PortfolioFitSection.tsx` (Product Sprint 4) so the Discovery
 * Candidate Card (Product Sprint 5, Deliverable 4) renders each
 * dimension identically rather than a second, parallel row layout.
 */
export function FitDimensionRow({ dimension }: { dimension: FitDimensionView }) {
  const { t } = useTranslation();
  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center">
        <Text as="span" color="secondary">
          {t(FIT_DIMENSION_KEY[dimension.kind])}
        </Text>
        <FitBadge rating={dimension.rating} />
      </Inline>
      {dimension.unavailableReason !== null ? (
        <Text color="tertiary" as="p">
          {dimension.unavailableReason}
        </Text>
      ) : (
        dimension.reasoning.map((line, index) => (
          <Text key={index} color="tertiary" as="p">
            {line}
          </Text>
        ))
      )}
    </Stack>
  );
}
