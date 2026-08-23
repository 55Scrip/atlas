import { useEffect, useState } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Inline, Stack, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { ALPHA_PLACEHOLDER_USER_ID } from "./alphaUser";
import { createDecisionDraft, listActiveDecisionDrafts, type DecisionDraftView } from "./decisionDraftApi";

/**
 * Product Sprint 12 (Decision Workflow Consolidation, Deliverable 2/3
 * -- One Decision Workflow / Start Decision).
 *
 * Sprint 11's own audit found this gap live: a case with no linked
 * Portfolio holding had a real, working "Compare" and "Add to
 * Watchlist," but recording an actual investment decision was
 * completely unreachable -- `investmentCase.actions.notLinkedNote`
 * just named the requirement ("linked to a holding") with no way to
 * act on it, because the quick-action panel (Add/Trim/Remove/Leave as
 * is) genuinely does require an existing position to adjust.
 *
 * `createDecisionDraft`/`listActiveDecisionDrafts` (`decisionDraftApi.ts`)
 * already existed, fully implemented and typed, with zero callers
 * anywhere in the frontend -- this component is the missing connection,
 * not a new capability. A Decision Draft is scoped to a Case, not a
 * Portfolio holding, so it works for exactly the case this sprint's own
 * Deliverable 2 designates as the chosen workflow: a genuinely new
 * investment decision. The existing quick-action panel on
 * `InvestmentCasePage.tsx` (Add to Position / Trim / Remove / Leave as
 * is) remains untouched -- unchanged, unredesigned -- and is the
 * intentional lightweight mode for adjusting a position Atlas already
 * knows about, per this sprint's own Deliverable 2 language ("unless
 * Atlas intentionally supports a lightweight mode").
 *
 * Deliverable 3's "never duplicated" rule: when a draft is already in
 * progress for this case, only the Resume link is shown -- never both
 * a Resume prompt and a fresh Start trigger side by side.
 */

type DraftsStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; drafts: DecisionDraftView[] };

type DecisionTypeChoice = "BUY" | "WATCH" | "PASS";

const DECISION_TYPE_LABEL_KEY: Record<DecisionTypeChoice, TranslationKey> = {
  BUY: "investmentCase.decision.typeBuy",
  WATCH: "investmentCase.decision.typeWatch",
  PASS: "investmentCase.decision.typePass",
};

export function StartDecisionSection({ caseId, ticker }: { caseId: string; ticker: string | null }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [draftsStatus, setDraftsStatus] = useState<DraftsStatus>({ kind: "loading" });
  const [expanded, setExpanded] = useState(false);
  const [decisionType, setDecisionType] = useState<DecisionTypeChoice>("BUY");
  const [reason, setReason] = useState("");
  const [confidence, setConfidence] = useState("50");
  const [manualTicker, setManualTicker] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Product Sprint 12: live-tested -- when `ticker` is unresolved (a
   * real, honest state; see Sprint 11/12's own `resolvedTicker`
   * fallback chain), the backend's `commit-with-reasoning` step
   * rejects the resulting Decision with "Subject.value must not be
   * empty." Rather than silently creating a Draft doomed to fail at
   * commit time, this asks for the ticker up front in that case only --
   * the common case (`ticker` already known) is unaffected. */
  const subject = ticker ?? manualTicker.trim();

  useEffect(() => {
    const controller = new AbortController();
    listActiveDecisionDrafts(caseId, controller.signal)
      .then((drafts) => setDraftsStatus({ kind: "loaded", drafts }))
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setDraftsStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [caseId]);

  async function handleStart() {
    setSubmitting(true);
    setError(null);
    try {
      const draft = await createDecisionDraft(caseId, ALPHA_PLACEHOLDER_USER_ID, {
        decisionType,
        subject,
        reason: reason.trim(),
        confidence: Number(confidence),
      });
      navigate(`/decision-drafts/${draft.draftId}/commit`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.unknownError"));
      setSubmitting(false);
    }
  }

  if (draftsStatus.kind === "loading") return null;

  if (draftsStatus.kind === "loaded" && draftsStatus.drafts.length > 0) {
    return (
      <Stack gap="metadata">
        <Text color="secondary">{t("decisionWorkspace.startDecision.resumeHeading")}</Text>
        <Inline gap="row" wrap>
          {draftsStatus.drafts.map((draft) => (
            <RouterLink key={draft.draftId} to={`/decision-drafts/${draft.draftId}/commit`} style={ACCENT_LINK_STYLE}>
              {t("decisionWorkspace.startDecision.resumeLink", {
                subject: draft.subject ?? t("decisionWorkspace.startDecision.resumeFallbackSubject"),
              })}
            </RouterLink>
          ))}
        </Inline>
      </Stack>
    );
  }

  if (!expanded) {
    return (
      <Button variant="primary" onClick={() => setExpanded(true)}>
        {t("decisionWorkspace.startDecision.trigger")}
      </Button>
    );
  }

  return (
    <Stack gap="metadata">
      <Text color="secondary">{t("decisionWorkspace.startDecision.explanation")}</Text>
      <Inline gap="row">
        {(Object.keys(DECISION_TYPE_LABEL_KEY) as DecisionTypeChoice[]).map((choice) => (
          <Button
            key={choice}
            variant={decisionType === choice ? "primary" : "tertiary"}
            onClick={() => setDecisionType(choice)}
          >
            {t(DECISION_TYPE_LABEL_KEY[choice])}
          </Button>
        ))}
      </Inline>
      {ticker === null && (
        <Text as="label">
          {t("decisionWorkspace.startDecision.tickerLabel")}
          <input
            type="text"
            value={manualTicker}
            onChange={(event) => setManualTicker(event.target.value)}
            placeholder={t("decisionWorkspace.startDecision.tickerPlaceholder")}
            style={{ width: "100%" }}
          />
        </Text>
      )}
      <Text as="label">
        {t("investmentCase.actions.reasonLabel")}
        <input
          type="text"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          style={{ width: "100%" }}
        />
      </Text>
      <Text as="label">
        {t("investmentCase.actions.confidenceLabel")}
        <input
          type="number"
          min={0}
          max={100}
          value={confidence}
          onChange={(event) => setConfidence(event.target.value)}
        />
      </Text>
      {error && (
        <Text color="tertiary" role="alert">
          {t("decisionWorkspace.startDecision.startFailed", { message: error })}
        </Text>
      )}
      <Inline gap="row">
        <Button variant="primary" onClick={handleStart} disabled={submitting || reason.trim() === "" || subject === ""}>
          {submitting ? t("decisionWorkspace.startDecision.submitting") : t("decisionWorkspace.startDecision.submitButton")}
        </Button>
        <Button variant="tertiary" onClick={() => setExpanded(false)} disabled={submitting}>
          {t("common.cancel")}
        </Button>
      </Inline>
    </Stack>
  );
}
