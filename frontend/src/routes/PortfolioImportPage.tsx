import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import type { InstrumentType } from "../portfolio-import/instrumentRegistry";
import { parsePortfolioText } from "../portfolio-import/parser";
import { reconcileRows } from "../portfolio-import/resolution";
import type { ImportRowErrorCode, ParseResult } from "../portfolio-import/types";

type Step = "paste" | "review";

interface PortfolioSnapshot {
  exists: boolean;
  cashWeightPercent: number | null;
  cashValueAbsolute: number | null;
}

type SnapshotStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; view: PortfolioSnapshot };

type SubmitStatus = { kind: "idle" } | { kind: "submitting" } | { kind: "error"; message: string };

const ERROR_LABEL_KEY: Record<ImportRowErrorCode, TranslationKey> = {
  "missing-name": "portfolioImport.error.missingName",
  "missing-value": "portfolioImport.error.missingValue",
  "invalid-value": "portfolioImport.error.invalidValue",
  "non-positive-value": "portfolioImport.error.nonPositiveValue",
  "duplicate-ticker": "portfolioImport.error.duplicateTicker",
  "too-many-columns": "portfolioImport.error.tooManyColumns",
};

const INSTRUMENT_TYPE_LABEL_KEY: Record<InstrumentType, TranslationKey> = {
  equity: "portfolioImport.instrumentType.equity",
  fund: "portfolioImport.instrumentType.fund",
  etp: "portfolioImport.instrumentType.etp",
  private: "portfolioImport.instrumentType.private",
  other: "portfolioImport.instrumentType.other",
};

/**
 * Portfolio Import v1.2.
 *
 * Input → Parse → Resolve (registry, explicit ticker, or manual
 * confirmation) → Preview → Confirm → Persist. The raw pasted text
 * never reaches the backend directly — only `ReconcileResult
 * .readyHoldings`, and only once every row the investor pasted either
 * resolved to a ticker automatically or was manually confirmed, with
 * no parse errors and no duplicate tickers remaining
 * (`reconcileRows`'s `canImport`).
 *
 * v1.2's hardening pass: a name only auto-resolves through an exact
 * hit in the maintained registry (`portfolio-import
 * /instrumentRegistry.ts`) or by being pasted already in the all-caps
 * shape of a literal ticker ("AMD", "BRK.B") — never by a company name
 * merely *resembling* a ticker ("Volvo" is 5 letters, same shape as a
 * real ticker, but Title Case; it is never guessed at). A registry hit
 * with no ticker (a fund, ETP, or private company) surfaces as
 * "recognized instrument — needs confirmation," never a fabricated
 * stock ticker. Everything else is shown as "needs confirmation" until
 * a human resolves it. No fuzzy matching anywhere in this path.
 *
 * Data-model decision, unchanged since v1 (verified again directly
 * against `atlas/alpha/portfolio/` before this sprint): `AlphaHolding`
 * has only `weight_percent` (required) and `value_absolute` (optional)
 * — no `quantity`/`shares` field exists anywhere in the backend, and
 * nothing here can persist an instrument as anything other than a
 * plain ticker + weight. The parsed numeric column is always labelled
 * "Weight %".
 *
 * Replace vs merge, cash handling, and the fresh-import vs
 * reconcile-replace endpoint routing are all unchanged from v1 — no
 * backend code was touched for this sprint.
 */
export function PortfolioImportPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>("paste");
  const [rawText, setRawText] = useState("");
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [manualTickers, setManualTickers] = useState<Record<number, string>>({});
  const [snapshotStatus, setSnapshotStatus] = useState<SnapshotStatus>({ kind: "loading" });
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioSnapshot>;
      })
      .then((view) => setSnapshotStatus({ kind: "loaded", view }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setSnapshotStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  const reconciled = useMemo(
    () => (parseResult ? reconcileRows(parseResult.rows, manualTickers) : null),
    [parseResult, manualTickers],
  );

  function goToReview() {
    if (rawText.trim() === "") return;
    setParseResult(parsePortfolioText(rawText));
    setManualTickers({});
    setSubmitStatus({ kind: "idle" });
    setStep("review");
  }

  function backToEdit() {
    setStep("paste");
  }

  function setManualTicker(lineNumber: number, value: string) {
    setManualTickers((prev) => ({ ...prev, [lineNumber]: value }));
  }

  function confirmImport() {
    if (!reconciled || !reconciled.canImport) return;
    if (snapshotStatus.kind !== "loaded") return;

    setSubmitStatus({ kind: "submitting" });
    const holdings = reconciled.readyHoldings.map((h) => ({
      ticker: h.ticker,
      weightPercent: h.weightPercent,
    }));

    const isReplace = snapshotStatus.view.exists;
    const endpoint = isReplace ? "/api/alpha-portfolio/reconcile" : "/api/alpha-portfolio/import";
    const body = isReplace
      ? {
          mode: "REPLACE_ALLOCATION",
          holdings,
          cashWeightPercent: snapshotStatus.view.cashWeightPercent,
          cashValueAbsolute: snapshotStatus.view.cashValueAbsolute,
        }
      : { holdings, cashWeightPercent: null, cashValueAbsolute: null, preferencesNotes: null };

    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const errorBody = (await response.json()) as { detail?: string };
          setSubmitStatus({
            kind: "error",
            message: errorBody.detail ?? t("common.invalidInput"),
          });
          return null;
        }
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json();
      })
      .then((result) => {
        if (result) navigate("/portfolio");
      })
      .catch((error: unknown) => {
        setSubmitStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
  }

  const canConfirm = reconciled !== null && reconciled.canImport && snapshotStatus.kind === "loaded";

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("portfolioImport.title")}</Heading>

        <Divider />

        {step === "paste" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("portfolioImport.paste.heading")}</Heading>
              <Text color="secondary">{t("portfolioImport.paste.instructions")}</Text>
              <Text as="label">
                <textarea
                  value={rawText}
                  onChange={(event) => setRawText(event.target.value)}
                  placeholder={t("portfolioImport.paste.placeholder")}
                  rows={10}
                  style={{ width: "100%", fontFamily: "monospace" }}
                />
              </Text>
              <Text color="tertiary">{t("portfolioImport.paste.reviewNote")}</Text>
              <div>
                <Button variant="primary" onClick={goToReview} disabled={rawText.trim() === ""}>
                  {t("portfolioImport.paste.continueButton")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {step === "review" && reconciled && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("portfolioImport.review.heading")}</Heading>

              {reconciled.rows.filter((row) => row.errorCode === null).length > 0 && (
                <Stack gap="inter-section">
                  <Text>
                    {t("portfolioImport.review.holdingsFound", {
                      count: reconciled.rows.filter((row) => row.errorCode === null).length,
                    })}
                  </Text>
                  <Stack gap="intra-section">
                    {reconciled.rows
                      .filter((row) => row.errorCode === null)
                      .map((row) => {
                        const isUnsupported = row.ticker === null && row.mappingStatus === "unsupported";
                        return (
                        <Surface key={row.lineNumber} tier="elevated">
                          <Stack gap="metadata">
                            <Inline gap="row" align="center" wrap>
                              <Text as="p">{row.originalName}</Text>
                              <Text color="secondary" as="p">
                                {row.ticker ?? "?"}
                              </Text>
                              {row.ticker ? (
                                <Text as="p" aria-label={t("portfolioImport.review.resolved")}>
                                  {"✓"}
                                </Text>
                              ) : isUnsupported ? (
                                <Text color="tertiary" as="p" role="status">
                                  {"! " + t("portfolioImport.review.recognizedUnsupported")}
                                </Text>
                              ) : (
                                <Text color="tertiary" as="p" role="status">
                                  {t("portfolioImport.review.needsConfirmation")}
                                </Text>
                              )}
                              {isUnsupported && row.instrumentType && (
                                <Text color="tertiary" as="p">
                                  {t(INSTRUMENT_TYPE_LABEL_KEY[row.instrumentType])}
                                </Text>
                              )}
                              <Text as="p">{row.weightPercent}%</Text>
                              {!row.ticker && (
                                <Text as="label">
                                  <input
                                    type="text"
                                    value={manualTickers[row.lineNumber] ?? ""}
                                    onChange={(event) => setManualTicker(row.lineNumber, event.target.value)}
                                    placeholder={t("portfolioImport.review.manualTickerPlaceholder")}
                                    aria-label={t("portfolioImport.review.manualTickerPlaceholder")}
                                    style={{ fontFamily: "monospace", width: "8ch" }}
                                  />
                                </Text>
                              )}
                            </Inline>
                            {isUnsupported && (
                              <Text color="tertiary" as="p">
                                {t("portfolioImport.review.unsupportedManualWarning", {
                                  instrumentType: row.instrumentType
                                    ? t(INSTRUMENT_TYPE_LABEL_KEY[row.instrumentType])
                                    : "",
                                })}
                              </Text>
                            )}
                          </Stack>
                        </Surface>
                        );
                      })}
                  </Stack>
                </Stack>
              )}

              {reconciled.errorCount > 0 && (
                <Stack gap="inter-section">
                  <Text color="tertiary" role="alert">
                    {t("portfolioImport.review.errorsHeading", { count: reconciled.errorCount })}
                  </Text>
                  <Stack gap="inter-section">
                    {reconciled.rows
                      .filter((row) => row.errorCode !== null)
                      .map((row) => (
                        <Text key={row.lineNumber} color="tertiary" as="p">
                          {t("portfolioImport.review.lineError", {
                            line: row.lineNumber,
                            error: row.errorCode
                              ? t(ERROR_LABEL_KEY[row.errorCode], { ticker: row.ticker ?? "" })
                              : "",
                          })}
                        </Text>
                      ))}
                  </Stack>
                </Stack>
              )}

              {reconciled.rows.length === 0 && (
                <Text color="secondary">{t("portfolioImport.review.noHoldingsFound")}</Text>
              )}

              {reconciled.needsConfirmationCount > 0 && (
                <Text color="tertiary">
                  {t("portfolioImport.review.confirmationRequired", {
                    count: reconciled.needsConfirmationCount,
                  })}
                </Text>
              )}

              {snapshotStatus.kind === "loaded" && snapshotStatus.view.exists && (
                <Text color="tertiary">{t("portfolioImport.review.replaceWarning")}</Text>
              )}

              {submitStatus.kind === "error" && (
                <Text color="tertiary" role="alert">
                  {t("portfolioImport.review.submitError", { message: submitStatus.message })}
                </Text>
              )}

              <div>
                <Button
                  variant="primary"
                  onClick={confirmImport}
                  disabled={!canConfirm || submitStatus.kind === "submitting"}
                >
                  {submitStatus.kind === "submitting" ? t("common.submitting") : t("portfolioImport.title")}
                </Button>{" "}
                <Button variant="tertiary" onClick={backToEdit} disabled={submitStatus.kind === "submitting"}>
                  {t("portfolioImport.review.backButton")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}
      </Stack>
    </Container>
  );
}
