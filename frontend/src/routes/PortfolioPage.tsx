import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";

interface HoldingView {
  ticker: string;
  weightPercent: number;
  valueAbsolute: number | null;
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
}

type Status =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; view: PortfolioView };

type CaseCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "error"; message: string };

/**
 * Portfolio (Alpha Sprint 1A). Shows holdings, allocation percentages,
 * and cash/unallocated when known, and a path from any holding into an
 * Investment Case. No trade recording, no reconciliation UI — both are
 * Sprint 1B (Alpha Sprint 1, Phase 4 revised plan, Decision 3).
 */
export function PortfolioPage() {
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [caseCreateStatus, setCaseCreateStatus] = useState<Record<string, CaseCreateStatus>>({});

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

  function openInvestmentCase(key: string) {
    setCaseCreateStatus((current) => ({ ...current, [key]: { kind: "creating" } }));
    fetch("/api/cases", { method: "POST" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<{ caseId: string }>;
      })
      .then((created) => {
        window.location.assign(`/investment-case/${created.caseId}`);
      })
      .catch((error: unknown) => {
        setCaseCreateStatus((current) => ({
          ...current,
          [key]: {
            kind: "error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

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
                <Button variant="tertiary" onClick={() => openInvestmentCase("__new__")}>
                  Open a new Investment Case
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {status.kind === "loaded" && status.view.exists && status.view.holdings.length > 0 && (
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

              {status.view.holdings.map((holding) => (
                <div key={holding.ticker}>
                  <Text>{holding.ticker}</Text>
                  <Text color="secondary" as="p">
                    {holding.weightPercent}%
                    {holding.valueAbsolute !== null ? ` — ${holding.valueAbsolute}` : ""}
                  </Text>
                  <Button
                    variant="tertiary"
                    onClick={() => openInvestmentCase(holding.ticker)}
                    disabled={caseCreateStatus[holding.ticker]?.kind === "creating"}
                  >
                    {caseCreateStatus[holding.ticker]?.kind === "creating"
                      ? "Opening…"
                      : "Open Investment Case"}
                  </Button>
                  {caseCreateStatus[holding.ticker]?.kind === "error" && (
                    <Text color="tertiary" role="alert">
                      Could not open an Investment Case.
                    </Text>
                  )}
                  <Divider tone="hairline" />
                </div>
              ))}

              {(status.view.cashWeightPercent !== null ||
                status.view.cashValueAbsolute !== null) && (
                <Text color="secondary">
                  Cash: {status.view.cashWeightPercent}%
                  {status.view.cashValueAbsolute !== null
                    ? ` — ${status.view.cashValueAbsolute}`
                    : ""}
                </Text>
              )}
              {status.view.concentrationLevel && (
                <Text color="secondary">Concentration: {status.view.concentrationLevel}</Text>
              )}

              <div>
                <Button variant="tertiary" onClick={() => openInvestmentCase("__new__")}>
                  Open a new Investment Case
                </Button>
              </div>
            </Stack>
          </Surface>
        )}
      </Stack>
    </Container>
  );
}
