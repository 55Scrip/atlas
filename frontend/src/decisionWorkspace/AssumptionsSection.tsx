import { useState } from "react";
import { Button, Heading, Inline, Label, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { StatusTone } from "../foundation";
import { useTranslation } from "../i18n";
import { challengeAssumption, createAssumption, retireAssumption, reviseAssumption } from "./assumptionApi";
import type { AssumptionStatus, AssumptionView } from "./reasoningWorkspaceApi";

const STATUS_TONE: Record<AssumptionStatus, StatusTone> = {
  supported: "positive",
  challenged: "caution",
  invalidated: "critical",
  superseded: "neutral",
  retired: "neutral",
};

/**
 * Sprint 13 §3 — create/revise/challenge/retire, each a direct call to
 * the existing Assumption API (Sprint 11), never a local reimplementation
 * of any of it. After every successful write this component calls
 * `onMutated`, which the parent (`DecisionWorkspacePage`) uses to
 * re-fetch the whole reasoning workspace from the backend — the
 * frontend never patches its own copy of an `AssumptionView` in place;
 * the next render always shows exactly what the backend now says.
 */
export function AssumptionsSection({
  decisionId,
  assumptions,
  onMutated,
}: {
  decisionId: string;
  assumptions: AssumptionView[];
  onMutated: () => void;
}) {
  const { t } = useTranslation();
  const [newStatement, setNewStatement] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setCreating(true);
    setError(null);
    try {
      await createAssumption(decisionId, { statement: newStatement.trim() || null, authorship: "user" });
      setNewStatement("");
      onMutated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.unknownError"));
    } finally {
      setCreating(false);
    }
  }

  return (
    <Stack gap="inter-section">
      <Heading level={3}>{t("decisionWorkspace.assumptions.heading")}</Heading>

      {assumptions.length === 0 && <Text color="secondary">{t("decisionWorkspace.assumptions.none")}</Text>}

      <Stack gap="row">
        {assumptions.map((assumption) => (
          <AssumptionRow key={assumption.assumptionId} assumption={assumption} onMutated={onMutated} />
        ))}
      </Stack>

      <Surface tier="primary" bordered>
        <Stack gap="row">
          <Text as="label">
            <input
              type="text"
              value={newStatement}
              onChange={(event) => setNewStatement(event.target.value)}
              placeholder={t("decisionWorkspace.assumptions.newStatementPlaceholder")}
              aria-label={t("decisionWorkspace.assumptions.statementLabel")}
              style={{ width: "100%" }}
            />
          </Text>
          {error && (
            <Text color="tertiary" role="alert">
              {t("decisionWorkspace.assumptions.actionFailed", { message: error })}
            </Text>
          )}
          <Inline gap="row">
            {/* Product Sprint 11 (Investment Workflow Excellence,
                Deliverable 5): live-tested -- this button had no guard
                against an empty statement, so a stray click created a
                real, persisted Assumption with `statement: null` (shown
                as a bare "-- ") and no way back except Retire. */}
            <Button variant="primary" onClick={handleCreate} disabled={creating || newStatement.trim() === ""}>
              {creating ? t("decisionWorkspace.assumptions.creatingLabel") : t("decisionWorkspace.assumptions.createButton")}
            </Button>
          </Inline>
        </Stack>
      </Surface>
    </Stack>
  );
}

function AssumptionRow({ assumption, onMutated }: { assumption: AssumptionView; onMutated: () => void }) {
  const { t } = useTranslation();
  const [editing, setEditing] = useState(false);
  const [draftStatement, setDraftStatement] = useState(assumption.statement ?? "");
  const [challenging, setChallenging] = useState(false);
  const [challengeNote, setChallengeNote] = useState("");
  const [challengeSeverity, setChallengeSeverity] = useState<"challenged" | "invalidated">("challenged");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const terminal = assumption.status === "superseded" || assumption.status === "retired";

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      setEditing(false);
      setChallenging(false);
      onMutated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.unknownError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Surface tier="primary" bordered>
      <Stack gap="metadata">
        <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
          <StatusBadge
            label={t(`decisionWorkspace.assumptions.status.${assumption.status}` as never)}
            tone={STATUS_TONE[assumption.status]}
          />
          {assumption.authorship && (
            <Text color="tertiary" as="span">
              {t("decisionWorkspace.assumptions.authorshipLabel")}: {assumption.authorship}
            </Text>
          )}
        </Inline>

        {editing ? (
          <Text as="label">
            <input
              type="text"
              value={draftStatement}
              onChange={(event) => setDraftStatement(event.target.value)}
              aria-label={t("decisionWorkspace.assumptions.statementLabel")}
              style={{ width: "100%" }}
            />
          </Text>
        ) : (
          <Text as="p">{assumption.statement ?? "—"}</Text>
        )}

        <Text color="tertiary" as="span">
          {t("decisionWorkspace.assumptions.linkedConditionsLabel")}:{" "}
          {assumption.linkedCaseConditionIds.length > 0
            ? assumption.linkedCaseConditionIds.join(", ")
            : t("decisionWorkspace.assumptions.linkedConditionsNone")}
        </Text>

        {assumption.lastChallengeNote && (
          <Text color="tertiary" as="p">
            {assumption.lastChallengeNote}
          </Text>
        )}

        {error && (
          <Text color="tertiary" role="alert">
            {t("decisionWorkspace.assumptions.actionFailed", { message: error })}
          </Text>
        )}

        {challenging && (
          <Stack gap="metadata">
            <Text as="label">
              <input
                type="text"
                value={challengeNote}
                onChange={(event) => setChallengeNote(event.target.value)}
                placeholder={t("decisionWorkspace.assumptions.challengeNotePlaceholder")}
                aria-label={t("decisionWorkspace.assumptions.challengeNotePlaceholder")}
                style={{ width: "100%" }}
              />
            </Text>
            <Text as="label">
              {t("decisionWorkspace.assumptions.severityLabel")}:{" "}
              <select
                value={challengeSeverity}
                onChange={(event) => setChallengeSeverity(event.target.value as "challenged" | "invalidated")}
              >
                <option value="challenged">{t("decisionWorkspace.assumptions.severityChallenged")}</option>
                <option value="invalidated">{t("decisionWorkspace.assumptions.severityInvalidated")}</option>
              </select>
            </Text>
          </Stack>
        )}

        {!terminal && (
          <Inline gap="row" wrap>
            {editing ? (
              <>
                <Button
                  variant="primary"
                  disabled={busy}
                  onClick={() => run(() => reviseAssumption(assumption.assumptionId, { statement: draftStatement.trim() || null, authorship: "user" }))}
                >
                  {busy ? t("decisionWorkspace.assumptions.savingLabel") : t("decisionWorkspace.assumptions.saveButton")}
                </Button>
                <Button variant="tertiary" disabled={busy} onClick={() => setEditing(false)}>
                  {t("decisionWorkspace.assumptions.cancelEditButton")}
                </Button>
              </>
            ) : challenging ? (
              <>
                <Button
                  variant="primary"
                  disabled={busy}
                  onClick={() =>
                    run(() =>
                      challengeAssumption(assumption.assumptionId, {
                        note: challengeNote.trim() || null,
                        severity: challengeSeverity,
                      }),
                    )
                  }
                >
                  {busy ? t("decisionWorkspace.assumptions.challengingLabel") : t("decisionWorkspace.assumptions.challengeButton")}
                </Button>
                <Button variant="tertiary" disabled={busy} onClick={() => setChallenging(false)}>
                  {t("decisionWorkspace.assumptions.cancelEditButton")}
                </Button>
              </>
            ) : (
              <>
                <Button variant="tertiary" onClick={() => setEditing(true)}>
                  {t("decisionWorkspace.assumptions.editButton")}
                </Button>
                <Button variant="tertiary" onClick={() => setChallenging(true)}>
                  {t("decisionWorkspace.assumptions.challengeButton")}
                </Button>
                <Button variant="tertiary" disabled={busy} onClick={() => run(() => retireAssumption(assumption.assumptionId))}>
                  {busy ? t("decisionWorkspace.assumptions.retiringLabel") : t("decisionWorkspace.assumptions.retireButton")}
                </Button>
              </>
            )}
          </Inline>
        )}
      </Stack>
    </Surface>
  );
}
