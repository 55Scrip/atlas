import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import { ACCENT_LINK_STYLE, AsyncSection, Button, Container, Heading, Inline, Stack, Surface, Text } from "../foundation";
import type { AsyncStatus } from "../foundation";
import { useTranslation } from "../i18n";
import { abandonDecisionDraft, fetchDecisionDraft, type DecisionDraftView as LegacyDraftView } from "./decisionDraftApi";
import { commitDraftWithReasoning } from "./reasoningWorkspaceApi";

interface AssumptionDraftRow {
  statement: string;
  linkedConditionPredicates: string[];
}

/**
 * Sprint 13 §5 — the Draft Commit Flow. Wraps Sprint 12's
 * `commit-with-reasoning` endpoint: the investor fills in plain
 * statement/predicate text for whatever assumptions and CaseConditions
 * they want created alongside the commit, and this page assembles
 * exactly the request shape that endpoint already expects (see
 * `reasoningWorkspaceApi.commitDraftWithReasoning`) -- no orchestration
 * logic of its own; the backend performs every write, in the order and
 * with the guarantees Sprint 12 already established.
 *
 * Product Sprint 10 (Navigation & Workflow Excellence, Deliverable 3):
 * previously had no way out except completing the commit -- a real
 * "how do I cancel and go back" gap. `draft.caseId` is already fetched,
 * so the return link to the originating Investment Case costs nothing
 * new.
 */

export function DraftCommitPage() {
  const { draftId } = useParams<{ draftId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [status, setStatus] = useState<AsyncStatus<LegacyDraftView>>({ kind: "loading" });
  const [assumptionRows, setAssumptionRows] = useState<AssumptionDraftRow[]>([]);
  const [standaloneConditions, setStandaloneConditions] = useState<string[]>([]);
  const [committing, setCommitting] = useState(false);
  const [commitError, setCommitError] = useState<string | null>(null);
  const [abandoning, setAbandoning] = useState(false);
  const [abandonError, setAbandonError] = useState<string | null>(null);

  useEffect(() => {
    if (!draftId) return;
    let cancelled = false;
    fetchDecisionDraft(draftId)
      .then((draft) => {
        if (cancelled) return;
        if (draft === null) {
          setStatus({ kind: "error", message: t("common.unknownError") });
        } else {
          setStatus({ kind: "loaded", data: draft });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) setStatus({ kind: "error", message: error instanceof Error ? error.message : t("common.unknownError") });
      });
    return () => {
      cancelled = true;
    };
  }, [draftId, t]);

  async function handleCommit() {
    if (!draftId) return;
    setCommitting(true);
    setCommitError(null);
    try {
      const result = await commitDraftWithReasoning(draftId, {
        assumptions: assumptionRows
          .filter((row) => row.statement.trim().length > 0)
          .map((row) => ({
            statement: row.statement.trim(),
            authorship: "user",
            linkedConditions: row.linkedConditionPredicates
              .filter((predicate) => predicate.trim().length > 0)
              .map((predicate) => ({ predicateText: predicate.trim(), authorship: "user" })),
          })),
        standaloneCaseConditions: standaloneConditions
          .filter((predicate) => predicate.trim().length > 0)
          .map((predicate) => ({ predicateText: predicate.trim(), authorship: "user" })),
      });
      navigate(`/decisions/${result.decision.id}/workspace`);
    } catch (error) {
      setCommitError(error instanceof Error ? error.message : t("common.unknownError"));
    } finally {
      setCommitting(false);
    }
  }

  /** Product Sprint 12 (Decision Workflow Consolidation, Deliverable 4
   * -- Draft Workflow, "Can they abandon it?"): `abandonDecisionDraft`
   * already existed with zero callers anywhere in the frontend --
   * there was previously no way to abandon a draft except leaving the
   * tab and never returning, which left it sitting as "in progress"
   * indefinitely (surfaced back to the investor by
   * `StartDecisionSection`'s own Resume prompt with no way to
   * dismiss it). One click, matching this app's own established
   * pattern for a reversible-enough action (Watchlist's own remove
   * button is the same single click, not a two-step confirm --
   * Product Sprint 10 found and fixed the opposite problem there). */
  async function handleAbandon(caseId: string) {
    if (!draftId) return;
    setAbandoning(true);
    setAbandonError(null);
    try {
      await abandonDecisionDraft(draftId);
      navigate(`/investment-case/${caseId}`);
    } catch (error) {
      setAbandonError(error instanceof Error ? error.message : t("common.unknownError"));
      setAbandoning(false);
    }
  }

  return (
    <Container width="wide">
      <Stack gap="inter-section">
        <Heading level={2}>{t("decisionWorkspace.commit.heading")}</Heading>
        <AsyncSection
          status={status}
          loadingLabel={t("decisionWorkspace.loading")}
          errorLabel={(message) => t("decisionWorkspace.loadError", { message: message ?? t("common.unknownError") })}
        >
          {(draft) => (
            <Stack gap="inter-section">
              <RouterLink to={`/investment-case/${draft.caseId}`} style={ACCENT_LINK_STYLE}>
                {t("decisionWorkspace.backToInvestmentCase")}
              </RouterLink>

              <Surface tier="primary" bordered>
                <Text as="p">{draft.subject ?? t("decisionWorkspace.draftsSection.subjectFallback")}</Text>
                <Text as="p" color="secondary">
                  {draft.reason}
                </Text>
              </Surface>

              <Text as="p" color="secondary">
                {t("decisionWorkspace.commit.explanation")}
              </Text>

              <AssumptionRowsEditor rows={assumptionRows} onChange={setAssumptionRows} />
              <StandaloneConditionsEditor predicates={standaloneConditions} onChange={setStandaloneConditions} />

              {commitError && (
                <Text color="tertiary" role="alert">
                  {t("decisionWorkspace.commit.commitFailed", { message: commitError })}
                </Text>
              )}
              {abandonError && (
                <Text color="tertiary" role="alert">
                  {t("decisionWorkspace.commit.abandonFailed", { message: abandonError })}
                </Text>
              )}

              <Inline gap="row">
                <Button variant="primary" onClick={handleCommit} disabled={committing || abandoning}>
                  {committing ? t("decisionWorkspace.commit.committingLabel") : t("decisionWorkspace.commit.commitButton")}
                </Button>
                <Button variant="tertiary" onClick={() => handleAbandon(draft.caseId)} disabled={committing || abandoning}>
                  {abandoning ? t("decisionWorkspace.commit.abandoningLabel") : t("decisionWorkspace.commit.abandonButton")}
                </Button>
              </Inline>
            </Stack>
          )}
        </AsyncSection>
      </Stack>
    </Container>
  );
}

function AssumptionRowsEditor({
  rows,
  onChange,
}: {
  rows: AssumptionDraftRow[];
  onChange: (rows: AssumptionDraftRow[]) => void;
}) {
  const { t } = useTranslation();

  function addRow() {
    onChange([...rows, { statement: "", linkedConditionPredicates: [] }]);
  }

  function updateStatement(index: number, statement: string) {
    onChange(rows.map((row, i) => (i === index ? { ...row, statement } : row)));
  }

  function addLinkedCondition(index: number) {
    onChange(
      rows.map((row, i) => (i === index ? { ...row, linkedConditionPredicates: [...row.linkedConditionPredicates, ""] } : row)),
    );
  }

  function updateLinkedCondition(rowIndex: number, conditionIndex: number, value: string) {
    onChange(
      rows.map((row, i) =>
        i === rowIndex
          ? {
              ...row,
              linkedConditionPredicates: row.linkedConditionPredicates.map((predicate, j) =>
                j === conditionIndex ? value : predicate,
              ),
            }
          : row,
      ),
    );
  }

  function removeRow(index: number) {
    onChange(rows.filter((_, i) => i !== index));
  }

  return (
    <Stack gap="row">
      {rows.map((row, index) => (
        <Surface key={index} tier="primary" bordered>
          <Stack gap="metadata">
            <Text as="label">
              <input
                type="text"
                value={row.statement}
                onChange={(event) => updateStatement(index, event.target.value)}
                placeholder={t("decisionWorkspace.commit.assumptionStatementPlaceholder")}
                aria-label={t("decisionWorkspace.commit.assumptionStatementPlaceholder")}
                style={{ width: "100%" }}
              />
            </Text>
            <Text color="tertiary" as="span">
              {t("decisionWorkspace.commit.linkedConditionsHeading")}
            </Text>
            {row.linkedConditionPredicates.map((predicate, conditionIndex) => (
              <Text as="label" key={conditionIndex}>
                <input
                  type="text"
                  value={predicate}
                  onChange={(event) => updateLinkedCondition(index, conditionIndex, event.target.value)}
                  placeholder={t("decisionWorkspace.commit.conditionPredicatePlaceholder")}
                  aria-label={t("decisionWorkspace.commit.conditionPredicatePlaceholder")}
                  style={{ width: "100%" }}
                />
              </Text>
            ))}
            <Inline gap="row">
              <Button variant="tertiary" onClick={() => addLinkedCondition(index)}>
                {t("decisionWorkspace.commit.addLinkedConditionButton")}
              </Button>
              <Button variant="tertiary" onClick={() => removeRow(index)}>
                {t("decisionWorkspace.commit.removeButton")}
              </Button>
            </Inline>
          </Stack>
        </Surface>
      ))}
      <Inline gap="row">
        <Button variant="tertiary" onClick={addRow}>
          {t("decisionWorkspace.commit.addAssumptionButton")}
        </Button>
      </Inline>
    </Stack>
  );
}

function StandaloneConditionsEditor({
  predicates,
  onChange,
}: {
  predicates: string[];
  onChange: (predicates: string[]) => void;
}) {
  const { t } = useTranslation();

  function addPredicate() {
    onChange([...predicates, ""]);
  }

  function updatePredicate(index: number, value: string) {
    onChange(predicates.map((predicate, i) => (i === index ? value : predicate)));
  }

  function removePredicate(index: number) {
    onChange(predicates.filter((_, i) => i !== index));
  }

  return (
    <Stack gap="row">
      <Text color="tertiary" as="span">
        {t("decisionWorkspace.commit.standaloneConditionsHeading")}
      </Text>
      {predicates.map((predicate, index) => (
        <Inline gap="row" key={index}>
          <Text as="label" style={{ flex: 1 }}>
            <input
              type="text"
              value={predicate}
              onChange={(event) => updatePredicate(index, event.target.value)}
              placeholder={t("decisionWorkspace.commit.conditionPredicatePlaceholder")}
              aria-label={t("decisionWorkspace.commit.conditionPredicatePlaceholder")}
              style={{ width: "100%" }}
            />
          </Text>
          <Button variant="tertiary" onClick={() => removePredicate(index)}>
            {t("decisionWorkspace.commit.removeButton")}
          </Button>
        </Inline>
      ))}
      <Inline gap="row">
        <Button variant="tertiary" onClick={addPredicate}>
          {t("decisionWorkspace.commit.addConditionButton")}
        </Button>
      </Inline>
    </Stack>
  );
}
