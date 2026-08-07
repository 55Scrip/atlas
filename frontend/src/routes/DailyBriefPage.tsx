import { Link as RouterLink } from "react-router-dom";
import { Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  deriveActivity,
  deriveOutstandingWork,
  sortActivity,
  type DecisionRecord,
  type HoldingLite,
  type OutcomeRecord,
  type OutstandingWorkItem,
  type TradeLogEntry,
} from "../activity/deriveActivity";
import { useEffect, useState } from "react";

const DECISION_TYPE_KEY: Record<string, TranslationKey> = {
  BUY: "investmentCase.decision.typeBuy",
  SELL: "investmentCase.decision.typeSell",
  HOLD: "investmentCase.decision.typeHold",
  WATCH: "investmentCase.decision.typeWatch",
  PASS: "investmentCase.decision.typePass",
};

const OUTSTANDING_WORK_LABEL_KEY: Record<OutstandingWorkItem["kind"], TranslationKey> = {
  "outcome-missing": "dashboard.needsAttention.outcomeMissing",
  "trade-missing": "dashboard.needsAttention.tradeMissing",
  "reconciliation-needed": "dashboard.needsAttention.reconciliationNeeded",
};

const PRIORITY_LIMIT = 3;
const RECENT_DECISIONS_LIMIT = 5;

type DecisionsStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; decisions: DecisionRecord[] };

type OutcomesStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; outcomes: OutcomeRecord[] };

type TradeLogStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; trades: TradeLogEntry[] };

interface PortfolioSummaryView {
  holdings: HoldingLite[];
}

type PortfolioStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: PortfolioSummaryView };

/**
 * Daily Brief (Implementation Sprint 1) — the first truthful Alpha
 * version of `UX-015`, deliberately narrowed to what this sprint locks:
 * no Watchlist Update preview, no Discover Highlight preview, no
 * external market data — every fact here is derived from the same four
 * endpoints (`/api/decisions`, `/api/outcomes`,
 * `/api/alpha-portfolio/trade-log`, `/api/alpha-portfolio`) and the same
 * `deriveActivity`/`deriveOutstandingWork` functions Dashboard and
 * History already read. Nothing new is computed, persisted, or fetched
 * — this page is a differently-shaped, more compact presentation of
 * facts that already exist elsewhere in Alpha.
 *
 * The Verdict, Priority, and Recent Decisions sections all read
 * directly off `deriveOutstandingWork`/`deriveActivity`'s own
 * deterministic output — no scoring, no ranking, no AI. Monitoring and
 * the footer are static, deliberately truthful text: Alpha has no live
 * market, earnings, or valuation monitoring, so neither section claims
 * any.
 */
export function DailyBriefPage() {
  const { t } = useTranslation();
  const [decisionsStatus, setDecisionsStatus] = useState<DecisionsStatus>({ kind: "loading" });
  const [outcomesStatus, setOutcomesStatus] = useState<OutcomesStatus>({ kind: "loading" });
  const [tradeLogStatus, setTradeLogStatus] = useState<TradeLogStatus>({ kind: "loading" });
  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatus>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/decisions", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DecisionRecord[]>;
      })
      .then((decisions) => setDecisionsStatus({ kind: "loaded", decisions }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionsStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/outcomes", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<OutcomeRecord[]>;
      })
      .then((outcomes) => setOutcomesStatus({ kind: "loaded", outcomes }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setOutcomesStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio/trade-log", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<TradeLogEntry[]>;
      })
      .then((trades) => setTradeLogStatus({ kind: "loaded", trades }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setTradeLogStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioSummaryView>;
      })
      .then((view) => setPortfolioStatus({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  const allLoaded =
    decisionsStatus.kind === "loaded" &&
    outcomesStatus.kind === "loaded" &&
    tradeLogStatus.kind === "loaded" &&
    portfolioStatus.kind === "loaded";

  const holdings = portfolioStatus.kind === "loaded" ? portfolioStatus.view.holdings : [];

  const outstandingWork = allLoaded
    ? deriveOutstandingWork(decisionsStatus.decisions, outcomesStatus.outcomes, tradeLogStatus.trades, holdings)
    : [];
  const priorityItems = outstandingWork.slice(0, PRIORITY_LIMIT);

  const recentDecisions = allLoaded
    ? sortActivity(
        deriveActivity(decisionsStatus.decisions, outcomesStatus.outcomes, tradeLogStatus.trades, holdings),
        "newest",
      ).slice(0, RECENT_DECISIONS_LIMIT)
    : [];

  const verdictKey: TranslationKey =
    outstandingWork.length === 0
      ? "dailyBrief.verdict.nothingUrgent"
      : outstandingWork.length === 1
        ? "dailyBrief.verdict.oneItem"
        : "dailyBrief.verdict.items";

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("dailyBrief.title")}</Heading>

        <Divider />

        {/* Daily Verdict — exactly one sentence, sourced solely from
            deriveOutstandingWork's own count. No severity language
            (urgent/critical), no invented framing beyond a plain count. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            {!allLoaded && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {allLoaded && (
              <Text>
                {verdictKey === "dailyBrief.verdict.items"
                  ? t(verdictKey, { count: outstandingWork.length })
                  : t(verdictKey)}
              </Text>
            )}
          </Stack>
        </Surface>

        <Divider />

        {/* Priority — the same deterministic outstanding-work checks
            Dashboard's Needs Attention already computes and labels,
            capped to 3. Reconciliation items with no linked Case route
            to Portfolio (where reconciliation is actually resolved);
            every other item routes to its Investment Case. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dailyBrief.priority.heading")}</Heading>
            {!allLoaded && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {allLoaded && priorityItems.length === 0 && (
              <Text color="secondary">{t("dashboard.needsAttention.empty")}</Text>
            )}
            {allLoaded && priorityItems.length > 0 && (
              <Stack gap="inter-section">
                {priorityItems.map((item) => (
                  <RouterLink
                    key={item.id}
                    to={item.caseId ? `/investment-case/${item.caseId}` : "/portfolio"}
                    state={item.caseId ? { origin: "daily-brief" } : undefined}
                  >
                    {t(OUTSTANDING_WORK_LABEL_KEY[item.kind], { security: item.security })}
                  </RouterLink>
                ))}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        {/* Recent Decisions — the same deriveActivity feed History and
            Dashboard already read, newest first, capped small. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dailyBrief.recentDecisions.heading")}</Heading>
            {!allLoaded && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {allLoaded && recentDecisions.length === 0 && (
              <Text color="secondary">{t("dailyBrief.recentDecisions.empty")}</Text>
            )}
            {allLoaded && recentDecisions.length > 0 && (
              <Stack gap="inter-section">
                {recentDecisions.map((event) => (
                  <div key={event.id}>
                    {event.caseId ? (
                      <RouterLink to={`/investment-case/${event.caseId}`} state={{ origin: "daily-brief" }}>
                        {event.security}
                      </RouterLink>
                    ) : (
                      <Text>{event.security}</Text>
                    )}
                    <Text color="secondary" as="p">
                      {event.decisionType &&
                        (DECISION_TYPE_KEY[event.decisionType]
                          ? t(DECISION_TYPE_KEY[event.decisionType]!)
                          : event.decisionType)}
                      {" — "}
                      {event.summary}
                    </Text>
                    <Text color="tertiary" as="p">
                      {event.date}
                    </Text>
                  </div>
                ))}
              </Stack>
            )}
            <RouterLink to="/history">{t("dashboard.viewHistoryLink")}</RouterLink>
          </Stack>
        </Surface>

        <Divider />

        {/* Monitoring — static, deliberately truthful. Alpha has no
            live market/earnings/valuation monitoring; this states only
            what genuinely happens: recorded decisions and cases are
            read back on every future visit. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dailyBrief.monitoring.heading")}</Heading>
            <Text color="secondary">{t("dailyBrief.monitoring.body")}</Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Text color="secondary">{t("dailyBrief.footer.reminder")}</Text>
        </Surface>
      </Stack>
    </Container>
  );
}
