import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";

/**
 * `transactionType` is an internal enum value (`TransactionType.BUY` /
 * `.SELL`, `atlas/alpha/portfolio/models.py`) read verbatim off the API
 * response — the value itself stays English, per the localization
 * architecture. This maps it to the same translated word the Investment
 * Case's own Buy/Sell control already uses, so the trade log reads
 * naturally in either language rather than mixing "Köp 10 AAPL".
 */
const TRANSACTION_TYPE_KEY: Record<string, TranslationKey> = {
  BUY: "investmentCase.decision.typeBuy",
  SELL: "investmentCase.decision.typeSell",
};

interface DecisionSummary {
  id: string;
  subject: string;
  recordedAt: string;
}

type DecisionsStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; decisions: DecisionSummary[] };

interface OutcomeSummary {
  id: string;
  statement: string;
  occurredAt: string;
}

type OutcomesStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; outcomes: OutcomeSummary[] };

interface TradeLogSummary {
  outcomeId: string;
  security: string;
  transactionType: string;
  quantity: number;
  executionPrice: number;
  executedAt: string;
}

type TradeLogStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; trades: TradeLogSummary[] };

interface PortfolioSummaryView {
  exists: boolean;
  numberOfHoldings: number;
  cashWeightPercent: number | null;
}

type PortfolioStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: PortfolioSummaryView };

/**
 * Dashboard Shell (Sprint 1, Commit 6) — structural layout only.
 *
 * Section set is UX-012 §14's own five "Required areas" for the
 * Dashboard, verbatim: Portfolio status summary, Active Monitoring
 * Conditions, Recent Decisions summary, Signals list, Navigation to all
 * active Workspaces. Everything except Recent Decisions and Portfolio
 * Status is a labeled placeholder — Monitoring, Signals, and Workspaces
 * remain explicitly out of scope.
 *
 * Alpha Sprint 1A: "Portfolio Status" is wired to a concise summary
 * (whether an Alpha portfolio exists, its holding count, cash %) and a
 * link to `/portfolio` — deliberately minimal, per this sprint's own
 * scope clarification.
 *
 * Alpha Sprint 1B: "Recent Decisions" is joined by two further History
 * sections -- Outcomes and Trade Executions -- both read-only lists
 * matching the identical loading/error/empty/list pattern Decisions
 * already established. No redesign: three small, consistent sections,
 * not a unified timeline.
 *
 * Single-column layout, no secondary sidebar: UX-012A's own Layout
 * foundations state this directly — "no persistent side panels" and
 * "full-width only for Dashboard signals." There is no UX-012 §14
 * structural text describing a primary/sidebar split for the Dashboard
 * either, so none is built.
 *
 * Responsive layout: a single-column vertical Stack requires no
 * breakpoint to adapt — it reflows correctly at any viewport width by
 * construction. No breakpoint token exists anywhere in the token system
 * (Commits 3/4 found none in the governing corpus), so none is invented
 * here; there is also no multi-column arrangement in this shell that
 * would need one.
 */
export function DashboardPage() {
  const { t } = useTranslation();
  const [decisionsStatus, setDecisionsStatus] = useState<DecisionsStatus>({ kind: "loading" });
  const [portfolioStatus, setPortfolioStatus] = useState<PortfolioStatus>({ kind: "loading" });
  const [outcomesStatus, setOutcomesStatus] = useState<OutcomesStatus>({ kind: "loading" });
  const [tradeLogStatus, setTradeLogStatus] = useState<TradeLogStatus>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/decisions", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<DecisionSummary[]>;
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

    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
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

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/outcomes", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<OutcomeSummary[]>;
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
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<TradeLogSummary[]>;
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

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("dashboard.title")}</Heading>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.portfolioStatus.heading")}</Heading>
            {portfolioStatus.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {portfolioStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("dashboard.portfolioStatus.loadError", { message: portfolioStatus.message })}
              </Text>
            )}
            {portfolioStatus.kind === "loaded" && !portfolioStatus.view.exists && (
              <Text color="secondary">{t("dashboard.portfolioStatus.notEstablished")}</Text>
            )}
            {portfolioStatus.kind === "loaded" && portfolioStatus.view.exists && (
              <Text color="secondary">
                {t("dashboard.portfolioStatus.summary", {
                  count: portfolioStatus.view.numberOfHoldings,
                  holdingWord:
                    portfolioStatus.view.numberOfHoldings === 1
                      ? t("dashboard.portfolioStatus.holdingSingular")
                      : t("dashboard.portfolioStatus.holdingPlural"),
                })}
                {portfolioStatus.view.cashWeightPercent !== null
                  ? t("dashboard.portfolioStatus.cashSuffix", {
                      percent: portfolioStatus.view.cashWeightPercent,
                    })
                  : ""}
              </Text>
            )}
            <RouterLink to="/portfolio">{t("dashboard.portfolioStatus.goToPortfolio")}</RouterLink>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.monitoring.heading")}</Heading>
            <Text color="secondary">{t("dashboard.notYetImplemented")}</Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.recentDecisions.heading")}</Heading>
            {decisionsStatus.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {decisionsStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("dashboard.recentDecisions.loadError", { message: decisionsStatus.message })}
              </Text>
            )}
            {decisionsStatus.kind === "loaded" && decisionsStatus.decisions.length === 0 && (
              <Text color="secondary">{t("dashboard.recentDecisions.empty")}</Text>
            )}
            {decisionsStatus.kind === "loaded" && decisionsStatus.decisions.length > 0 && (
              <Stack gap="inter-section">
                {decisionsStatus.decisions.map((decision) => (
                  <div key={decision.id}>
                    <Text>{decision.subject}</Text>
                    <Text color="secondary" as="p">
                      {decision.recordedAt}
                    </Text>
                  </div>
                ))}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.outcomes.heading")}</Heading>
            {outcomesStatus.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {outcomesStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("dashboard.outcomes.loadError", { message: outcomesStatus.message })}
              </Text>
            )}
            {outcomesStatus.kind === "loaded" && outcomesStatus.outcomes.length === 0 && (
              <Text color="secondary">{t("dashboard.outcomes.empty")}</Text>
            )}
            {outcomesStatus.kind === "loaded" && outcomesStatus.outcomes.length > 0 && (
              <Stack gap="inter-section">
                {outcomesStatus.outcomes.map((outcome) => (
                  <div key={outcome.id}>
                    <Text>{outcome.statement}</Text>
                    <Text color="secondary" as="p">
                      {outcome.occurredAt}
                    </Text>
                  </div>
                ))}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.tradeExecutions.heading")}</Heading>
            {tradeLogStatus.kind === "loading" && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {tradeLogStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                {t("dashboard.tradeExecutions.loadError", { message: tradeLogStatus.message })}
              </Text>
            )}
            {tradeLogStatus.kind === "loaded" && tradeLogStatus.trades.length === 0 && (
              <Text color="secondary">{t("dashboard.tradeExecutions.empty")}</Text>
            )}
            {tradeLogStatus.kind === "loaded" && tradeLogStatus.trades.length > 0 && (
              <Stack gap="inter-section">
                {tradeLogStatus.trades.map((trade) => (
                  <div key={trade.outcomeId}>
                    <Text>
                      {TRANSACTION_TYPE_KEY[trade.transactionType]
                        ? t(TRANSACTION_TYPE_KEY[trade.transactionType]!)
                        : trade.transactionType}{" "}
                      {trade.quantity} {trade.security} @ {trade.executionPrice}
                    </Text>
                    <Text color="secondary" as="p">
                      {trade.executedAt}
                    </Text>
                  </div>
                ))}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.signals.heading")}</Heading>
            <Text color="secondary">{t("dashboard.notYetImplemented")}</Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.workspaces.heading")}</Heading>
            <Text color="secondary">{t("dashboard.workspaces.empty")}</Text>
          </Stack>
        </Surface>
      </Stack>
    </Container>
  );
}
