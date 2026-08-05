import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";

type Step = "choice" | "import" | "scratch";

interface HoldingRow {
  ticker: string;
  weightPercent: string;
  valueAbsolute: string;
}

const EMPTY_ROW: HoldingRow = { ticker: "", weightPercent: "", valueAbsolute: "" };

type SubmitStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

/**
 * First-Time Experience (Alpha Sprint 1A): the path choice, the manual
 * existing-portfolio entry flow, and the from-scratch entry flow. Both
 * flows land on `/portfolio`. No import mechanism beyond manual entry
 * exists — no file import, no screenshot parsing, no broker connection
 * (explicitly deferred, Alpha Sprint 1 Phase 4).
 */
export function WelcomePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("choice");

  const [rows, setRows] = useState<HoldingRow[]>([{ ...EMPTY_ROW }]);
  const [cashWeightPercent, setCashWeightPercent] = useState("");
  const [cashValueAbsolute, setCashValueAbsolute] = useState("");
  const [importPreferences, setImportPreferences] = useState("");
  const [importStatus, setImportStatus] = useState<SubmitStatus>({ kind: "idle" });

  const [objective, setObjective] = useState("");
  const [horizon, setHorizon] = useState("");
  const [scratchPreferences, setScratchPreferences] = useState("");
  const [scratchStatus, setScratchStatus] = useState<SubmitStatus>({ kind: "idle" });

  function updateRow(index: number, patch: Partial<HoldingRow>) {
    setRows((current) => current.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function addRow() {
    setRows((current) => [...current, { ...EMPTY_ROW }]);
  }

  function removeRow(index: number) {
    setRows((current) => current.filter((_, i) => i !== index));
  }

  function submitImport() {
    const holdings = rows
      .filter((row) => row.ticker.trim() !== "")
      .map((row) => ({
        ticker: row.ticker.trim(),
        weightPercent: Number.parseFloat(row.weightPercent),
        valueAbsolute:
          row.valueAbsolute.trim() === "" ? null : Number.parseFloat(row.valueAbsolute),
      }));

    if (holdings.length === 0) {
      setImportStatus({ kind: "validation-error", message: "Enter at least one holding." });
      return;
    }
    if (holdings.some((holding) => Number.isNaN(holding.weightPercent))) {
      setImportStatus({
        kind: "validation-error",
        message: "Every holding needs a percentage.",
      });
      return;
    }

    setImportStatus({ kind: "submitting" });
    fetch("/api/alpha-portfolio/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        holdings,
        cashWeightPercent:
          cashWeightPercent.trim() === "" ? null : Number.parseFloat(cashWeightPercent),
        cashValueAbsolute:
          cashValueAbsolute.trim() === "" ? null : Number.parseFloat(cashValueAbsolute),
        preferencesNotes: importPreferences.trim() === "" ? null : importPreferences.trim(),
      }),
    })
      .then(async (response) => {
        if (response.status === 400) {
          const body = (await response.json()) as { detail?: string };
          setImportStatus({ kind: "validation-error", message: body.detail ?? "Invalid input." });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        navigate("/portfolio");
      })
      .catch((error: unknown) => {
        setImportStatus({
          kind: "api-error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });
  }

  function submitScratch() {
    if (objective.trim() === "" || horizon.trim() === "") {
      setScratchStatus({
        kind: "validation-error",
        message: "Objective and horizon are both required.",
      });
      return;
    }

    setScratchStatus({ kind: "submitting" });
    fetch("/api/alpha-portfolio/from-scratch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        objective: objective.trim(),
        horizon: horizon.trim(),
        preferencesNotes: scratchPreferences.trim() === "" ? null : scratchPreferences.trim(),
      }),
    })
      .then(async (response) => {
        if (response.status === 400) {
          const body = (await response.json()) as { detail?: string };
          setScratchStatus({
            kind: "validation-error",
            message: body.detail ?? "Invalid input.",
          });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        navigate("/portfolio");
      })
      .catch((error: unknown) => {
        setScratchStatus({
          kind: "api-error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });
  }

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>Welcome to Atlas</Heading>

        {step === "choice" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>How would you like to begin?</Text>
              <div>
                <Button variant="primary" onClick={() => setStep("import")}>
                  I have an existing portfolio
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setStep("scratch")}>
                  Start from scratch
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {step === "import" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>Your existing portfolio</Heading>
              <Text color="secondary">
                Enter each holding as a percentage of your portfolio. Exact values are optional.
              </Text>

              {rows.map((row, index) => (
                <Stack key={index} gap="inter-section">
                  <Text as="label">
                    Ticker
                    <br />
                    <input
                      value={row.ticker}
                      onChange={(event) => updateRow(index, { ticker: event.target.value })}
                    />
                  </Text>
                  <Text as="label">
                    Weight %
                    <br />
                    <input
                      value={row.weightPercent}
                      onChange={(event) =>
                        updateRow(index, { weightPercent: event.target.value })
                      }
                    />
                  </Text>
                  <Text as="label">
                    Value (optional)
                    <br />
                    <input
                      value={row.valueAbsolute}
                      onChange={(event) =>
                        updateRow(index, { valueAbsolute: event.target.value })
                      }
                    />
                  </Text>
                  {rows.length > 1 && (
                    <Button variant="tertiary" onClick={() => removeRow(index)}>
                      Remove
                    </Button>
                  )}
                  <Divider tone="hairline" />
                </Stack>
              ))}

              <div>
                <Button variant="tertiary" onClick={addRow}>
                  + Add holding
                </Button>
              </div>

              <Text as="label">
                Cash %
                <br />
                <input
                  value={cashWeightPercent}
                  onChange={(event) => setCashWeightPercent(event.target.value)}
                />
              </Text>
              <Text as="label">
                Cash value (optional)
                <br />
                <input
                  value={cashValueAbsolute}
                  onChange={(event) => setCashValueAbsolute(event.target.value)}
                />
              </Text>

              <Text as="label">
                Preferences (optional)
                <br />
                <textarea
                  value={importPreferences}
                  onChange={(event) => setImportPreferences(event.target.value)}
                />
              </Text>

              {importStatus.kind === "validation-error" && (
                <Text color="tertiary" role="alert">
                  {importStatus.message}
                </Text>
              )}
              {importStatus.kind === "api-error" && (
                <Text color="tertiary" role="alert">
                  Could not save this portfolio: {importStatus.message}
                </Text>
              )}

              <div>
                <Button
                  variant="primary"
                  onClick={submitImport}
                  disabled={importStatus.kind === "submitting"}
                >
                  {importStatus.kind === "submitting" ? "Saving…" : "Continue to Portfolio"}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setStep("choice")}>
                  Back
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {step === "scratch" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>Starting from scratch</Heading>
              <Text as="label">
                Investment objective
                <br />
                <input value={objective} onChange={(event) => setObjective(event.target.value)} />
              </Text>
              <Text as="label">
                Investment horizon
                <br />
                <input value={horizon} onChange={(event) => setHorizon(event.target.value)} />
              </Text>
              <Text as="label">
                Preferences (optional)
                <br />
                <textarea
                  value={scratchPreferences}
                  onChange={(event) => setScratchPreferences(event.target.value)}
                />
              </Text>

              {scratchStatus.kind === "validation-error" && (
                <Text color="tertiary" role="alert">
                  {scratchStatus.message}
                </Text>
              )}
              {scratchStatus.kind === "api-error" && (
                <Text color="tertiary" role="alert">
                  Could not save: {scratchStatus.message}
                </Text>
              )}

              <div>
                <Button
                  variant="primary"
                  onClick={submitScratch}
                  disabled={scratchStatus.kind === "submitting"}
                >
                  {scratchStatus.kind === "submitting" ? "Saving…" : "Continue to Portfolio"}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setStep("choice")}>
                  Back
                </Button>
              </div>
            </Stack>
          </Surface>
        )}
      </Stack>
    </Container>
  );
}
