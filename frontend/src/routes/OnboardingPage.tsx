import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Link, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { invalidateAlphaPortfolio, useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import {
  BackendError,
  confirmImport,
  fetchEnrichmentProgress,
  previewImport,
  toConfirmHolding,
  type EnrichmentProgress,
  type ImportPreview,
  type ParsedHoldingRow,
} from "../portfolio-import/importApi";

/**
 * Zero-Effort Portfolio Onboarding -- the single unified entry point,
 * replacing the old `WelcomePage` (manual rows, no resolution) and
 * `PortfolioImportPage` (paste-only, 2-column parser). Every entry
 * method funnels into the same backend preview pipeline
 * (`atlas.alpha.portfolio_import`); this component never parses or
 * resolves a ticker itself.
 *
 * Mounted at both `/welcome` (no portfolio yet) and `/portfolio/import`
 * (replace an existing one) -- `portfolioExists` is the only thing that
 * changes between those two contexts (which confirm endpoint is called,
 * and whether a replace warning is shown).
 */

type EntryMethod = "avanza" | "nordnet" | "paste";
type Screen =
  | "choose"
  | "text"
  | "manual"
  | "scratch"
  | "loading-preview"
  | "review"
  | "confirming"
  | "progress";

interface ManualRow {
  company: string;
  quantity: string;
  price: string;
}

const EMPTY_MANUAL_ROW: ManualRow = { company: "", quantity: "", price: "" };
const MIN_MANUAL_TICKER_LENGTH = 2;

const INPUT_INSTRUCTIONS_KEY: Record<EntryMethod, TranslationKey> = {
  avanza: "onboarding.input.instructionsAvanza",
  nordnet: "onboarding.input.instructionsNordnet",
  paste: "onboarding.input.instructionsPaste",
};

/** Rows that genuinely need the investor's input -- a candidate pick or
 * a manual ticker. Every other non-resolved status (UNSUPPORTED, ERROR,
 * DUPLICATE) is informational only: Atlas already knows the outcome and
 * there's nothing to ask, so it's shown as a reason, never a form field
 * (Real Avanza Import Fix, Phase 4/8). */
function needsAttention(row: ParsedHoldingRow): boolean {
  return row.status === "AMBIGUOUS" || row.status === "UNRESOLVED";
}

function isInformationalExclusion(row: ParsedHoldingRow): boolean {
  return row.status === "UNSUPPORTED" || row.status === "ERROR" || row.status === "DUPLICATE";
}

/** Real Avanza Import Fix (Phase 7): backend validation strings must
 * never reach the UI verbatim -- always a translated, calm message.
 * The raw detail still goes to the console for debugging. */
function describeError(error: unknown, t: (key: TranslationKey) => string): string {
  if (error instanceof BackendError) {
    console.error("Atlas backend error:", error.detail);
    return t("onboarding.review.errors.submitFailed");
  }
  return t("common.unknownError");
}

export function OnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const portfolioResource = useAlphaPortfolio();
  const portfolioExists =
    portfolioResource.kind === "loaded" && (portfolioResource.data as { exists: boolean }).exists;

  const [screen, setScreen] = useState<Screen>("choose");
  const [entryMethod, setEntryMethod] = useState<EntryMethod>("paste");
  const [rawText, setRawText] = useState("");
  const [manualRows, setManualRows] = useState<ManualRow[]>([{ ...EMPTY_MANUAL_ROW }]);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [overrides, setOverrides] = useState<Record<number, string>>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [objective, setObjective] = useState("");
  const [horizon, setHorizon] = useState("");
  const [scratchSubmitting, setScratchSubmitting] = useState(false);
  const [scratchError, setScratchError] = useState<string | null>(null);

  const [batchId, setBatchId] = useState<string | null>(null);
  const [holdingsIdentifiedCount, setHoldingsIdentifiedCount] = useState(0);
  const [progress, setProgress] = useState<EnrichmentProgress | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (screen !== "progress" || !batchId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    async function poll() {
      try {
        const result = await fetchEnrichmentProgress(batchId as string);
        if (cancelled) return;
        setProgress(result);
        if (!result.complete) timer = setTimeout(poll, 2500);
      } catch {
        if (!cancelled) timer = setTimeout(poll, 2500);
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [screen, batchId]);

  async function runPreview(text: string) {
    if (text.trim() === "") return;
    setErrorMessage(null);
    setScreen("loading-preview");
    try {
      const result = await previewImport(text);
      setPreview(result);
      setOverrides({});
      if (result.rows.length === 0) {
        setErrorMessage(t("onboarding.review.noHoldingsFound"));
        setScreen("text");
        return;
      }
      if (!result.needsReview) {
        await runConfirm(result, {});
      } else {
        setScreen("review");
      }
    } catch (error) {
      setErrorMessage(describeError(error, t));
      setScreen("text");
    }
  }

  async function runConfirm(previewToUse: ImportPreview, overridesToUse: Record<number, string>) {
    setScreen("confirming");
    setErrorMessage(null);
    const holdings = previewToUse.rows
      .filter((row) => row.status === "RESOLVED" || overridesToUse[row.lineNumber])
      .map((row) => toConfirmHolding(row, overridesToUse[row.lineNumber]));

    if (holdings.length === 0) {
      setErrorMessage(t("onboarding.review.errors.nothingToImport"));
      setScreen("review");
      return;
    }

    try {
      const result = await confirmImport(holdings, portfolioExists);
      invalidateAlphaPortfolio();
      setHoldingsIdentifiedCount(holdings.length);
      if (result.batchId) {
        setBatchId(result.batchId);
        setScreen("progress");
      } else {
        navigate("/portfolio");
      }
    } catch (error) {
      setErrorMessage(describeError(error, t));
      setScreen("review");
    }
  }

  function chooseTextMethod(method: EntryMethod) {
    setEntryMethod(method);
    setRawText("");
    setErrorMessage(null);
    setScreen("text");
  }

  function handleFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === "string" ? reader.result : "";
      void runPreview(text);
    };
    reader.onerror = () => setErrorMessage(t("onboarding.csv.readError"));
    reader.readAsText(file);
  }

  function updateManualRow(index: number, patch: Partial<ManualRow>) {
    setManualRows((current) => current.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function addManualRow() {
    setManualRows((current) => [...current, { ...EMPTY_MANUAL_ROW }]);
  }

  function removeManualRow(index: number) {
    setManualRows((current) => current.filter((_, i) => i !== index));
  }

  function submitManualRows() {
    const lines = ["Company,Quantity,Price"];
    for (const row of manualRows) {
      if (row.company.trim() === "") continue;
      lines.push(`${row.company.trim()},${row.quantity.trim()},${row.price.trim()}`);
    }
    void runPreview(lines.join("\n"));
  }

  function submitScratch() {
    if (objective.trim() === "" || horizon.trim() === "") {
      setScratchError(t("onboarding.scratch.errors.required"));
      return;
    }
    setScratchSubmitting(true);
    setScratchError(null);
    fetch("/api/alpha-portfolio/from-scratch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ objective: objective.trim(), horizon: horizon.trim(), preferencesNotes: null }),
    })
      .then(async (response) => {
        if (response.status === 400) {
          const body = (await response.json()) as { detail?: string };
          console.error("Atlas backend error:", body.detail);
          setScratchError(t("common.invalidInput"));
          return;
        }
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        invalidateAlphaPortfolio();
        navigate("/portfolio");
      })
      .catch(() => {
        setScratchError(t("onboarding.scratch.errors.saveFailed"));
      })
      .finally(() => setScratchSubmitting(false));
  }

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("onboarding.title")}</Heading>
        <Divider />

        {screen === "choose" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text>{t("onboarding.choose.prompt")}</Text>
              <Stack gap="intra-section">
                <Button variant="primary" onClick={() => chooseTextMethod("avanza")}>
                  {t("onboarding.choose.avanza")}
                </Button>
                <Button variant="primary" onClick={() => chooseTextMethod("nordnet")}>
                  {t("onboarding.choose.nordnet")}
                </Button>
                <Button variant="tertiary" onClick={() => chooseTextMethod("paste")}>
                  {t("onboarding.choose.paste")}
                </Button>
                <Button variant="tertiary" onClick={() => fileInputRef.current?.click()}>
                  {t("onboarding.choose.csv")}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.txt"
                  onChange={handleFileSelected}
                  style={{ display: "none" }}
                />
                <Button variant="tertiary" onClick={() => setScreen("manual")}>
                  {t("onboarding.choose.manual")}
                </Button>
              </Stack>
              {errorMessage && (
                <Text color="tertiary" role="alert">
                  {errorMessage}
                </Text>
              )}
            </Stack>
          </Surface>
        )}

        {screen === "text" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Text color="secondary">{t(INPUT_INSTRUCTIONS_KEY[entryMethod])}</Text>
              <Text as="label">
                <textarea
                  value={rawText}
                  onChange={(event) => setRawText(event.target.value)}
                  placeholder={t("onboarding.input.placeholder")}
                  rows={10}
                  style={{ width: "100%", fontFamily: "monospace" }}
                />
              </Text>
              {errorMessage && (
                <Text color="tertiary" role="alert">
                  {errorMessage}
                </Text>
              )}
              <div>
                <Button variant="primary" onClick={() => void runPreview(rawText)} disabled={rawText.trim() === ""}>
                  {t("onboarding.input.continueButton")}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setScreen("choose")}>
                  {t("onboarding.input.backButton")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {screen === "manual" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("onboarding.manual.heading")}</Heading>
              <Text color="secondary">{t("onboarding.manual.instructions")}</Text>

              {manualRows.map((row, index) => (
                <Stack key={index} gap="inter-section">
                  <Inline gap="row" wrap>
                    <Text as="label">
                      {t("onboarding.manual.companyLabel")}
                      <br />
                      <input
                        value={row.company}
                        onChange={(event) => updateManualRow(index, { company: event.target.value })}
                      />
                    </Text>
                    <Text as="label">
                      {t("onboarding.manual.quantityLabel")}
                      <br />
                      <input
                        value={row.quantity}
                        onChange={(event) => updateManualRow(index, { quantity: event.target.value })}
                      />
                    </Text>
                    <Text as="label">
                      {t("onboarding.manual.priceLabel")}
                      <br />
                      <input
                        value={row.price}
                        onChange={(event) => updateManualRow(index, { price: event.target.value })}
                      />
                    </Text>
                  </Inline>
                  {manualRows.length > 1 && (
                    <Button variant="tertiary" onClick={() => removeManualRow(index)}>
                      {t("onboarding.manual.removeRowButton")}
                    </Button>
                  )}
                  <Divider tone="hairline" />
                </Stack>
              ))}

              <div>
                <Button variant="tertiary" onClick={addManualRow}>
                  {t("onboarding.manual.addRowButton")}
                </Button>
              </div>

              {errorMessage && (
                <Text color="tertiary" role="alert">
                  {errorMessage}
                </Text>
              )}

              <div>
                <Button
                  variant="primary"
                  onClick={submitManualRows}
                  disabled={manualRows.every((row) => row.company.trim() === "")}
                >
                  {t("onboarding.manual.continueButton")}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setScreen("choose")}>
                  {t("onboarding.input.backButton")}
                </Button>
              </div>

              <Divider tone="hairline" />
              <Link
                href="#"
                onClick={(event) => {
                  event.preventDefault();
                  setScreen("scratch");
                }}
              >
                {t("onboarding.manual.noPortfolioYetLink")}
              </Link>
            </Stack>
          </Surface>
        )}

        {screen === "scratch" && (
          <Surface tier="primary">
            <Stack gap="inter-section">
              <Heading level={2}>{t("onboarding.scratch.heading")}</Heading>
              <Text as="label">
                {t("onboarding.scratch.objectiveLabel")}
                <br />
                <input value={objective} onChange={(event) => setObjective(event.target.value)} />
              </Text>
              <Text as="label">
                {t("onboarding.scratch.horizonLabel")}
                <br />
                <input value={horizon} onChange={(event) => setHorizon(event.target.value)} />
              </Text>
              {scratchError && (
                <Text color="tertiary" role="alert">
                  {scratchError}
                </Text>
              )}
              <div>
                <Button variant="primary" onClick={submitScratch} disabled={scratchSubmitting}>
                  {scratchSubmitting ? t("common.saving") : t("onboarding.scratch.continueButton")}
                </Button>{" "}
                <Button variant="tertiary" onClick={() => setScreen("manual")} disabled={scratchSubmitting}>
                  {t("onboarding.input.backButton")}
                </Button>
              </div>
            </Stack>
          </Surface>
        )}

        {(screen === "loading-preview" || screen === "confirming") && (
          <Surface tier="primary">
            <Text role="status" aria-live="polite">
              {screen === "loading-preview" ? t("onboarding.loadingPreview") : t("onboarding.confirming")}
            </Text>
          </Surface>
        )}

        {screen === "review" && preview && (
          <ReviewScreen
            preview={preview}
            overrides={overrides}
            setOverrides={setOverrides}
            errorMessage={errorMessage}
            portfolioExists={portfolioExists}
            onBack={() => setScreen("choose")}
            onImport={() => void runConfirm(preview, overrides)}
            t={t}
          />
        )}

        {screen === "progress" && (
          <ProgressScreen
            holdingsIdentifiedCount={holdingsIdentifiedCount}
            progress={progress}
            onGoToPortfolio={() => navigate("/portfolio")}
            t={t}
          />
        )}
      </Stack>
    </Container>
  );
}

function ReviewScreen({
  preview,
  overrides,
  setOverrides,
  errorMessage,
  portfolioExists,
  onBack,
  onImport,
  t,
}: {
  preview: ImportPreview;
  overrides: Record<number, string>;
  setOverrides: (updater: (current: Record<number, string>) => Record<number, string>) => void;
  errorMessage: string | null;
  portfolioExists: boolean;
  onBack: () => void;
  onImport: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const attentionRows = preview.rows.filter(needsAttention);
  const resolvedRows = preview.rows.filter((row) => row.status === "RESOLVED");
  const informationalRows = preview.rows.filter(isInformationalExclusion);

  function setOverride(lineNumber: number, value: string) {
    setOverrides((current) => ({ ...current, [lineNumber]: value }));
  }

  function hasResolvedOverride(row: ParsedHoldingRow): boolean {
    return (overrides[row.lineNumber]?.trim() ?? "").length >= MIN_MANUAL_TICKER_LENGTH;
  }

  // Real Avanza Import Fix (Phase 8): one unusual holding must never
  // hold the rest of a real import hostage. Import is enabled as soon
  // as there is at least one importable holding -- any attention row
  // the investor hasn't (yet) resolved is simply skipped, never
  // silently: `willSkipCount` is always shown when it isn't zero.
  const willSkipCount = attentionRows.filter((row) => !hasResolvedOverride(row)).length;
  const importableCount = resolvedRows.length + (attentionRows.length - willSkipCount);
  const canImport = !preview.currencyConflict && importableCount > 0;

  return (
    <Surface tier="primary">
      <Stack gap="inter-section">
        <Heading level={2}>{t("onboarding.review.heading")}</Heading>
        <Text>{t("onboarding.review.foundSummary", { count: preview.holdingsFound })}</Text>
        {resolvedRows.length > 0 && (
          <Text color="secondary" as="p">
            {"✓ " + t("onboarding.review.resolvedSummary", { count: resolvedRows.length })}
          </Text>
        )}
        {attentionRows.length > 0 && (
          <Text color="secondary" as="p">
            {"? " + t("onboarding.review.needsAttentionSummary", { count: attentionRows.length })}
          </Text>
        )}
        {informationalRows.length > 0 && (
          <Text color="tertiary" as="p">
            {t("onboarding.review.excludedSummary", { count: informationalRows.length })}
          </Text>
        )}

        {preview.currencyConflict && (
          <Text color="tertiary" role="alert">
            {t("onboarding.review.currencyConflict")}
          </Text>
        )}

        {attentionRows.length > 0 && (
          <Stack gap="intra-section">
            {attentionRows.map((row) => (
              <Surface key={row.lineNumber} tier="elevated">
                <Stack gap="metadata">
                  <Text as="p">{row.originalName ?? row.raw}</Text>
                  {row.status === "AMBIGUOUS" ? (
                    <Stack gap="metadata">
                      <Text color="secondary" as="p">
                        {t("onboarding.review.ambiguousPrompt")}
                      </Text>
                      {row.candidates.map((candidate) => (
                        <Text as="label" key={candidate.ticker}>
                          <input
                            type="radio"
                            name={`candidate-${row.lineNumber}`}
                            checked={overrides[row.lineNumber] === candidate.ticker}
                            onChange={() => setOverride(row.lineNumber, candidate.ticker)}
                          />{" "}
                          {candidate.displayName} ({candidate.ticker})
                        </Text>
                      ))}
                    </Stack>
                  ) : (
                    <Text as="label">
                      {t("onboarding.review.unresolvedPrompt")}
                      <br />
                      <input
                        type="text"
                        value={overrides[row.lineNumber] ?? ""}
                        onChange={(event) => setOverride(row.lineNumber, event.target.value.toUpperCase())}
                        placeholder={t("onboarding.review.tickerPlaceholder")}
                        style={{ fontFamily: "monospace", width: "10ch" }}
                      />
                    </Text>
                  )}
                </Stack>
              </Surface>
            ))}
          </Stack>
        )}

        {informationalRows.length > 0 && (
          <Stack gap="intra-section">
            {informationalRows.map((row) => (
              <Surface key={row.lineNumber} tier="elevated">
                <Text as="p">{row.originalName ?? row.raw}</Text>
                <Text color="tertiary" as="p">
                  {row.message}
                </Text>
              </Surface>
            ))}
          </Stack>
        )}

        {portfolioExists && <Text color="tertiary">{t("onboarding.review.replaceWarning")}</Text>}

        {willSkipCount > 0 && (
          <Text color="tertiary" as="p">
            {t("onboarding.review.willSkipNote", { count: willSkipCount })}
          </Text>
        )}

        {errorMessage && (
          <Text color="tertiary" role="alert">
            {errorMessage}
          </Text>
        )}

        <div>
          <Button variant="primary" onClick={onImport} disabled={!canImport}>
            {t("onboarding.review.importButton")}
          </Button>{" "}
          <Button variant="tertiary" onClick={onBack}>
            {t("onboarding.review.backButton")}
          </Button>
        </div>
      </Stack>
    </Surface>
  );
}

function ProgressScreen({
  holdingsIdentifiedCount,
  progress,
  onGoToPortfolio,
  t,
}: {
  holdingsIdentifiedCount: number;
  progress: EnrichmentProgress | null;
  onGoToPortfolio: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="inter-section">
        <Heading level={2}>{t("onboarding.progress.heading")}</Heading>
        <Text as="p" color="secondary">
          {"✓ " + t("onboarding.progress.imported")}
        </Text>
        <Text as="p" color="secondary">
          {"✓ " + t("onboarding.progress.holdingsIdentified", { count: holdingsIdentifiedCount })}
        </Text>
        {progress && progress.total > 0 && (
          <Stack gap="metadata">
            {!progress.complete && progress.currentlyAnalyzing && (
              <Text as="p" role="status" aria-live="polite">
                {t("onboarding.progress.analyzing", { name: progress.currentlyAnalyzing })}
              </Text>
            )}
            <Text as="p" color="secondary">
              {t("onboarding.progress.countSummary", { done: progress.doneCount, total: progress.total })}
            </Text>
          </Stack>
        )}
        <Divider tone="hairline" />
        <Text as="p">
          <strong>{t("onboarding.progress.startNow")}</strong>
        </Text>
        <Text as="p" color="secondary">
          {t("onboarding.progress.remainingNote")}
        </Text>
        <div>
          <Button variant="primary" onClick={onGoToPortfolio}>
            {t("onboarding.progress.goToPortfolio")}
          </Button>
        </div>
      </Stack>
    </Surface>
  );
}
