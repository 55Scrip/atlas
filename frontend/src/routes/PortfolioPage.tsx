import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";

/**
 * `concentrationLevel` is an internal enum value (`ConcentrationLevel.LOW`
 * etc., `atlas/domains/portfolio/models.py`, serialized as its raw
 * `.value` — "Low", "Moderate", "Elevated", "High") — the value itself
 * stays English on the wire, per the localization architecture. This
 * maps it to a translated word only where it's displayed.
 */
const CONCENTRATION_LEVEL_KEY: Record<string, TranslationKey> = {
  Low: "portfolio.concentrationLevel.low",
  Moderate: "portfolio.concentrationLevel.moderate",
  Elevated: "portfolio.concentrationLevel.elevated",
  High: "portfolio.concentrationLevel.high",
};

interface HoldingView {
  ticker: string;
  weightPercent: number;
  valueAbsolute: number | null;
  caseId: string | null;
  reconciliationStatus: "NONE" | "UPDATED" | "AWAITING_RECONCILIATION";
}

interface PortfolioView {
  exists: boolean;
  entryMode: string | null;
  hasAbsoluteValues: boolean;
  holdings: HoldingView[];
  cashWeightPercent: number | null;
  cashValueAbsolute: number | null;
  totalValue: number | null;
  numberOfHoldings: number;
  concentrationLevel: string | null;
  objective: string | null;
  horizon: string | null;
  awaitingReconciliation: boolean;
}

type Status =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: PortfolioView };

type CaseCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "error"; message: string };

type ReconcileStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string };

interface ReplaceRow {
  ticker: string;
  weightPercent: string;
  valueAbsolute: string;
}

const UNALLOCATED_TOLERANCE = 0.01;

/**
 * Portfolio (Alpha Sprint 1A, extended Alpha Sprint 1B). Shows holdings,
 * allocation percentages, cash/unallocated when known, a path from any
 * holding into an Investment Case, and -- since Sprint 1B -- each
 * holding's status relative to the most recently recorded trade
 * ("Updated automatically" or "Awaiting reconciliation"), plus a
 * portfolio-level banner and reconciliation actions when any holding is
 * awaiting reconciliation.
 *
 * Foundation Patch: a holding that already has a linked Investment Case
 * (`holding.caseId`, persisted by the backend's case-link endpoint)
 * navigates straight there — no new Case is created. Only a holding
 * with no linked Case yet creates one and records the association.
 */
export function PortfolioPage() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [caseCreateStatus, setCaseCreateStatus] = useState<Record<string, CaseCreateStatus>>({});
  const [reconcileWeightInputs, setReconcileWeightInputs] = useState<Record<string, string>>({});
  const [reconcileStatus, setReconcileStatus] = useState<Record<string, ReconcileStatus>>({});

  const [showReplaceForm, setShowReplaceForm] = useState(false);
  const [replaceRows, setReplaceRows] = useState<ReplaceRow[]>([]);
  const [replaceCashWeight, setReplaceCashWeight] = useState("");
  const [replaceCashValue, setReplaceCashValue] = useState("");
  const [replaceStatus, setReplaceStatus] = useState<ReconcileStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<PortfolioView>;
      })
      .then((view) => setStatus({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });

    return () => controller.abort();
  }, []);

  function openInvestmentCase(ticker: string, existingCaseId: string | null) {
    if (existingCaseId) {
      window.location.assign(`/investment-case/${existingCaseId}`);
      return;
    }

    setCaseCreateStatus((current) => ({ ...current, [ticker]: { kind: "creating" } }));
    fetch("/api/cases", { method: "POST" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<{ caseId: string }>;
      })
      .then((created) => {
        if (ticker === "__new__") {
          window.location.assign(`/investment-case/${created.caseId}`);
          return;
        }
        return fetch(`/api/alpha-portfolio/holdings/${encodeURIComponent(ticker)}/case-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidateCaseId: created.caseId }),
        })
          .then((linkResponse) => {
            if (!linkResponse.ok) {
              throw new Error(`Backend responded with ${linkResponse.status}`);
            }
            return linkResponse.json() as Promise<{ caseId: string }>;
          })
          .then((linked) => {
            window.location.assign(`/investment-case/${linked.caseId}`);
          });
      })
      .catch((error: unknown) => {
        setCaseCreateStatus((current) => ({
          ...current,
          [ticker]: {
            kind: "error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function submitUpdateHoldingWeight(ticker: string) {
    const raw = reconcileWeightInputs[ticker] ?? "";
    const weightPercent = Number.parseFloat(raw);
    if (raw.trim() === "" || Number.isNaN(weightPercent)) {
      setReconcileStatus((current) => ({
        ...current,
        [ticker]: { kind: "error", message: t("portfolio.holdings.errors.invalidPercentage") },
      }));
      return;
    }

    setReconcileStatus((current) => ({ ...current, [ticker]: { kind: "submitting" } }));
    fetch("/api/alpha-portfolio/reconcile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "UPDATE_HOLDING_WEIGHT", ticker, weightPercent }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setReconcileStatus((current) => ({
            ...current,
            [ticker]: { kind: "error", message: body.detail ?? t("common.invalidInput") },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const view = (await response.json()) as PortfolioView;
        setStatus({ kind: "loaded", view });
        setReconcileStatus((current) => ({ ...current, [ticker]: { kind: "idle" } }));
      })
      .catch((error: unknown) => {
        setReconcileStatus((current) => ({
          ...current,
          [ticker]: {
            kind: "error",
            message: error instanceof Error ? error.message : t("common.unknownError"),
          },
        }));
      });
  }

  function openReplaceForm() {
    if (status.kind === "loaded" && status.view.exists) {
      setReplaceRows(
        status.view.holdings.map((holding) => ({
          ticker: holding.ticker,
          weightPercent: String(holding.weightPercent),
          valueAbsolute: holding.valueAbsolute !== null ? String(holding.valueAbsolute) : "",
        })),
      );
      setReplaceCashWeight(
        status.view.cashWeightPercent !== null ? String(status.view.cashWeightPercent) : "",
      );
      setReplaceCashValue(
        status.view.cashValueAbsolute !== null ? String(status.view.cashValueAbsolute) : "",
      );
    }
    setReplaceStatus({ kind: "idle" });
    setShowReplaceForm(true);
  }

  function updateReplaceRow(index: number, patch: Partial<ReplaceRow>) {
    setReplaceRows((current) =>
      current.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );
  }

  function submitReplaceAllocation() {
    const holdings = replaceRows
      .filter((row) => row.ticker.trim() !== "")
      .map((row) => ({
        ticker: row.ticker.trim(),
        weightPercent: Number.parseFloat(row.weightPercent),
        valueAbsolute: row.valueAbsolute.trim() === "" ? null : Number.parseFloat(row.valueAbsolute),
      }));

    if (holdings.length === 0 || holdings.some((h) => Number.isNaN(h.weightPercent))) {
      setReplaceStatus({
        kind: "error",
        message: t("portfolio.replaceForm.errors.invalidPercentage"),
      });
      return;
    }

    setReplaceStatus({ kind: "submitting" });
    fetch("/api/alpha-portfolio/reconcile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "REPLACE_ALLOCATION",
        holdings,
        cashWeightPercent:
          replaceCashWeight.trim() === "" ? null : Number.parseFloat(replaceCashWeight),
        cashValueAbsolute:
          replaceCashValue.trim() === "" ? null : Number.parseFloat(replaceCashValue),
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setReplaceStatus({ kind: "error", message: body.detail ?? t("common.invalidInput") });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const view = (await response.json()) as PortfolioView;
        setStatus({ kind: "loaded", view });
        setReplaceStatus({ kind: "idle" });
        setShowReplaceForm(false);
      })
      .catch((error: unknown) => {
        setReplaceStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  const unallocatedPercent =
    status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0
      ? 100 -
        status.view.holdings.reduce((sum, holding) => sum + holding.weightPercent, 0) -
        (status.view.cashWeightPercent ?? 0)
      : null;

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("portfolio.title")}</Heading>

        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {status.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("portfolio.loadError", { message: status.message })}
          </Text>
        )}

        {status.kind === "loaded" && !status.view.exists && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>{t("portfolio.notEstablished")}</Text>
              <RouterLink to="/welcome">{t("portfolio.setupLink")}</RouterLink>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length === 0 && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>{t("portfolio.empty.title")}</Text>
              {status.view.objective && (
                <Text color="secondary">
                  {t("portfolio.empty.objective", { value: status.view.objective })}
                </Text>
              )}
              {status.view.horizon && (
                <Text color="secondary">
                  {t("portfolio.empty.horizon", { value: status.view.horizon })}
                </Text>
              )}
              <Text color="secondary">{t("portfolio.empty.explanation")}</Text>
              <div>
                <Button variant="tertiary" onClick={() => openInvestmentCase("__new__", null)}>
                  {t("portfolio.openNewCase")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0 && (
          <Stack gap="inter-section">
            {status.view.awaitingReconciliation && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Text color="tertiary" role="status">
                    {t("portfolio.awaitingBanner.title")}
                  </Text>
                  <Text color="secondary">{t("portfolio.awaitingBanner.body")}</Text>
                  {!showReplaceForm && (
                    <div>
                      <Button variant="tertiary" onClick={openReplaceForm}>
                        {t("portfolio.replaceAllocationButton")}
                      </Button>
                    </div>
                  )}
                </Stack>
              </Surface>
            )}

            {showReplaceForm && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Heading level={2}>{t("portfolio.replaceForm.heading")}</Heading>
                  {replaceRows.map((row, index) => (
                    <Stack key={index} gap="inter-section">
                      <Text as="label">
                        {t("form.ticker")}
                        <br />
                        <input
                          value={row.ticker}
                          onChange={(event) => updateReplaceRow(index, { ticker: event.target.value })}
                        />
                      </Text>
                      <Text as="label">
                        {t("form.weightPercent")}
                        <br />
                        <input
                          value={row.weightPercent}
                          onChange={(event) =>
                            updateReplaceRow(index, { weightPercent: event.target.value })
                          }
                        />
                      </Text>
                      <Text as="label">
                        {t("form.valueOptional")}
                        <br />
                        <input
                          value={row.valueAbsolute}
                          onChange={(event) =>
                            updateReplaceRow(index, { valueAbsolute: event.target.value })
                          }
                        />
                      </Text>
                      <Divider tone="hairline" />
                    </Stack>
                  ))}
                  <Text as="label">
                    {t("form.cashPercent")}
                    <br />
                    <input
                      value={replaceCashWeight}
                      onChange={(event) => setReplaceCashWeight(event.target.value)}
                    />
                  </Text>
                  <Text as="label">
                    {t("form.cashValueOptional")}
                    <br />
                    <input
                      value={replaceCashValue}
                      onChange={(event) => setReplaceCashValue(event.target.value)}
                    />
                  </Text>
                  {replaceStatus.kind === "error" && (
                    <Text color="tertiary" role="alert">
                      {replaceStatus.message}
                    </Text>
                  )}
                  <div>
                    <Button
                      variant="primary"
                      onClick={submitReplaceAllocation}
                      disabled={replaceStatus.kind === "submitting"}
                    >
                      {replaceStatus.kind === "submitting"
                        ? t("common.saving")
                        : t("portfolio.replaceForm.saveButton")}
                    </Button>{" "}
                    <Button variant="tertiary" onClick={() => setShowReplaceForm(false)}>
                      {t("common.cancel")}
                    </Button>
                  </div>
                </Stack>
              </Surface>
            )}

            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>{t("portfolio.holdings.heading")}</Heading>
                {!status.view.hasAbsoluteValues && (
                  <Text color="secondary">{t("portfolio.holdings.percentOnly")}</Text>
                )}
                {status.view.hasAbsoluteValues && status.view.totalValue !== null && (
                  <Text color="secondary">
                    {t("portfolio.holdings.totalValue", { value: status.view.totalValue })}
                  </Text>
                )}

                {status.view.holdings.map((holding) => {
                  const thisCaseCreateStatus: CaseCreateStatus =
                    caseCreateStatus[holding.ticker] ?? { kind: "idle" };
                  const thisReconcileStatus: ReconcileStatus =
                    reconcileStatus[holding.ticker] ?? { kind: "idle" };

                  return (
                    <div key={holding.ticker}>
                      <Text>{holding.ticker}</Text>
                      <Text color="secondary" as="p">
                        {holding.weightPercent}%
                        {holding.valueAbsolute !== null ? ` — ${holding.valueAbsolute}` : ""}
                      </Text>
                      {holding.reconciliationStatus === "UPDATED" && (
                        <Text color="secondary" as="p">
                          {t("portfolio.holdings.updatedAutomatically")}
                        </Text>
                      )}
                      {holding.reconciliationStatus === "AWAITING_RECONCILIATION" && (
                        <Stack gap="inter-section">
                          <Text color="tertiary" as="p">
                            {t("portfolio.holdings.awaitingReconciliation")}
                          </Text>
                          <Text as="label">
                            {t("portfolio.holdings.newWeightLabel")}
                            <br />
                            <input
                              value={reconcileWeightInputs[holding.ticker] ?? ""}
                              onChange={(event) =>
                                setReconcileWeightInputs((current) => ({
                                  ...current,
                                  [holding.ticker]: event.target.value,
                                }))
                              }
                            />
                          </Text>
                          <Button
                            variant="tertiary"
                            onClick={() => submitUpdateHoldingWeight(holding.ticker)}
                            disabled={thisReconcileStatus.kind === "submitting"}
                          >
                            {thisReconcileStatus.kind === "submitting"
                              ? t("portfolio.holdings.updating")
                              : t("portfolio.holdings.updateButton")}
                          </Button>
                          {thisReconcileStatus.kind === "error" && (
                            <Text color="tertiary" role="alert">
                              {thisReconcileStatus.message}
                            </Text>
                          )}
                        </Stack>
                      )}
                      <Button
                        variant="tertiary"
                        onClick={() => openInvestmentCase(holding.ticker, holding.caseId)}
                        disabled={thisCaseCreateStatus.kind === "creating"}
                      >
                        {thisCaseCreateStatus.kind === "creating"
                          ? t("portfolio.holdings.opening")
                          : t("portfolio.holdings.openCaseButton")}
                      </Button>
                      {thisCaseCreateStatus.kind === "error" && (
                        <Text color="tertiary" role="alert">
                          {t("portfolio.holdings.openCaseError")}
                        </Text>
                      )}
                      <Divider tone="hairline" />
                    </div>
                  );
                })}

                {status.view.cashWeightPercent !== null && (
                  <Text color="secondary">
                    {t("portfolio.cashLabel", { percent: status.view.cashWeightPercent })}
                    {status.view.cashValueAbsolute !== null
                      ? ` — ${status.view.cashValueAbsolute}`
                      : ""}
                  </Text>
                )}
                {unallocatedPercent !== null && unallocatedPercent > UNALLOCATED_TOLERANCE && (
                  <Text color="secondary">
                    {t("portfolio.unallocated", {
                      percent: Math.round(unallocatedPercent * 100) / 100,
                    })}
                  </Text>
                )}
                {status.view.concentrationLevel && (
                  <Text color="secondary">
                    {t("portfolio.concentration", {
                      value: CONCENTRATION_LEVEL_KEY[status.view.concentrationLevel]
                        ? t(CONCENTRATION_LEVEL_KEY[status.view.concentrationLevel]!)
                        : status.view.concentrationLevel,
                    })}
                  </Text>
                )}

                <div>
                  <Button variant="tertiary" onClick={() => openInvestmentCase("__new__", null)}>
                    {t("portfolio.openNewCase")}
                  </Button>
                </div>
              </Stack>
            </Surface>
          </Stack>
        )}
      </Stack>
    </Container>
  );
}
