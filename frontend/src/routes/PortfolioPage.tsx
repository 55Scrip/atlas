import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";

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
          message: error instanceof Error ? error.message : "Unknown error",
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
            message: error instanceof Error ? error.message : "Unknown error",
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
        [ticker]: { kind: "error", message: "Enter a valid percentage." },
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
            [ticker]: { kind: "error", message: body.detail ?? "Invalid input." },
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
            message: error instanceof Error ? error.message : "Unknown error",
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
      setReplaceStatus({ kind: "error", message: "Every holding needs a valid percentage." });
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
          setReplaceStatus({ kind: "error", message: body.detail ?? "Invalid input." });
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
          message: error instanceof Error ? error.message : "Unknown error",
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
        <Heading level={1}>Portfolio</Heading>

        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            Loading…
          </Text>
        )}
        {status.kind === "error" && (
          <Text color="tertiary" role="alert">
            Could not load your portfolio: {status.message}
          </Text>
        )}

        {status.kind === "loaded" && !status.view.exists && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>No portfolio has been established yet.</Text>
              <RouterLink to="/welcome">Set up your portfolio</RouterLink>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length === 0 && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>Your portfolio is empty.</Text>
              {status.view.objective && <Text color="secondary">Objective: {status.view.objective}</Text>}
              {status.view.horizon && <Text color="secondary">Horizon: {status.view.horizon}</Text>}
              <Text color="secondary">
                There is nothing to show here yet — Atlas does not fabricate holdings or
                opportunities. As you open Investment Cases and record decisions, they will
                appear here.
              </Text>
              <div>
                <Button variant="tertiary" onClick={() => openInvestmentCase("__new__", null)}>
                  Open a new Investment Case
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
                    Trade recorded. Allocation requires reconciliation.
                  </Text>
                  <Text color="secondary">
                    One or more holdings were traded while Atlas only knew percentages, so their
                    allocation was left untouched rather than invented. Update the affected
                    holding below, or replace the entire allocation.
                  </Text>
                  {!showReplaceForm && (
                    <div>
                      <Button variant="tertiary" onClick={openReplaceForm}>
                        Replace entire allocation
                      </Button>
                    </div>
                  )}
                </Stack>
              </Surface>
            )}

            {showReplaceForm && (
              <Surface tier="primary">
                <Stack gap="inter-section">
                  <Heading level={2}>Replace entire allocation</Heading>
                  {replaceRows.map((row, index) => (
                    <Stack key={index} gap="inter-section">
                      <Text as="label">
                        Ticker
                        <br />
                        <input
                          value={row.ticker}
                          onChange={(event) => updateReplaceRow(index, { ticker: event.target.value })}
                        />
                      </Text>
                      <Text as="label">
                        Weight %
                        <br />
                        <input
                          value={row.weightPercent}
                          onChange={(event) =>
                            updateReplaceRow(index, { weightPercent: event.target.value })
                          }
                        />
                      </Text>
                      <Text as="label">
                        Value (optional)
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
                    Cash %
                    <br />
                    <input
                      value={replaceCashWeight}
                      onChange={(event) => setReplaceCashWeight(event.target.value)}
                    />
                  </Text>
                  <Text as="label">
                    Cash value (optional)
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
                      {replaceStatus.kind === "submitting" ? "Saving…" : "Save allocation"}
                    </Button>{" "}
                    <Button variant="tertiary" onClick={() => setShowReplaceForm(false)}>
                      Cancel
                    </Button>
                  </div>
                </Stack>
              </Surface>
            )}

            <Surface tier="primary">
              <Stack gap="inter-section">
                <Heading level={2}>Holdings</Heading>
                {!status.view.hasAbsoluteValues && (
                  <Text color="secondary">
                    Showing percentages only — no absolute portfolio value was entered.
                  </Text>
                )}
                {status.view.hasAbsoluteValues && status.view.totalValue !== null && (
                  <Text color="secondary">Total value: {status.view.totalValue}</Text>
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
                          Updated automatically
                        </Text>
                      )}
                      {holding.reconciliationStatus === "AWAITING_RECONCILIATION" && (
                        <Stack gap="inter-section">
                          <Text color="tertiary" as="p">
                            Awaiting reconciliation
                          </Text>
                          <Text as="label">
                            New weight %
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
                              ? "Updating…"
                              : "Update this holding"}
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
                          ? "Opening…"
                          : "Open Investment Case"}
                      </Button>
                      {thisCaseCreateStatus.kind === "error" && (
                        <Text color="tertiary" role="alert">
                          Could not open an Investment Case.
                        </Text>
                      )}
                      <Divider tone="hairline" />
                    </div>
                  );
                })}

                {status.view.cashWeightPercent !== null && (
                  <Text color="secondary">
                    Cash: {status.view.cashWeightPercent}%
                    {status.view.cashValueAbsolute !== null
                      ? ` — ${status.view.cashValueAbsolute}`
                      : ""}
                  </Text>
                )}
                {unallocatedPercent !== null && unallocatedPercent > UNALLOCATED_TOLERANCE && (
                  <Text color="secondary">
                    Unallocated: {Math.round(unallocatedPercent * 100) / 100}% — this portfolio
                    does not yet account for 100% of holdings; Atlas does not invent the
                    remainder.
                  </Text>
                )}
                {status.view.concentrationLevel && (
                  <Text color="secondary">Concentration: {status.view.concentrationLevel}</Text>
                )}

                <div>
                  <Button variant="tertiary" onClick={() => openInvestmentCase("__new__", null)}>
                    Open a new Investment Case
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
