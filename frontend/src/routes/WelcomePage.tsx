import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { invalidateAlphaPortfolio } from "../portfolio/alphaPortfolioData";

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
  const { t } = useTranslation();
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
    const rawRows = rows.filter((row) => row.ticker.trim() !== "");

    if (rawRows.length === 0) {
      setImportStatus({ kind: "validation-error", message: t("welcome.import.errors.noHoldings") });
      return;
    }

    for (const row of rawRows) {
      if (Number.isNaN(Number.parseFloat(row.weightPercent))) {
        setImportStatus({
          kind: "validation-error",
          message: t("welcome.import.errors.missingPercentage"),
        });
        return;
      }
      if (row.valueAbsolute.trim() !== "" && Number.isNaN(Number.parseFloat(row.valueAbsolute))) {
        setImportStatus({
          kind: "validation-error",
          message: t("welcome.import.errors.invalidValueFor", {
            value: row.valueAbsolute,
            ticker: row.ticker.trim(),
          }),
        });
        return;
      }
    }

    const normalizedTickers = rawRows.map((row) => row.ticker.trim().toUpperCase());
    const duplicateTickers = [
      ...new Set(
        normalizedTickers.filter((ticker, index) => normalizedTickers.indexOf(ticker) !== index),
      ),
    ];
    if (duplicateTickers.length > 0) {
      setImportStatus({
        kind: "validation-error",
        message: t("welcome.import.errors.duplicateTickers", {
          tickers: duplicateTickers.join(", "),
        }),
      });
      return;
    }

    if (cashWeightPercent.trim() !== "" && Number.isNaN(Number.parseFloat(cashWeightPercent))) {
      setImportStatus({
        kind: "validation-error",
        message: t("welcome.import.errors.invalidCashPercent", { value: cashWeightPercent }),
      });
      return;
    }
    if (cashValueAbsolute.trim() !== "" && Number.isNaN(Number.parseFloat(cashValueAbsolute))) {
      setImportStatus({
        kind: "validation-error",
        message: t("welcome.import.errors.invalidCashValue", { value: cashValueAbsolute }),
      });
      return;
    }
    if ((cashWeightPercent.trim() !== "") !== (cashValueAbsolute.trim() !== "")) {
      setImportStatus({
        kind: "validation-error",
        message: t("welcome.import.errors.cashBothOrNeither"),
      });
      return;
    }

    const holdings = rawRows.map((row) => ({
      ticker: row.ticker.trim(),
      weightPercent: Number.parseFloat(row.weightPercent),
      valueAbsolute: row.valueAbsolute.trim() === "" ? null : Number.parseFloat(row.valueAbsolute),
    }));

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
          setImportStatus({
            kind: "validation-error",
            message: body.detail ?? t("common.invalidInput"),
          });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        invalidateAlphaPortfolio();
        navigate("/portfolio");
      })
      .catch((error: unknown) => {
        setImportStatus({
          kind: "api-error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  function submitScratch() {
    if (objective.trim() === "" || horizon.trim() === "") {
      setScratchStatus({
        kind: "validation-error",
        message: t("welcome.scratch.errors.required"),
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
            message: body.detail ?? t("common.invalidInput"),
          });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        invalidateAlphaPortfolio();
        navigate("/portfolio");
      })
      .catch((error: unknown) => {
        setScratchStatus({
          kind: "api-error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("welcome.title")}</Heading>

        {step === "choice" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>{t("welcome.choice.prompt")}</Text>
              <div>
                <Button variant="primary" onClick={() => setStep("import")}>
                  {t("welcome.choice.haveExisting")}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setStep("scratch")}>
                  {t("welcome.choice.startFromScratch")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {step === "import" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("welcome.import.heading")}</Heading>
              <Text color="secondary">{t("welcome.import.instructions")}</Text>

              {rows.map((row, index) => (
                <Stack key={index} gap="inter-section">
                  <Text as="label">
                    {t("form.ticker")}
                    <br />
                    <input
                      value={row.ticker}
                      onChange={(event) => updateRow(index, { ticker: event.target.value })}
                    />
                  </Text>
                  <Text as="label">
                    {t("form.weightPercent")}
                    <br />
                    <input
                      value={row.weightPercent}
                      onChange={(event) =>
                        updateRow(index, { weightPercent: event.target.value })
                      }
                    />
                  </Text>
                  <Text as="label">
                    {t("form.valueOptional")}
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
                      {t("form.removeButton")}
                    </Button>
                  )}
                  <Divider tone="hairline" />
                </Stack>
              ))}

              <div>
                <Button variant="tertiary" onClick={addRow}>
                  {t("welcome.import.addHoldingButton")}
                </Button>
              </div>

              <Text as="label">
                {t("form.cashPercent")}
                <br />
                <input
                  value={cashWeightPercent}
                  onChange={(event) => setCashWeightPercent(event.target.value)}
                />
              </Text>
              <Text as="label">
                {t("form.cashValueOptional")}
                <br />
                <input
                  value={cashValueAbsolute}
                  onChange={(event) => setCashValueAbsolute(event.target.value)}
                />
              </Text>

              <Text as="label">
                {t("form.preferencesOptional")}
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
                  {t("welcome.import.errors.saveFailed", { message: importStatus.message })}
                </Text>
              )}

              <div>
                <Button
                  variant="primary"
                  onClick={submitImport}
                  disabled={importStatus.kind === "submitting"}
                >
                  {importStatus.kind === "submitting" ? t("common.saving") : t("welcome.continueButton")}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setStep("choice")}>
                  {t("welcome.backButton")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {step === "scratch" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("welcome.scratch.heading")}</Heading>
              <Text as="label">
                {t("welcome.scratch.objectiveLabel")}
                <br />
                <input value={objective} onChange={(event) => setObjective(event.target.value)} />
              </Text>
              <Text as="label">
                {t("welcome.scratch.horizonLabel")}
                <br />
                <input value={horizon} onChange={(event) => setHorizon(event.target.value)} />
              </Text>
              <Text as="label">
                {t("form.preferencesOptional")}
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
                  {t("welcome.scratch.errors.saveFailed", { message: scratchStatus.message })}
                </Text>
              )}

              <div>
                <Button
                  variant="primary"
                  onClick={submitScratch}
                  disabled={scratchStatus.kind === "submitting"}
                >
                  {scratchStatus.kind === "submitting" ? t("common.saving") : t("welcome.continueButton")}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setStep("choice")}>
                  {t("welcome.backButton")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}
      </Stack>
    </Container>
  );
}
