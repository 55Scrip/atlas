import { Inline, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { PriorityBadge } from "./PriorityBadge";
import { AgendaItemRow, AgendaItemActions } from "./AgendaItemRow";
import { describeReasonLine } from "./describeReasonFact";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import type { TickerAgendaGroup } from "./groupAgendaByTicker";
import type { TickerStanceView } from "../stance/stanceApi";

const MAX_COMPACT_REASONS = 3;

/**
 * Daily Brief Compression -- one card per ticker (Deliverable 3's own
 * "one ticker = one card, never 15 independent cards" instruction).
 * The compact view shows only the group's own already-real fields:
 * highest priority among its items, a deduplicated reason list capped
 * at three lines, and one "Review →" action reusing the exact same
 * routing `AgendaItemRow` already uses. Nothing here is a new signal --
 * every full per-item detail (Stance, evidence/explanation
 * disclosures, every individual action) remains one click away via
 * `ExpandableDetail`, never deleted, only deferred.
 */
export function TickerAgendaCard({
  group,
  stanceByTicker,
  onOpenInvestmentCase,
  onOpenCandidate,
  onCompare,
  onOpenHolding,
  onGoToPortfolio,
}: {
  group: TickerAgendaGroup;
  stanceByTicker: Map<string, TickerStanceView["stance"]>;
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
  onOpenCandidate: (ticker: string) => void;
  onCompare: (ticker: string) => void;
  onOpenHolding: (ticker: string) => void;
  onGoToPortfolio: () => void;
}) {
  const { t } = useTranslation();
  // `group.items` is never empty by construction (`groupAgendaByTicker`
  // only ever creates a group from at least one real item).
  const primaryItem = group.items[0]!;
  const compactReasons = group.reasons.slice(0, MAX_COMPACT_REASONS);
  const hiddenReasonCount = group.reasons.length - compactReasons.length;

  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" align="center">
          <PriorityBadge priority={group.topPriority} />
          {group.ticker && (
            <Text as="span" style={{ fontWeight: 600 }}>
              {group.ticker}
            </Text>
          )}
          <Text color="tertiary" as="span">
            {t(group.items.length === 1 ? "dailyBriefAgenda.group.updateCountOne" : "dailyBriefAgenda.group.updateCountOther", {
              count: group.items.length,
            })}
          </Text>
        </Inline>
      </Inline>

      <Stack gap="row">
        {compactReasons.map((reason, index) => (
          <Text key={index} as="p" color="secondary">
            • {describeReasonLine(reason, group.reasonFacts[index] ?? null, t)}
          </Text>
        ))}
        {hiddenReasonCount > 0 && (
          <Text color="tertiary" as="p">
            {t(hiddenReasonCount === 1 ? "dailyBriefAgenda.group.moreReasonsOne" : "dailyBriefAgenda.group.moreReasonsOther", {
              count: hiddenReasonCount,
            })}
          </Text>
        )}
      </Stack>

      <Inline gap="row" wrap align="center">
        <AgendaItemActions
          item={primaryItem}
          onOpenInvestmentCase={onOpenInvestmentCase}
          onOpenCandidate={onOpenCandidate}
          onCompare={onCompare}
          onOpenHolding={onOpenHolding}
          onGoToPortfolio={onGoToPortfolio}
        />
      </Inline>

      {group.items.length > 1 && (
        <ExpandableDetail summaryLabel={t("dailyBriefAgenda.group.showDetails")}>
          <Stack gap="inter-section">
            {group.items.map((item) => (
              <AgendaItemRow
                key={item.id}
                item={item}
                stance={item.ticker ? (stanceByTicker.get(item.ticker) ?? null) : null}
                onOpenInvestmentCase={onOpenInvestmentCase}
                onOpenCandidate={onOpenCandidate}
                onCompare={onCompare}
                onOpenHolding={onOpenHolding}
                onGoToPortfolio={onGoToPortfolio}
              />
            ))}
          </Stack>
        </ExpandableDetail>
      )}
    </Stack>
  );
}
