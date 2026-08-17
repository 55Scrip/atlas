import { useEffect, useState } from "react";
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

/**
 * `transactionType` is an internal enum value (`TransactionType.BUY` /
 * `.SELL`, `atlas/alpha/portfolio/models.py`) read verbatim off the API
 * response — the value itself stays English, per the localization
 * architecture. This maps it to the same translated word the Investment
 * Case's own Buy/Sell control already uses, so activity reads naturally
 * in either language rather than mixing "Köp 10 AAPL".
 */
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
  exists: boolean;
  numberOfHoldings: number;
  cashWeightPercent: number | null;
  holdings: HoldingLite[];
}

type PortfolioStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: PortfolioSummaryView };

const RECENT_ACTIVITY_LIMIT = 10;
const CONTINUE_WORKING_LIMIT = 5;

/**
 * Dashboard (Sprint 1 shell; Alpha Sprint 1A Portfolio Status; Sprint 4
 * Decision Continuity & History).
 *
 * Sprint 4 replaces the former "Active Monitoring Conditions" and
 * "Signals" placeholders (both permanently "Not yet implemented" —
 * neither capability exists) and the three separate raw Recent
 * Decisions/Outcomes/Trade Executions lists with three real,
 * operational sections built on the shared `deriveActivity`/
 * `deriveOutstandingWork` derivations (`../activity/deriveActivity.ts`)
 * — the exact same data History and the Investment Case Timeline read,
 * cross-referenced here instead of fabricated: Needs Attention
 * (deterministic outstanding-work checks, no scoring), Recent Activity
 * (the unified Decision/Outcome/Trade feed, newest first), and Continue
 * Working (the most recently active Cases, linking back in with
 * `state: { origin: "dashboard" }` so Investment Case can honestly say
 * how it was reached). "Portfolio Status" is unchanged from Alpha
 * Sprint 1A. No AI, no prioritization, no placeholder content remains.
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
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
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

  const allLoaded =
    decisionsStatus.kind === "loaded" &&
    outcomesStatus.kind === "loaded" &&
    tradeLogStatus.kind === "loaded" &&
    portfolioStatus.kind === "loaded";

  const holdings = portfolioStatus.kind === "loaded" ? portfolioStatus.view.holdings : [];

  /** Decisions/outcomes/trades are fetched system-wide (every Case ever
   * created), not scoped to the current portfolio -- so every derived
   * list here is filtered to cases with a *current* holding before
   * display. Without this, a Case whose holding was later removed (e.g.
   * a past test/demo position) would keep surfacing as if it still
   * needed the investor's attention today. */
  const heldCaseIds = new Set(holdings.filter((h) => h.caseId !== null).map((h) => h.caseId as string));

  const outstandingWork = allLoaded
    ? deriveOutstandingWork(
        decisionsStatus.decisions,
        outcomesStatus.outcomes,
        tradeLogStatus.trades,
        holdings,
      ).filter((item) => item.caseId !== null && heldCaseIds.has(item.caseId))
    : [];

  const recentActivity = allLoaded
    ? sortActivity(
        deriveActivity(decisionsStatus.decisions, outcomesStatus.outcomes, tradeLogStatus.trades, holdings).filter(
          (event) => event.caseId !== null && heldCaseIds.has(event.caseId),
        ),
        "newest",
      ).slice(0, RECENT_ACTIVITY_LIMIT)
    : [];

  const continueWorking: { caseId: string; security: string; date: string }[] = [];
  if (allLoaded) {
    const seen = new Set<string>();
    for (const event of sortActivity(
      deriveActivity(decisionsStatus.decisions, outcomesStatus.outcomes, tradeLogStatus.trades, holdings),
      "newest",
    )) {
      if (!event.caseId || seen.has(event.caseId) || !heldCaseIds.has(event.caseId)) continue;
      seen.add(event.caseId);
      continueWorking.push({ caseId: event.caseId, security: event.security, date: event.date });
      if (continueWorking.length >= CONTINUE_WORKING_LIMIT) break;
    }
  }

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
              <Stack gap="inter-section">
                <Text color="secondary">{t("dashboard.portfolioStatus.notEstablished")}</Text>
                <RouterLink to="/welcome">{t("dashboard.portfolioStatus.setupCta")}</RouterLink>
              </Stack>
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
            <Heading level={2}>{t("dashboard.needsAttention.heading")}</Heading>
            {!allLoaded && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {allLoaded && outstandingWork.length === 0 && (
              <Text color="secondary">{t("dashboard.needsAttention.empty")}</Text>
            )}
            {allLoaded && outstandingWork.length > 0 && (
              <Stack gap="inter-section">
                {outstandingWork.map((item) =>
                  item.caseId ? (
                    <RouterLink
                      key={item.id}
                      to={`/investment-case/${item.caseId}`}
                      state={{ origin: "dashboard" }}
                    >
                      {t(OUTSTANDING_WORK_LABEL_KEY[item.kind], { security: item.security })}
                    </RouterLink>
                  ) : (
                    <Text key={item.id} color="tertiary">
                      {t(OUTSTANDING_WORK_LABEL_KEY[item.kind], { security: item.security })}
                    </Text>
                  ),
                )}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.recentActivity.heading")}</Heading>
            {!allLoaded && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {allLoaded && recentActivity.length === 0 && (
              <Text color="secondary">{t("dashboard.recentActivity.empty")}</Text>
            )}
            {allLoaded && recentActivity.length > 0 && (
              <Stack gap="inter-section">
                {recentActivity.map((event) => (
                  <div key={event.id}>
                    {event.caseId ? (
                      <RouterLink
                        to={`/investment-case/${event.caseId}`}
                        state={{ origin: "dashboard" }}
                      >
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
            {allLoaded && <RouterLink to="/history">{t("dashboard.viewHistoryLink")}</RouterLink>}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>{t("dashboard.continueWorking.heading")}</Heading>
            {!allLoaded && (
              <Text role="status" aria-live="polite">
                {t("common.loading")}
              </Text>
            )}
            {allLoaded && continueWorking.length === 0 && (
              <Text color="secondary">{t("dashboard.continueWorking.empty")}</Text>
            )}
            {allLoaded && continueWorking.length > 0 && (
              <Stack gap="inter-section">
                {continueWorking.map((item) => (
                  <RouterLink
                    key={item.caseId}
                    to={`/investment-case/${item.caseId}`}
                    state={{ origin: "dashboard" }}
                  >
                    {item.security}
                  </RouterLink>
                ))}
              </Stack>
            )}
            {allLoaded && continueWorking.length > 0 && (
              <RouterLink to="/history">{t("dashboard.viewHistoryLink")}</RouterLink>
            )}
          </Stack>
        </Surface>
      </Stack>
    </Container>
  );
}
