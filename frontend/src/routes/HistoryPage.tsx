import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  deriveActivity,
  sortActivity,
  type ActivityEvent,
  type DecisionRecord,
  type HoldingLite,
  type OutcomeRecord,
  type TradeLogEntry,
} from "../activity/deriveActivity";

interface PortfolioViewLite {
  holdings: HoldingLite[];
}

type FetchStatus<T> =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; data: T };

type StatusFilter = "all" | "open" | "completed";
type TypeFilter = "all" | "BUY" | "SELL" | "HOLD";
type SortDirection = "newest" | "oldest";

const KIND_LABEL_KEY: Record<ActivityEvent["kind"], TranslationKey> = {
  decision: "history.row.kindDecision",
  outcome: "history.row.kindOutcome",
  trade: "history.row.kindTrade",
};

const DECISION_TYPE_KEY: Record<string, TranslationKey> = {
  BUY: "investmentCase.decision.typeBuy",
  SELL: "investmentCase.decision.typeSell",
  HOLD: "investmentCase.decision.typeHold",
  WATCH: "investmentCase.decision.typeWatch",
  PASS: "investmentCase.decision.typePass",
};

/**
 * History (Sprint 4): the permanent chronological record of an
 * investor's activity, built entirely from `deriveActivity` over the
 * same `/api/decisions`, `/api/outcomes`, and
 * `/api/alpha-portfolio/trade-log` data every other page already reads.
 * No new backend endpoint. No generated summaries — each row's summary
 * is either a Decision's own `reason`, an Outcome's own `statement`, or
 * a Trade's own quantity/price, never invented text.
 */
export function HistoryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [decisionsStatus, setDecisionsStatus] = useState<FetchStatus<DecisionRecord[]>>({
    kind: "loading",
  });
  const [outcomesStatus, setOutcomesStatus] = useState<FetchStatus<OutcomeRecord[]>>({
    kind: "loading",
  });
  const [tradesStatus, setTradesStatus] = useState<FetchStatus<TradeLogEntry[]>>({
    kind: "loading",
  });
  const [portfolioStatus, setPortfolioStatus] = useState<FetchStatus<PortfolioViewLite>>({
    kind: "loading",
  });

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [sortDirection, setSortDirection] = useState<SortDirection>("newest");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/decisions", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DecisionRecord[]>;
      })
      .then((data) => setDecisionsStatus({ kind: "loaded", data }))
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
      .then((data) => setOutcomesStatus({ kind: "loaded", data }))
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
      .then((data) => setTradesStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setTradesStatus({
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
        return response.json() as Promise<PortfolioViewLite>;
      })
      .then((data) => setPortfolioStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  const statuses = [decisionsStatus, outcomesStatus, tradesStatus, portfolioStatus];
  const isLoading = statuses.some((s) => s.kind === "loading");
  const firstError = statuses.find((s) => s.kind === "error") as
    | { kind: "error"; message: string }
    | undefined;

  const events =
    decisionsStatus.kind === "loaded" &&
    outcomesStatus.kind === "loaded" &&
    tradesStatus.kind === "loaded" &&
    portfolioStatus.kind === "loaded"
      ? deriveActivity(
          decisionsStatus.data,
          outcomesStatus.data,
          tradesStatus.data,
          portfolioStatus.data.holdings,
        )
      : [];

  const filtered = events.filter((event) => {
    if (statusFilter !== "all" && event.status !== statusFilter) return false;
    if (typeFilter !== "all" && event.decisionType !== typeFilter) return false;
    return true;
  });
  const sorted = sortActivity(filtered, sortDirection);

  function openEvent(event: ActivityEvent) {
    if (!event.caseId) return;
    navigate(`/investment-case/${event.caseId}`, { state: { origin: "history" } });
  }

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("history.title")}</Heading>

        {isLoading && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {firstError && (
          <Text color="tertiary" role="alert">
            {t("history.loadError", { message: firstError.message })}
          </Text>
        )}

        {!isLoading && !firstError && (
          <>
            <Surface tier="primary">
              <Stack gap="inter-section">
                <div>
                  <Button
                    variant={statusFilter === "all" ? "primary" : "tertiary"}
                    onClick={() => setStatusFilter("all")}
                  >
                    {t("history.filter.all")}
                  </Button>{" "}
                  <Button
                    variant={statusFilter === "open" ? "primary" : "tertiary"}
                    onClick={() => setStatusFilter("open")}
                  >
                    {t("history.filter.open")}
                  </Button>{" "}
                  <Button
                    variant={statusFilter === "completed" ? "primary" : "tertiary"}
                    onClick={() => setStatusFilter("completed")}
                  >
                    {t("history.filter.completed")}
                  </Button>
                </div>
                <div>
                  <Button
                    variant={typeFilter === "all" ? "primary" : "tertiary"}
                    onClick={() => setTypeFilter("all")}
                  >
                    {t("history.filter.all")}
                  </Button>{" "}
                  <Button
                    variant={typeFilter === "BUY" ? "primary" : "tertiary"}
                    onClick={() => setTypeFilter("BUY")}
                  >
                    {t("investmentCase.decision.typeBuy")}
                  </Button>{" "}
                  <Button
                    variant={typeFilter === "SELL" ? "primary" : "tertiary"}
                    onClick={() => setTypeFilter("SELL")}
                  >
                    {t("investmentCase.decision.typeSell")}
                  </Button>{" "}
                  <Button
                    variant={typeFilter === "HOLD" ? "primary" : "tertiary"}
                    onClick={() => setTypeFilter("HOLD")}
                  >
                    {t("investmentCase.decision.typeHold")}
                  </Button>
                </div>
                <div>
                  <Button
                    variant={sortDirection === "newest" ? "primary" : "tertiary"}
                    onClick={() => setSortDirection("newest")}
                  >
                    {t("history.sort.newest")}
                  </Button>{" "}
                  <Button
                    variant={sortDirection === "oldest" ? "primary" : "tertiary"}
                    onClick={() => setSortDirection("oldest")}
                  >
                    {t("history.sort.oldest")}
                  </Button>
                </div>
              </Stack>
            </Surface>

            <Divider />

            <Surface tier="primary">
              <Stack gap="inter-section">
                {events.length === 0 && <Text color="secondary">{t("history.empty")}</Text>}
                {events.length > 0 && sorted.length === 0 && (
                  <Text color="secondary">{t("history.noneMatchFilter")}</Text>
                )}
                {sorted.map((event) => (
                  <div key={event.id}>
                    <Button variant="tertiary" onClick={() => openEvent(event)}>
                      {event.security}
                    </Button>
                    <Text>{t(KIND_LABEL_KEY[event.kind])}</Text>
                    <Text color="secondary" as="p">
                      {event.decisionType &&
                        (DECISION_TYPE_KEY[event.decisionType]
                          ? t(DECISION_TYPE_KEY[event.decisionType]!)
                          : event.decisionType)}
                      {" · "}
                      {event.status === "open" ? t("history.status.open") : t("history.status.completed")}
                      {" · "}
                      {event.date}
                    </Text>
                    {event.summary && (
                      <Text color="secondary" as="p">
                        {event.summary}
                      </Text>
                    )}
                    <Divider tone="hairline" />
                  </div>
                ))}
              </Stack>
            </Surface>
          </>
        )}
      </Stack>
    </Container>
  );
}
