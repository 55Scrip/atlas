import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { parsePortfolioText } from "../portfolio-import/parser";
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
  "missing-ticker": "portfolioImport.error.missingTicker",
  "missing-value": "portfolioImport.error.missingValue",
  "invalid-value": "portfolioImport.error.invalidValue",
  "non-positive-value": "portfolioImport.error.nonPositiveValue",
  "duplicate-ticker": "portfolioImport.error.duplicateTicker",
  "too-many-columns": "portfolioImport.error.tooManyColumns",
};

/**
 * Portfolio Import v1.
 *
 * Input → Parse → Validate → Preview → Confirm → Persist. The raw
 * pasted text never reaches the backend directly — only
 * `ParseResult.validHoldings`, and only after the investor has seen
 * every row (valid or not) and confirmed. Confirmation is disabled
 * while any parse error remains (`parseResult.errorCount > 0`).
 *
 * Data-model decision, made after reading `atlas/alpha/portfolio/`
 * directly rather than from memory: `AlphaHolding` has only
 * `weight_percent` (required) and `value_absolute` (optional) — no
 * `quantity`/`shares` field exists anywhere in the backend. So the
 * parsed numeric column is always labelled "Weight %", never
 * "Shares" — the smallest honest representation, per this sprint's
 * own explicit fallback guidance, rather than inventing a quantity
 * concept the backend cannot truthfully persist.
 *
 * Replace vs merge: when a portfolio already exists, this reuses
 * `POST /alpha-portfolio/reconcile` (`mode: REPLACE_ALLOCATION`) —
 * the one existing service method that already preserves `case_id`
 * for any ticker still present after the replace
 * (`AlphaPortfolioService.reconcile_replace_allocation`, verified by
 * direct code read). `POST /alpha-portfolio/import` is used only for
 * a brand-new portfolio, where there is no existing `case_id` to
 * preserve. No backend code was changed for this sprint — both
 * endpoints, and the case-preservation behavior, already existed.
 *
 * Cash is never invented: for a fresh import there is none to carry
 * forward (matches "never infer cash"); for a replace, the investor's
 * already-recorded cash figures are passed through unchanged rather
 * than silently cleared, since the pasted text never mentions cash at
 * all and clearing a real, previously-entered figure as a side effect
 * of importing holdings would itself be a kind of fabrication (an
 * uninitiated, unintended change).
 */
export function PortfolioImportPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>("paste");
  const [rawText, setRawText] = useState("");
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
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

  function goToReview() {
    if (rawText.trim() === "") return;
    setParseResult(parsePortfolioText(rawText));
    setSubmitStatus({ kind: "idle" });
    setStep("review");
  }

  function backToEdit() {
    setStep("paste");
  }

  function confirmImport() {
    if (!parseResult || parseResult.errorCount > 0 || parseResult.validHoldings.length === 0) return;
    if (snapshotStatus.kind !== "loaded") return;

    setSubmitStatus({ kind: "submitting" });
    const holdings = parseResult.validHoldings.map((h) => ({
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

  const canConfirm =
    parseResult !== null &&
    parseResult.errorCount === 0 &&
    parseResult.validHoldings.length > 0 &&
    snapshotStatus.kind === "loaded";

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

        {step === "review" && parseResult && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("portfolioImport.review.heading")}</Heading>

              {parseResult.validHoldings.length > 0 && (
                <Stack gap="inter-section">
                  <Text>
                    {t("portfolioImport.review.holdingsFound", {
                      count: parseResult.validHoldings.length,
                    })}
                  </Text>
                  <Stack gap="inter-section">
                    {parseResult.validHoldings.map((holding) => (
                      <Text key={holding.ticker} color="secondary" as="p">
                        {holding.ticker} — {holding.weightPercent}% ({t("portfolioImport.review.weightPercentLabel")})
                      </Text>
                    ))}
                  </Stack>
                </Stack>
              )}

              {parseResult.errorCount > 0 && (
                <Stack gap="inter-section">
                  <Text color="tertiary" role="alert">
                    {t("portfolioImport.review.errorsHeading", { count: parseResult.errorCount })}
                  </Text>
                  <Stack gap="inter-section">
                    {parseResult.rows
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

              {parseResult.validHoldings.length === 0 && parseResult.errorCount === 0 && (
                <Text color="secondary">{t("portfolioImport.review.noHoldingsFound")}</Text>
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
