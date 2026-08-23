import { useCallback, useEffect, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";
import { ACCENT_LINK_STYLE, AsyncSection, Container, Heading, Inline, Label, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { AsyncStatus } from "../foundation";
import { useTranslation } from "../i18n";
import { AssumptionsSection } from "./AssumptionsSection";
import { CaseConditionsSection } from "./CaseConditionsSection";
import { ReasoningTimelineView } from "./ReasoningTimelineView";
import { buildReasoningTimeline, type TimelineEntry } from "./reasoningTimeline";
import {
  fetchActiveAssumptions,
  fetchActiveCaseConditions,
  fetchAssumptionEvents,
  fetchCaseConditionEvents,
  fetchDecisionDraftEvents,
  fetchDecisionReasoningWorkspace,
  fetchOpenDecisionDrafts,
  type ActiveAssumptionRow,
  type ActiveCaseConditionRow,
  type DecisionReasoningWorkspace,
  type OpenDecisionDraftRow,
} from "./reasoningWorkspaceApi";

/**
 * Sprint 13 §1 — the first complete Decision Workspace product
 * surface. Every fact shown here is read from an existing endpoint
 * (Sprints 9-12); this page performs no domain computation of its own
 * -- `status` badges render exactly the `status` string each backend
 * view already carries, the timeline is a client-side *sort* of
 * already-fetched raw events (`reasoningTimeline.ts`), and every
 * mutation (`AssumptionsSection`/`CaseConditionsSection`) triggers a
 * full re-fetch from the backend rather than a local patch.
 *
 * Product Sprint 10 (Navigation & Workflow Excellence): until now, this
 * page was a real, fully-built, real-data surface reachable only in a
 * closed loop with `/decision-drafts/:draftId/commit` -- no Tier-1 page
 * ever linked in, and this page had no link back out either. Fixed on
 * both ends: `InvestmentCasePage.tsx`'s Decision History tab now links
 * each Decision here, and this page now links back to that same
 * Investment Case (`decision.caseId`, already fetched).
 */

interface WorkspaceData {
  workspace: DecisionReasoningWorkspace;
  timeline: TimelineEntry[];
  caseActiveAssumptions: ActiveAssumptionRow[];
  caseActiveConditions: ActiveCaseConditionRow[];
  openDrafts: OpenDecisionDraftRow[];
}

async function loadAll(decisionId: string, signal: AbortSignal): Promise<WorkspaceData> {
  const workspace = await fetchDecisionReasoningWorkspace(decisionId, signal);

  const draftIds = [
    ...(workspace.originatingDraft ? [workspace.originatingDraft.draftId] : []),
    ...workspace.activeCaseDrafts.map((draft) => draft.draftId),
  ];

  const [draftEventLists, assumptionEventLists, conditionEventLists, caseActiveAssumptions, caseActiveConditions, openDrafts] =
    await Promise.all([
      Promise.all(draftIds.map((id) => fetchDecisionDraftEvents(id, signal))),
      Promise.all(workspace.assumptions.map((a) => fetchAssumptionEvents(a.assumptionId, signal))),
      Promise.all(workspace.caseConditions.map((c) => fetchCaseConditionEvents(c.conditionId, signal))),
      fetchActiveAssumptions(workspace.decision.caseId, signal),
      fetchActiveCaseConditions(workspace.decision.caseId, signal),
      fetchOpenDecisionDrafts(workspace.decision.userId, signal),
    ]);

  const timeline = buildReasoningTimeline({
    drafts: Object.fromEntries(draftIds.map((id, index) => [id, draftEventLists[index] ?? []])),
    assumptions: Object.fromEntries(
      workspace.assumptions.map((a, index) => [a.assumptionId, assumptionEventLists[index] ?? []]),
    ),
    caseConditions: Object.fromEntries(
      workspace.caseConditions.map((c, index) => [c.conditionId, conditionEventLists[index] ?? []]),
    ),
  });

  return { workspace, timeline, caseActiveAssumptions, caseActiveConditions, openDrafts };
}

export function DecisionWorkspacePage() {
  const { decisionId } = useParams<{ decisionId: string }>();
  const { t } = useTranslation();
  const [status, setStatus] = useState<AsyncStatus<WorkspaceData>>({ kind: "loading" });
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((token) => token + 1), []);

  useEffect(() => {
    if (!decisionId) return;
    const controller = new AbortController();
    setStatus({ kind: "loading" });
    loadAll(decisionId, controller.signal)
      .then((data) => setStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({ kind: "error", message: error instanceof Error ? error.message : t("common.unknownError") });
      });
    return () => controller.abort();
  }, [decisionId, reloadToken, t]);

  return (
    <Container width="wide">
      <Stack gap="inter-section">
        <Heading level={2}>{t("decisionWorkspace.heading")}</Heading>
        <AsyncSection
          status={status}
          loadingLabel={t("decisionWorkspace.loading")}
          errorLabel={(message) => t("decisionWorkspace.loadError", { message: message ?? t("common.unknownError") })}
        >
          {(data) => <DecisionWorkspaceContent data={data} onMutated={reload} />}
        </AsyncSection>
      </Stack>
    </Container>
  );
}

function DecisionWorkspaceContent({ data, onMutated }: { data: WorkspaceData; onMutated: () => void }) {
  const { t } = useTranslation();
  const { workspace, timeline, caseActiveAssumptions, caseActiveConditions, openDrafts } = data;
  const { decision, decisionContext, originatingDraft, activeCaseDrafts } = workspace;

  return (
    <Stack gap="inter-section">
      {/* Product Sprint 10 (Navigation & Workflow Excellence, Deliverable
          3 -- Back Navigation): this page previously had no way back to
          the Investment Case it belongs to -- a real dead end reachable
          only by browser Back. `decision.caseId` is already fetched,
          right here, so this costs nothing new. */}
      <RouterLink to={`/investment-case/${decision.caseId}`} style={ACCENT_LINK_STYLE}>
        {t("decisionWorkspace.backToInvestmentCase")}
      </RouterLink>

      <Surface tier="primary" bordered>
        <Stack gap="metadata">
          <Label>{t("decisionWorkspace.decisionSection.heading")}</Label>
          <Heading level={3}>{decision.subject}</Heading>
          <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
            <Text as="span">
              {t("decisionWorkspace.decisionSection.typeLabel")}: {decision.decisionType}
            </Text>
            <Text as="span">
              {t("decisionWorkspace.decisionSection.confidenceLabel")}: {decision.confidence}
            </Text>
            <Text as="span">
              {t("decisionWorkspace.decisionSection.decidedAtLabel")}: {new Date(decision.decidedAt).toLocaleDateString()}
            </Text>
          </Inline>
          <Text as="p" color="secondary">
            {decision.reason}
          </Text>
        </Stack>
      </Surface>

      <Surface tier="primary" bordered>
        <Stack gap="metadata">
          <Label>{t("decisionWorkspace.contextSection.heading")}</Label>
          {decisionContext ? (
            <Stack gap="row">
              <Text as="p">{decisionContext.situation}</Text>
              {decisionContext.portfolioRelevance && (
                <Text as="p" color="secondary">
                  {t("decisionWorkspace.contextSection.portfolioRelevanceLabel")}: {decisionContext.portfolioRelevance}
                </Text>
              )}
              {decisionContext.capitalConsiderations && (
                <Text as="p" color="secondary">
                  {t("decisionWorkspace.contextSection.capitalConsiderationsLabel")}: {decisionContext.capitalConsiderations}
                </Text>
              )}
              {decisionContext.alternativesConsidered.length > 0 && (
                <Text as="p" color="secondary">
                  {t("decisionWorkspace.contextSection.alternativesLabel")}: {decisionContext.alternativesConsidered.join(", ")}
                </Text>
              )}
              {decisionContext.uncertainties.length > 0 && (
                <Text as="p" color="secondary">
                  {t("decisionWorkspace.contextSection.uncertaintiesLabel")}: {decisionContext.uncertainties.join(", ")}
                </Text>
              )}
            </Stack>
          ) : (
            <Text color="secondary">{t("decisionWorkspace.contextSection.none")}</Text>
          )}
        </Stack>
      </Surface>

      <Stack gap="metadata">
        <Label>{t("decisionWorkspace.draftsSection.originatingHeading")}</Label>
        {originatingDraft ? (
          <Surface tier="primary" bordered>
            <Text as="p">{originatingDraft.subject ?? t("decisionWorkspace.draftsSection.subjectFallback")}</Text>
          </Surface>
        ) : (
          <Text color="secondary">{t("decisionWorkspace.draftsSection.originatingNone")}</Text>
        )}
      </Stack>

      <Stack gap="metadata">
        <Label>{t("decisionWorkspace.draftsSection.activeCaseHeading")}</Label>
        {activeCaseDrafts.length === 0 ? (
          <Text color="secondary">{t("decisionWorkspace.draftsSection.activeCaseNone")}</Text>
        ) : (
          <Stack gap="row">
            {activeCaseDrafts.map((draft) => (
              <Surface key={draft.draftId} tier="primary" bordered>
                <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
                  <Text as="span">{draft.subject ?? t("decisionWorkspace.draftsSection.subjectFallback")}</Text>
                  <RouterLink to={`/decision-drafts/${draft.draftId}/commit`} style={ACCENT_LINK_STYLE}>
                    {t("decisionWorkspace.commit.heading")}
                  </RouterLink>
                </Inline>
              </Surface>
            ))}
          </Stack>
        )}
      </Stack>

      <AssumptionsSection decisionId={decision.id} assumptions={workspace.assumptions} onMutated={onMutated} />

      <CaseConditionsSection
        caseId={decision.caseId}
        decisionId={decision.id}
        caseConditions={workspace.caseConditions}
        onMutated={onMutated}
      />

      <Stack gap="inter-section">
        <Heading level={3}>{t("decisionWorkspace.timeline.heading")}</Heading>
        <ReasoningTimelineView entries={timeline} />
      </Stack>

      <CaseWideReasoningSummary
        activeAssumptions={caseActiveAssumptions}
        activeConditions={caseActiveConditions}
        openDrafts={openDrafts}
      />
    </Stack>
  );
}

/** Sprint 13 §6 — the Case-scoped "Active Assumptions"/"Active
 * CaseConditions" read models (broader than the Decision-scoped ones
 * embedded in `workspace.assumptions`/`.caseConditions` above — these
 * span every Decision on the Case) and the user-scoped "Open Decision
 * Drafts" read model, each consumed exactly as Sprint 12 produces it,
 * with no client-side re-derivation of any of the three. */
function CaseWideReasoningSummary({
  activeAssumptions,
  activeConditions,
  openDrafts,
}: {
  activeAssumptions: ActiveAssumptionRow[];
  activeConditions: ActiveCaseConditionRow[];
  openDrafts: OpenDecisionDraftRow[];
}) {
  const { t } = useTranslation();
  return (
    <Surface tier="panel" bordered>
      <Stack gap="inter-section">
        <Stack gap="metadata">
          <Label>{t("decisionWorkspace.assumptions.heading")}</Label>
          <Text color="tertiary" as="span">
            {activeAssumptions.length}
          </Text>
        </Stack>
        <Stack gap="metadata">
          <Label>{t("decisionWorkspace.caseConditions.heading")}</Label>
          <Text color="tertiary" as="span">
            {activeConditions.length}
          </Text>
        </Stack>
        <Stack gap="metadata">
          <Label>{t("decisionWorkspace.draftsSection.activeCaseHeading")}</Label>
          {openDrafts.length === 0 ? (
            <Text color="secondary">{t("decisionWorkspace.draftsSection.activeCaseNone")}</Text>
          ) : (
            <Stack gap="row">
              {openDrafts.map((draft) => (
                <Text key={draft.draftId} as="span" color="secondary">
                  {draft.subject ?? t("decisionWorkspace.draftsSection.subjectFallback")}
                </Text>
              ))}
            </Stack>
          )}
        </Stack>
      </Stack>
    </Surface>
  );
}
