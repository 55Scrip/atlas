import type { ReactNode } from "react";
import { ACCENT_LINK_STYLE, Inline, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { AGENDA_GROUP_KEY, AGENDA_ITEM_KIND_KEY, SIGNAL_NATURE_KEY } from "../status/statusTone";
import { PriorityBadge } from "./PriorityBadge";
import { SignalNatureBadge } from "./SignalNatureBadge";
import { agendaItemHeadline } from "./describeAgendaHeadline";
import { describeReasonLine } from "./describeReasonFact";
import type { AgendaItemView } from "./dailyBriefAgendaApi";
import { StanceBadge } from "../stance/StanceBadge";
import { primaryStanceReason, stanceReasonSentence } from "../stance/describeStance";
import type { StanceView } from "../stance/stanceApi";
import { TickerExplanationDetail } from "../explainability/TickerExplanationDetail";
import { TickerEvidenceQualityDetail } from "../evidenceQuality/TickerEvidenceQualityDetail";
import { TickerEvidenceTimelineDetail } from "../evidenceTimeline/TickerEvidenceTimelineDetail";

/**
 * Deliverable 5/6 -- one agenda item, the same reusable row wherever
 * the agenda appears (Daily Brief, Portfolio). Every field rendered
 * here is `item`'s own real data: Headline, Reason, Affected company,
 * Portfolio context, Recommended next step (the action links below,
 * derived from `kind`), Source (the group tag), Time (not shown inline
 * -- the page's own "last updated" line already covers it, matching
 * Daily Brief's pre-existing convention).
 *
 * Action targets reuse existing routes exactly -- Investment Case
 * (`/investment-case/:caseId`), Discovery's candidate detail and
 * compare routes (`/discovery/candidate/:ticker`, `/discovery/compare`,
 * Product Sprint 5), and Portfolio's own holding-detail route
 * (`/portfolio/holding/:ticker`). No new route, no new page.
 */
export function AgendaItemRow({
  item,
  stance = null,
  onOpenInvestmentCase,
  onOpenCandidate,
  onCompare,
  onOpenHolding,
  onGoToPortfolio,
}: {
  item: AgendaItemView;
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 8). Only ever rendered when `item
   * .source === "change_intelligence"` -- that is Change Intelligence's
   * own real, already-established "something genuinely changed since
   * the last review" eligibility gate (the same one this item's own
   * presence in the agenda already depended on), reused here rather
   * than a new "did the Stance itself change" comparison this Sprint
   * does not persist a prior snapshot to make. Never shown for an
   * item whose source is something else (Portfolio Fit, a Case
   * Condition, ...) -- those are real signals, but not evidence that
   * Atlas's *stance* specifically moved today. */
  stance?: StanceView | null;
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
  onOpenCandidate: (ticker: string) => void;
  onCompare: (ticker: string) => void;
  onOpenHolding: (ticker: string) => void;
  onGoToPortfolio: () => void;
}) {
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const showsStance = stance !== null && item.source === "change_intelligence";
  const primaryReason = showsStance ? primaryStanceReason(stance) : null;

  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" align="center">
          <PriorityBadge priority={item.priority} />
          <SignalNatureBadge nature={item.nature} />
          <Text color="tertiary" as="span">
            {t(AGENDA_GROUP_KEY[item.group])}
          </Text>
        </Inline>
      </Inline>

      <Text as="p">
        {item.ticker && (
          <Text as="span" color="secondary">
            {item.ticker} —{" "}
          </Text>
        )}
        {agendaItemHeadline(item, t)}
      </Text>

      {item.nature === "persistent_condition" && (
        <Text color="tertiary" as="p">
          {item.since
            ? t("dailyBriefAgenda.since.withDate", { date: new Date(item.since).toLocaleDateString(locale) })
            : t("dailyBriefAgenda.since.withoutDate")}
        </Text>
      )}

      {item.portfolioContext && (
        <Text color="tertiary" as="p">
          {item.portfolioContext}
        </Text>
      )}

      {item.reason.length > 1 &&
        item.reason
          .map((r, index) => ({
            text: r,
            nature: item.reasonNature[index] ?? item.nature,
            fact: (item.reasonFacts ?? [])[index] ?? null,
          }))
          .filter(({ text }) => text !== item.headline)
          .map(({ text, nature, fact }, index) => (
            <Text key={index} color="tertiary" as="p">
              <Text as="span" color="tertiary" style={{ fontWeight: 600 }}>
                {t(SIGNAL_NATURE_KEY[nature])}:{" "}
              </Text>
              {describeReasonLine(text, fact, t)}
            </Text>
          ))}

      {showsStance && stance !== null && (
        <Inline gap="metadata" align="center">
          <Text color="secondary" as="span" style={{ fontWeight: 600 }}>
            {t("stance.dailyBrief.currentViewLabel")}
          </Text>
          <StanceBadge level={stance.level} />
          {primaryReason && (
            <Text color="tertiary" as="span">
              {stanceReasonSentence(primaryReason, t)}
            </Text>
          )}
        </Inline>
      )}

      {item.ticker && (
        <TickerExplanationDetail ticker={item.ticker} summaryLabel={t("explainability.dailyBrief.expandLabel")} t={t} />
      )}

      {item.ticker && (
        <TickerEvidenceQualityDetail ticker={item.ticker} summaryLabel={t("evidenceQuality.dailyBrief.expandLabel")} t={t} />
      )}

      {item.ticker && (
        <TickerEvidenceTimelineDetail ticker={item.ticker} summaryLabel={t("evidenceTimeline.dailyBrief.expandLabel")} t={t} />
      )}

      <Inline gap="row" wrap align="center">
        <AgendaItemActions
          item={item}
          onOpenInvestmentCase={onOpenInvestmentCase}
          onOpenCandidate={onOpenCandidate}
          onCompare={onCompare}
          onOpenHolding={onOpenHolding}
          onGoToPortfolio={onGoToPortfolio}
        />
      </Inline>
    </Stack>
  );
}

/** Exported for `TickerAgendaCard` (Daily Brief Compression) -- the
 * compact grouped card's own "Review →" action reuses this exact
 * routing logic rather than a second copy of the same `kind` switch. */
export function AgendaItemActions({
  item,
  onOpenInvestmentCase,
  onOpenCandidate,
  onCompare,
  onOpenHolding,
  onGoToPortfolio,
}: {
  item: AgendaItemView;
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
  onOpenCandidate: (ticker: string) => void;
  onCompare: (ticker: string) => void;
  onOpenHolding: (ticker: string) => void;
  onGoToPortfolio: () => void;
}) {
  const { t } = useTranslation();
  const link = (labelKey: Parameters<typeof t>[0], onClick: () => void) => (
    <a
      key={labelKey}
      href="#"
      style={ACCENT_LINK_STYLE}
      onClick={(event) => {
        event.preventDefault();
        onClick();
      }}
    >
      {t(labelKey)} →
    </a>
  );

  const actions: ReactNode[] = [];
  switch (item.kind) {
    case "review_investment_case":
    case "revisit_assumption":
    case "evaluate_case_condition":
      if (item.caseId) actions.push(link("dailyBriefAgenda.action.openInvestmentCase", () => onOpenInvestmentCase(item.caseId!, item.ticker)));
      break;
    case "review_portfolio_position":
      if (item.caseId) actions.push(link("dailyBriefAgenda.action.openInvestmentCase", () => onOpenInvestmentCase(item.caseId!, item.ticker)));
      if (item.ticker) actions.push(link("dailyBriefAgenda.action.reviewPosition", () => onOpenHolding(item.ticker!)));
      break;
    case "review_watchlist_candidate":
    case "portfolio_opportunity":
      if (item.ticker) actions.push(link("dailyBriefAgenda.action.reviewCandidate", () => onOpenCandidate(item.ticker!)));
      if (item.ticker) actions.push(link("dailyBriefAgenda.action.compare", () => onCompare(item.ticker!)));
      if (item.caseId) actions.push(link("dailyBriefAgenda.action.openInvestmentCase", () => onOpenInvestmentCase(item.caseId!, item.ticker)));
      break;
    case "compare_candidate":
      if (item.ticker) actions.push(link("dailyBriefAgenda.action.compare", () => onCompare(item.ticker!)));
      break;
    case "portfolio_risk":
      if (item.ticker && item.caseId) {
        actions.push(link("dailyBriefAgenda.action.openInvestmentCase", () => onOpenInvestmentCase(item.caseId!, item.ticker)));
      } else {
        actions.push(link("dailyBriefAgenda.action.goToPortfolio", onGoToPortfolio));
      }
      break;
  }
  return <>{actions}</>;
}
