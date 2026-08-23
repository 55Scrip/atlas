import { useState } from "react";
import { Button, Heading, Inline, Label, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { StatusTone } from "../foundation";
import { useTranslation } from "../i18n";
import { createCaseCondition, evaluateCaseCondition, retireCaseCondition, reviseCaseCondition } from "./caseConditionApi";
import type { CaseConditionRole, CaseConditionStatus, CaseConditionView } from "./reasoningWorkspaceApi";

const STATUS_TONE: Record<CaseConditionStatus, StatusTone> = {
  active: "neutral",
  satisfied: "caution",
  superseded: "neutral",
  retired: "neutral",
};

/**
 * Sprint 13 §4 — create/revise/evaluate/retire, each a direct call to
 * the existing CaseCondition API (Sprint 10). `evaluate` exercises
 * both backend evaluation paths (ADR-CC-001 §5): a plain checkbox for
 * `humanAssertedSatisfied` (the only path for a free-text predicate)
 * and, for a date-structured condition, no extra input at all --
 * `evaluatedAt` defaults to now server-side.
 */
export function CaseConditionsSection({
  caseId,
  decisionId,
  caseConditions,
  onMutated,
}: {
  caseId: string;
  decisionId: string;
  caseConditions: CaseConditionView[];
  onMutated: () => void;
}) {
  const { t } = useTranslation();
  const [newPredicate, setNewPredicate] = useState("");
  const [newRole, setNewRole] = useState<CaseConditionRole>("monitoring");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setCreating(true);
    setError(null);
    try {
      await createCaseCondition(caseId, {
        decisionId,
        predicateText: newPredicate.trim() || null,
        role: newRole,
        authorship: "user",
      });
      setNewPredicate("");
      onMutated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.unknownError"));
    } finally {
      setCreating(false);
    }
  }

  return (
    <Stack gap="inter-section">
      <Heading level={3}>{t("decisionWorkspace.caseConditions.heading")}</Heading>

      {caseConditions.length === 0 && <Text color="secondary">{t("decisionWorkspace.caseConditions.none")}</Text>}

      <Stack gap="row">
        {caseConditions.map((condition) => (
          <CaseConditionRow key={condition.conditionId} condition={condition} onMutated={onMutated} />
        ))}
      </Stack>

      <Surface tier="primary" bordered>
        <Stack gap="row">
          <Text as="label">
            <input
              type="text"
              value={newPredicate}
              onChange={(event) => setNewPredicate(event.target.value)}
              placeholder={t("decisionWorkspace.caseConditions.newPredicatePlaceholder")}
              aria-label={t("decisionWorkspace.caseConditions.predicateLabel")}
              style={{ width: "100%" }}
            />
          </Text>
          <Text as="label">
            {t("decisionWorkspace.caseConditions.roleLabel")}:{" "}
            <select value={newRole} onChange={(event) => setNewRole(event.target.value as CaseConditionRole)}>
              <option value="monitoring">{t("decisionWorkspace.caseConditions.roleMonitoring")}</option>
              <option value="invalidation">{t("decisionWorkspace.caseConditions.roleInvalidation")}</option>
            </select>
          </Text>
          {error && (
            <Text color="tertiary" role="alert">
              {t("decisionWorkspace.caseConditions.actionFailed", { message: error })}
            </Text>
          )}
          <Inline gap="row">
            {/* Product Sprint 11 (Investment Workflow Excellence,
                Deliverable 5): same guard as `AssumptionsSection.tsx` --
                previously had no protection against creating a real,
                persisted CaseCondition with a null predicate. */}
            <Button variant="primary" onClick={handleCreate} disabled={creating || newPredicate.trim() === ""}>
              {creating ? t("decisionWorkspace.caseConditions.creatingLabel") : t("decisionWorkspace.caseConditions.createButton")}
            </Button>
          </Inline>
        </Stack>
      </Surface>
    </Stack>
  );
}

function CaseConditionRow({ condition, onMutated }: { condition: CaseConditionView; onMutated: () => void }) {
  const { t } = useTranslation();
  const [editing, setEditing] = useState(false);
  const [draftPredicate, setDraftPredicate] = useState(condition.predicateText ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evaluationResult, setEvaluationResult] = useState<string | null>(null);
  const [humanAsserted, setHumanAsserted] = useState(false);

  const terminal = condition.status === "superseded" || condition.status === "retired";

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      setEditing(false);
      onMutated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.unknownError"));
    } finally {
      setBusy(false);
    }
  }

  async function handleEvaluate() {
    setBusy(true);
    setError(null);
    setEvaluationResult(null);
    try {
      const result = await evaluateCaseCondition(
        condition.conditionId,
        condition.structuredKind === null ? { humanAssertedSatisfied: humanAsserted } : {},
      );
      setEvaluationResult(
        result.satisfied
          ? t("decisionWorkspace.caseConditions.evaluateSatisfiedResult")
          : t("decisionWorkspace.caseConditions.evaluateNotSatisfiedResult"),
      );
      if (result.transitioned) onMutated();
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
            label={t(`decisionWorkspace.caseConditions.status.${condition.status}` as never)}
            tone={STATUS_TONE[condition.status]}
          />
          {condition.role && (
            <Text color="tertiary" as="span">
              {t(condition.role === "monitoring" ? "decisionWorkspace.caseConditions.roleMonitoring" : "decisionWorkspace.caseConditions.roleInvalidation")}
            </Text>
          )}
        </Inline>

        {editing ? (
          <Text as="label">
            <input
              type="text"
              value={draftPredicate}
              onChange={(event) => setDraftPredicate(event.target.value)}
              aria-label={t("decisionWorkspace.caseConditions.predicateLabel")}
              style={{ width: "100%" }}
            />
          </Text>
        ) : (
          <Text as="p">{condition.predicateText ?? "—"}</Text>
        )}

        {condition.lastObservedValue !== null && (
          <Text color="tertiary" as="span">
            {condition.lastObservedValue}
          </Text>
        )}

        {evaluationResult && (
          <Text color="secondary" role="status">
            {evaluationResult}
          </Text>
        )}
        {error && (
          <Text color="tertiary" role="alert">
            {t("decisionWorkspace.caseConditions.actionFailed", { message: error })}
          </Text>
        )}

        {!terminal && condition.structuredKind === null && (
          <Text as="label">
            <input type="checkbox" checked={humanAsserted} onChange={(event) => setHumanAsserted(event.target.checked)} />{" "}
            {t("decisionWorkspace.caseConditions.humanAssertLabel")}
          </Text>
        )}

        {!terminal && (
          <Inline gap="row" wrap>
            {editing ? (
              <>
                <Button
                  variant="primary"
                  disabled={busy}
                  onClick={() => run(() => reviseCaseCondition(condition.conditionId, { predicateText: draftPredicate.trim() || null }))}
                >
                  {busy ? t("decisionWorkspace.caseConditions.savingLabel") : t("decisionWorkspace.caseConditions.saveButton")}
                </Button>
                <Button variant="tertiary" disabled={busy} onClick={() => setEditing(false)}>
                  {t("decisionWorkspace.caseConditions.cancelEditButton")}
                </Button>
              </>
            ) : (
              <>
                <Button variant="tertiary" onClick={() => setEditing(true)}>
                  {t("decisionWorkspace.caseConditions.editButton")}
                </Button>
                <Button variant="tertiary" disabled={busy} onClick={handleEvaluate}>
                  {busy ? t("decisionWorkspace.caseConditions.evaluatingLabel") : t("decisionWorkspace.caseConditions.evaluateButton")}
                </Button>
                <Button variant="tertiary" disabled={busy} onClick={() => run(() => retireCaseCondition(condition.conditionId))}>
                  {busy ? t("decisionWorkspace.caseConditions.retiringLabel") : t("decisionWorkspace.caseConditions.retireButton")}
                </Button>
              </>
            )}
          </Inline>
        )}
      </Stack>
    </Surface>
  );
}
