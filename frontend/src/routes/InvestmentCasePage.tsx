import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Button, Container, Divider, Heading, Link, Stack, Surface, Text } from "../foundation";

/**
 * Investment Case (Alpha Sprint 1A) — merges the former Investment Case
 * shell (Sprint 1, Commit 8) and Decision Workspace (Sprint 1, Commits
 * 9-11+) into the one shared Investment Case implementation Alpha Sprint
 * 1 requires ("Use one shared Investment Case implementation. Do not
 * create a separate Decision Workspace."). The `/decision-workspace/*`
 * routes are removed; every real workflow that used to live there
 * (Observation, Evidence, Knowledge Reference, Reasoning Trace,
 * Judgment, Decision, Outcome) now lives here, unchanged in behavior.
 *
 * TERMINOLOGY, corrected: the former docstring here read "Investment
 * Case... not yet a settled Atlas concept," citing the pre-reconciliation
 * state of Architecture-Governance.md and Atlas-Alpha-Baseline-v1.0.md.
 * That is now stale. As of this session's own Product Architecture
 * Reconciliation (commit 963b008), `APP-001` v0.4 §3.13 settles
 * "Investment Case" as the confirmed, 1:1 product-facing name for
 * atlas/core's own `Case` (`OE-002` §3.1), distinct from, and enclosing,
 * Decision Context — see `Architecture-Governance.md` §8.7.4 and
 * `Atlas-Alpha-Baseline-v1.0.md` §4/§6. `UX-012`'s own text has not
 * itself been updated to cite this resolution (a separate, UX-track
 * document edit, outside this sprint's scope) — but the Product-layer
 * question this page previously deferred on is closed.
 *
 * This page still does not adopt UX-012 §15's separately-defined
 * "Investment Workspace" reasoning sequence (Current Conclusion,
 * Supporting Factors, Challenges, ...), and does not fabricate any
 * Investment Case content with no backend model yet (Atlas assessment,
 * thesis, risks, conviction, valuation context, monitoring conditions —
 * per Alpha Sprint 1 Phase 4, "do not fabricate the full designed
 * Investment Case content that has no backend model yet"). It renders
 * exactly the real backend concepts that exist: Case, and every Core
 * Loop object already implemented beneath it.
 */

interface CaseSummary {
  caseId: string;
  recordedAt: string;
}

type CaseStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; case: CaseSummary };

/**
 * Shared shape for every "fetch the full list, scoped to this Case"
 * status (Observation, Evidence, Knowledge Reference, Reasoning Trace,
 * Judgment, Decision, Outcome all used seven byte-identical copies of
 * this same three-variant union before Integration Sprint 1 — collapsed
 * into one type here; no behavior changes, since all seven copies were
 * already structurally identical).
 */
type ListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

/**
 * Fetches the full, case-scoped list for one domain object type and
 * mirrors it into local state — the one fetch shape every section on
 * this page shares (Observation, Evidence, Knowledge Reference,
 * Reasoning Trace, Judgment, Decision, Outcome). Before Integration
 * Sprint 1, each section repeated this same effect body inline; this
 * hook replaces all seven copies with one, with no change in behavior:
 * same AbortController-per-effect cleanup, same loading/ready/error
 * transitions, same "ignore AbortError" catch.
 */
function useApiList<T>(
  url: string,
  caseId: string | undefined,
  setRecords: (records: T[]) => void,
  setStatus: (status: ListStatus) => void,
) {
  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setStatus({ kind: "loading" });

    fetch(url, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<T[]>;
      })
      .then((records) => {
        setRecords(records);
        setStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [url, caseId, setRecords, setStatus]);
}

/**
 * Deletes one record by id and mirrors the removal into local state —
 * the one delete shape every deletable section on this page shares
 * (Evidence, Knowledge Reference, Reasoning Trace, Judgment; Decision
 * and Outcome have no delete capability at all, per their own governing
 * design, so neither calls this). Before Integration Sprint 1, each
 * section repeated this same function body inline; this helper replaces
 * all four copies with one, with no change in behavior: same
 * deleting/idle/error transitions, same "404 counts as already gone"
 * tolerance.
 */
function deleteRecord<T>(
  url: string,
  id: string,
  matchesId: (record: T) => boolean,
  setRecords: (updater: (current: T[]) => T[]) => void,
  setDeleteStatus: (
    updater: (
      current: Record<string, "idle" | "deleting" | "error">,
    ) => Record<string, "idle" | "deleting" | "error">,
  ) => void,
) {
  setDeleteStatus((current) => ({ ...current, [id]: "deleting" }));

  fetch(url, { method: "DELETE" })
    .then((response) => {
      if (!response.ok && response.status !== 404) {
        throw new Error(`Backend responded with ${response.status}`);
      }
      setRecords((current) => current.filter((record) => !matchesId(record)));
      setDeleteStatus((current) => ({ ...current, [id]: "idle" }));
    })
    .catch(() => {
      setDeleteStatus((current) => ({ ...current, [id]: "error" }));
    });
}

interface ObservationRecord {
  observationId: string;
  caseId: string;
  subject: string;
  statement: string;
  observedAt: string;
}

type ObservationCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; observation: ObservationRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface EvidenceRecord {
  evidenceId: string;
  observationId: string;
  statement: string;
  direction: string;
  source: string | null;
  observedAt: string;
}

type EvidenceCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; evidence: EvidenceRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface EvidenceFormInput {
  summary: string;
  source: string;
  direction: "SUPPORTS" | "CHALLENGES";
}

const EMPTY_EVIDENCE_FORM: EvidenceFormInput = { summary: "", source: "", direction: "SUPPORTS" };

interface KnowledgeReferenceTarget {
  targetType: string;
  targetId: string;
}

interface KnowledgeReferenceRecord {
  knowledgeReferenceId: string;
  caseId: string;
  target: KnowledgeReferenceTarget;
  recordedAt: string;
}

type KnowledgeReferenceCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; knowledgeReference: KnowledgeReferenceRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface ReasoningTraceSupport {
  targetType: string;
  targetId: string;
}

interface ReasoningTraceRecord {
  reasoningTraceId: string;
  caseId: string;
  supports: ReasoningTraceSupport[];
  recordedAt: string;
}

type ReasoningTraceCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; reasoningTrace: ReasoningTraceRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface JudgmentSubject {
  targetType: string;
  targetId: string;
}

interface JudgmentRecord {
  judgmentId: string;
  caseId: string;
  characterization: string;
  subject: JudgmentSubject | null;
  recordedAt: string;
}

type JudgmentCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; judgment: JudgmentRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface DecisionRecord {
  id: string;
  caseId: string;
  userId: string;
  decisionType: string;
  subject: string;
  reason: string;
  confidence: number;
  decidedAt: string;
  recordedAt: string;
  source: string;
  observationId: string | null;
}

type DecisionCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; decision: DecisionRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface DecisionFormInput {
  decisionType: "BUY" | "SELL" | "HOLD" | "WATCH" | "PASS";
  subject: string;
  reason: string;
  confidence: string;
}

const EMPTY_DECISION_FORM: DecisionFormInput = {
  decisionType: "BUY",
  subject: "",
  reason: "",
  confidence: "50",
};

/**
 * Atlas Alpha has no login/session/identity system anywhere in this
 * frontend. The real backend's `Decision.user_id` is required, but per
 * the governing (unimplemented) Decision-Implementation-Design.md, it
 * "has no future semantic role" and is retained only as legacy
 * compatibility metadata — never shown to the investor. This fixed,
 * documented placeholder is used until Atlas Alpha has a real identity
 * system; it is not real user data, and no authentication is added.
 */
const ALPHA_PLACEHOLDER_USER_ID = "00000000-0000-0000-0000-000000000001";

interface OutcomeRecord {
  id: string;
  caseId: string;
  decisionId: string;
  statement: string;
  note: string | null;
  occurredAt: string;
  recordedAt: string;
}

type OutcomeCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; outcome: OutcomeRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

interface OutcomeFormInput {
  decisionId: string;
  statement: string;
  note: string;
}

const EMPTY_OUTCOME_FORM: OutcomeFormInput = { decisionId: "", statement: "", note: "" };

export function InvestmentCasePage() {
  const { caseId } = useParams<{ caseId?: string }>();
  const [status, setStatus] = useState<CaseStatus>({ kind: "loading" });

  const [observations, setObservations] = useState<ObservationRecord[]>([]);
  const [listStatus, setListStatus] = useState<ListStatus>({ kind: "loading" });
  const [createStatus, setCreateStatus] = useState<ObservationCreateStatus>({ kind: "idle" });
  const [subjectInput, setSubjectInput] = useState("");
  const [statementInput, setStatementInput] = useState("");

  const [allEvidence, setAllEvidence] = useState<EvidenceRecord[]>([]);
  const [evidenceListStatus, setEvidenceListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [evidenceCreateStatus, setEvidenceCreateStatus] = useState<
    Record<string, EvidenceCreateStatus>
  >({});
  const [evidenceForm, setEvidenceForm] = useState<Record<string, EvidenceFormInput>>({});
  const [evidenceDeleteStatus, setEvidenceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allKnowledgeReferences, setAllKnowledgeReferences] = useState<KnowledgeReferenceRecord[]>(
    [],
  );
  const [knowledgeReferenceListStatus, setKnowledgeReferenceListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [knowledgeReferenceCreateStatus, setKnowledgeReferenceCreateStatus] = useState<
    Record<string, KnowledgeReferenceCreateStatus>
  >({});
  const [knowledgeReferenceDeleteStatus, setKnowledgeReferenceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allReasoningTraces, setAllReasoningTraces] = useState<ReasoningTraceRecord[]>([]);
  const [reasoningTraceListStatus, setReasoningTraceListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [reasoningTraceCreateStatus, setReasoningTraceCreateStatus] = useState<
    Record<string, ReasoningTraceCreateStatus>
  >({});
  const [reasoningTraceDeleteStatus, setReasoningTraceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allJudgments, setAllJudgments] = useState<JudgmentRecord[]>([]);
  const [judgmentListStatus, setJudgmentListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [judgmentCreateStatus, setJudgmentCreateStatus] = useState<
    Record<string, JudgmentCreateStatus>
  >({});
  const [judgmentForm, setJudgmentForm] = useState<Record<string, string>>({});
  const [judgmentDeleteStatus, setJudgmentDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allDecisions, setAllDecisions] = useState<DecisionRecord[]>([]);
  const [decisionListStatus, setDecisionListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [decisionCreateStatus, setDecisionCreateStatus] = useState<
    Record<string, DecisionCreateStatus>
  >({});
  const [decisionForm, setDecisionForm] = useState<Record<string, DecisionFormInput>>({});

  const [allOutcomes, setAllOutcomes] = useState<OutcomeRecord[]>([]);
  const [outcomeListStatus, setOutcomeListStatus] = useState<ListStatus>({
    kind: "loading",
  });
  const [outcomeCreateStatus, setOutcomeCreateStatus] = useState<
    Record<string, OutcomeCreateStatus>
  >({});
  const [outcomeForm, setOutcomeForm] = useState<Record<string, OutcomeFormInput>>({});

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setStatus({ kind: "loading" });

    fetch(`/api/cases/${caseId}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<CaseSummary>;
      })
      .then((caseSummary) => setStatus({ kind: "loaded", case: caseSummary }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [caseId]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setListStatus({ kind: "loading" });

    fetch("/api/observations", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<ObservationRecord[]>;
      })
      .then((allObservations) => {
        setObservations(allObservations.filter((o) => o.caseId === caseId));
        setListStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setListStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [caseId]);

  useApiList<EvidenceRecord>("/api/evidence", caseId, setAllEvidence, setEvidenceListStatus);
  useApiList<KnowledgeReferenceRecord>(
    "/api/knowledge-references",
    caseId,
    setAllKnowledgeReferences,
    setKnowledgeReferenceListStatus,
  );
  useApiList<ReasoningTraceRecord>(
    "/api/reasoning-traces",
    caseId,
    setAllReasoningTraces,
    setReasoningTraceListStatus,
  );
  useApiList<JudgmentRecord>("/api/judgments", caseId, setAllJudgments, setJudgmentListStatus);
  useApiList<DecisionRecord>("/api/decisions", caseId, setAllDecisions, setDecisionListStatus);
  useApiList<OutcomeRecord>("/api/outcomes", caseId, setAllOutcomes, setOutcomeListStatus);

  function submitEvidence(observationId: string) {
    const form = evidenceForm[observationId] ?? EMPTY_EVIDENCE_FORM;
    setEvidenceCreateStatus((current) => ({ ...current, [observationId]: { kind: "submitting" } }));

    fetch("/api/evidence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        observationId,
        statement: form.summary,
        direction: form.direction,
        source: form.source || null,
        observedAt: new Date().toISOString(),
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setEvidenceCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? "Invalid input.",
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const evidence = (await response.json()) as EvidenceRecord;
        setAllEvidence((current) => [...current, evidence]);
        setEvidenceCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", evidence },
        }));
      })
      .catch((error: unknown) => {
        setEvidenceCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

  function deleteEvidence(evidenceId: string) {
    deleteRecord<EvidenceRecord>(
      `/api/evidence/${evidenceId}`,
      evidenceId,
      (e) => e.evidenceId === evidenceId,
      setAllEvidence,
      setEvidenceDeleteStatus,
    );
  }

  function submitKnowledgeReference(observationId: string) {
    if (!caseId) return;
    setKnowledgeReferenceCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/knowledge-references", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        target: { targetType: "Observation", targetId: observationId },
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setKnowledgeReferenceCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? "Invalid input.",
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const knowledgeReference = (await response.json()) as KnowledgeReferenceRecord;
        setAllKnowledgeReferences((current) => [...current, knowledgeReference]);
        setKnowledgeReferenceCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", knowledgeReference },
        }));
      })
      .catch((error: unknown) => {
        setKnowledgeReferenceCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

  function deleteKnowledgeReference(knowledgeReferenceId: string) {
    deleteRecord<KnowledgeReferenceRecord>(
      `/api/knowledge-references/${knowledgeReferenceId}`,
      knowledgeReferenceId,
      (k) => k.knowledgeReferenceId === knowledgeReferenceId,
      setAllKnowledgeReferences,
      setKnowledgeReferenceDeleteStatus,
    );
  }

  function submitReasoningTrace(observationId: string) {
    if (!caseId) return;
    setReasoningTraceCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/reasoning-traces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        supports: [{ targetType: "Observation", targetId: observationId }],
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setReasoningTraceCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? "Invalid input.",
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const reasoningTrace = (await response.json()) as ReasoningTraceRecord;
        setAllReasoningTraces((current) => [...current, reasoningTrace]);
        setReasoningTraceCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", reasoningTrace },
        }));
      })
      .catch((error: unknown) => {
        setReasoningTraceCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

  function deleteReasoningTrace(reasoningTraceId: string) {
    deleteRecord<ReasoningTraceRecord>(
      `/api/reasoning-traces/${reasoningTraceId}`,
      reasoningTraceId,
      (r) => r.reasoningTraceId === reasoningTraceId,
      setAllReasoningTraces,
      setReasoningTraceDeleteStatus,
    );
  }

  function submitJudgment(observationId: string) {
    if (!caseId) return;
    const characterization = judgmentForm[observationId] ?? "";
    setJudgmentCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/judgments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        characterization,
        subject: { targetType: "Observation", targetId: observationId },
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setJudgmentCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? "Invalid input.",
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const judgment = (await response.json()) as JudgmentRecord;
        setAllJudgments((current) => [...current, judgment]);
        setJudgmentCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", judgment },
        }));
      })
      .catch((error: unknown) => {
        setJudgmentCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

  function deleteJudgment(judgmentId: string) {
    deleteRecord<JudgmentRecord>(
      `/api/judgments/${judgmentId}`,
      judgmentId,
      (j) => j.judgmentId === judgmentId,
      setAllJudgments,
      setJudgmentDeleteStatus,
    );
  }

  function submitDecision(observationId: string) {
    if (!caseId) return;
    const form = decisionForm[observationId] ?? EMPTY_DECISION_FORM;
    const confidence = Number.parseInt(form.confidence, 10);
    setDecisionCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/decisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        userId: ALPHA_PLACEHOLDER_USER_ID,
        decisionType: form.decisionType,
        subject: form.subject,
        reason: form.reason,
        confidence,
        observationId,
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 422 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setDecisionCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 404 ? "api-error" : "validation-error",
              message: body.detail ?? "Invalid input.",
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const decision = (await response.json()) as DecisionRecord;
        setAllDecisions((current) => [...current, decision]);
        setDecisionCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", decision },
        }));
      })
      .catch((error: unknown) => {
        setDecisionCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

  function submitOutcome(observationId: string) {
    const form = outcomeForm[observationId] ?? EMPTY_OUTCOME_FORM;
    setOutcomeCreateStatus((current) => ({
      ...current,
      [observationId]: { kind: "submitting" },
    }));

    fetch("/api/outcomes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decisionId: form.decisionId,
        statement: form.statement,
        occurredAt: new Date().toISOString(),
        note: form.note || null,
      }),
    })
      .then(async (response) => {
        if (response.status === 400 || response.status === 404) {
          const body = (await response.json()) as { detail?: string };
          setOutcomeCreateStatus((current) => ({
            ...current,
            [observationId]: {
              kind: response.status === 400 ? "validation-error" : "api-error",
              message: body.detail ?? "Invalid input.",
            },
          }));
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const outcome = (await response.json()) as OutcomeRecord;
        setAllOutcomes((current) => [...current, outcome]);
        setOutcomeCreateStatus((current) => ({
          ...current,
          [observationId]: { kind: "success", outcome },
        }));
      })
      .catch((error: unknown) => {
        setOutcomeCreateStatus((current) => ({
          ...current,
          [observationId]: {
            kind: "api-error",
            message: error instanceof Error ? error.message : "Unknown error",
          },
        }));
      });
  }

  function submitObservation() {
    if (!caseId) return;
    setCreateStatus({ kind: "submitting" });

    fetch("/api/observations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId,
        subject: subjectInput,
        statement: statementInput,
        observedAt: new Date().toISOString(),
      }),
    })
      .then(async (response) => {
        if (response.status === 400) {
          const body = (await response.json()) as { detail?: string };
          setCreateStatus({ kind: "validation-error", message: body.detail ?? "Invalid input." });
          return;
        }
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        const observation = (await response.json()) as ObservationRecord;
        setObservations((current) => [...current, observation]);
        setCreateStatus({ kind: "success", observation });
      })
      .catch((error: unknown) => {
        setCreateStatus({
          kind: "api-error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });
  }

  return (
    <Container>
      <Stack gap="inter-section">
        {/* Header — UX-012B §20: identity area, subject identity, return
            navigation control (all required); status indicator
            (optional). Merged from the former Investment Case shell and
            Decision Workspace headers (Alpha Sprint 1A). */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={1}>Investment Case</Heading>
            <Link href="/portfolio">← Return to Portfolio</Link>
            {!caseId && <Text color="secondary">No case selected.</Text>}
            {caseId && status.kind === "loading" && (
              <Text role="status" aria-live="polite">
                Loading…
              </Text>
            )}
            {caseId && status.kind === "error" && (
              <Text color="tertiary" role="alert">
                Could not load this case: {status.message}
              </Text>
            )}
            {caseId && status.kind === "loaded" && (
              <Text>Subject: Case {status.case.caseId}</Text>
            )}
          </Stack>
        </Surface>

        <Divider />

        {/* Status area — UX-012B §20's own Workspace Header "status
            indicator" optional element, surfaced here as its own region
            per this task's own suggested structure. No monitoring or
            draft/historical state exists yet for a shell with no
            editable content, so this is a placeholder only. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Status</Heading>
            <Text color="secondary">
              Reserved for draft, historical, and monitoring status indicators in a future
              commit.
            </Text>
          </Stack>
        </Surface>

        <Divider />

        {/* Primary Work Area — UX-012B §20's Workspace Frame "body"
            required element. Observation Capture Flow (Commit 10) lives
            here; reasoning and decision recording (UX-012 §17) remain
            out of scope. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Primary Work Area</Heading>

            {!caseId && <Text color="secondary">No case selected.</Text>}

            {caseId && (
              <Stack gap="inter-section">
                <Heading level={3}>Observations</Heading>

                {listStatus.kind === "loading" && (
                  <Text role="status" aria-live="polite">
                    Loading observations…
                  </Text>
                )}
                {listStatus.kind === "error" && (
                  <Text color="tertiary" role="alert">
                    Could not load observations: {listStatus.message}
                  </Text>
                )}
                {listStatus.kind === "ready" && observations.length === 0 && (
                  <Text color="secondary">No observations recorded yet.</Text>
                )}
                {listStatus.kind === "ready" && observations.length > 0 && (
                  <Stack gap="inter-section">
                    {observations.map((observation) => {
                      const evidenceForObservation = allEvidence.filter(
                        (e) => e.observationId === observation.observationId,
                      );
                      const thisCreateStatus: EvidenceCreateStatus = evidenceCreateStatus[
                        observation.observationId
                      ] ?? { kind: "idle" };
                      const thisForm: EvidenceFormInput =
                        evidenceForm[observation.observationId] ?? EMPTY_EVIDENCE_FORM;

                      const knowledgeReferencesForObservation = allKnowledgeReferences.filter(
                        (k) =>
                          k.target.targetType === "Observation" &&
                          k.target.targetId === observation.observationId,
                      );
                      const thisKnowledgeReferenceCreateStatus: KnowledgeReferenceCreateStatus =
                        knowledgeReferenceCreateStatus[observation.observationId] ?? {
                          kind: "idle",
                        };

                      const reasoningTracesForObservation = allReasoningTraces.filter((trace) =>
                        trace.supports.some(
                          (support) =>
                            support.targetType === "Observation" &&
                            support.targetId === observation.observationId,
                        ),
                      );
                      const thisReasoningTraceCreateStatus: ReasoningTraceCreateStatus =
                        reasoningTraceCreateStatus[observation.observationId] ?? { kind: "idle" };

                      const judgmentsForObservation = allJudgments.filter(
                        (judgment) =>
                          judgment.subject !== null &&
                          judgment.subject.targetType === "Observation" &&
                          judgment.subject.targetId === observation.observationId,
                      );
                      const thisJudgmentCreateStatus: JudgmentCreateStatus =
                        judgmentCreateStatus[observation.observationId] ?? { kind: "idle" };
                      const thisJudgmentForm = judgmentForm[observation.observationId] ?? "";

                      const decisionsForObservation = allDecisions.filter(
                        (decision) => decision.observationId === observation.observationId,
                      );
                      const thisDecisionCreateStatus: DecisionCreateStatus =
                        decisionCreateStatus[observation.observationId] ?? { kind: "idle" };
                      const thisDecisionForm: DecisionFormInput =
                        decisionForm[observation.observationId] ?? EMPTY_DECISION_FORM;

                      const decisionIdsForObservation = new Set(
                        decisionsForObservation.map((decision) => decision.id),
                      );
                      const outcomesForObservation = allOutcomes.filter((outcome) =>
                        decisionIdsForObservation.has(outcome.decisionId),
                      );
                      const thisOutcomeCreateStatus: OutcomeCreateStatus =
                        outcomeCreateStatus[observation.observationId] ?? { kind: "idle" };
                      const thisOutcomeForm: OutcomeFormInput = outcomeForm[
                        observation.observationId
                      ] ?? {
                        ...EMPTY_OUTCOME_FORM,
                        decisionId:
                          decisionsForObservation.length === 1
                            ? decisionsForObservation[0]?.id ?? ""
                            : "",
                      };

                      return (
                        <div key={observation.observationId}>
                          <Text>{observation.subject}</Text>
                          <Text color="secondary" as="p">
                            {observation.statement}
                          </Text>
                          <Text color="tertiary" as="p">
                            {observation.observedAt}
                          </Text>

                          <Stack gap="inter-section">
                            <Heading level={4}>Evidence</Heading>

                            {evidenceListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                Loading evidence…
                              </Text>
                            )}
                            {evidenceListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                Could not load evidence: {evidenceListStatus.message}
                              </Text>
                            )}
                            {evidenceListStatus.kind === "ready" &&
                              evidenceForObservation.length === 0 && (
                                <Text color="secondary">No evidence recorded yet.</Text>
                              )}
                            {evidenceListStatus.kind === "ready" &&
                              evidenceForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {evidenceForObservation.map((evidence) => (
                                    <div key={evidence.evidenceId}>
                                      <Text>{evidence.statement}</Text>
                                      <Text color="secondary" as="p">
                                        {evidence.direction}
                                        {evidence.source ? ` — ${evidence.source}` : ""}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() => deleteEvidence(evidence.evidenceId)}
                                        disabled={
                                          evidenceDeleteStatus[evidence.evidenceId] === "deleting"
                                        }
                                      >
                                        {evidenceDeleteStatus[evidence.evidenceId] === "deleting"
                                          ? "Deleting…"
                                          : "Delete"}
                                      </Button>
                                      {evidenceDeleteStatus[evidence.evidenceId] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          Could not delete this evidence.
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setEvidenceCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                + Add Evidence
                              </Button>
                            )}

                            {thisCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  Evidence recorded: {thisCreateStatus.evidence.statement}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setEvidenceForm((current) => ({
                                      ...current,
                                      [observation.observationId]: EMPTY_EVIDENCE_FORM,
                                    }));
                                    setEvidenceCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  Add another
                                </Button>
                              </Stack>
                            )}

                            {(thisCreateStatus.kind === "creating" ||
                              thisCreateStatus.kind === "submitting" ||
                              thisCreateStatus.kind === "validation-error" ||
                              thisCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text as="label">
                                  Summary
                                  <br />
                                  <input
                                    value={thisForm.summary}
                                    onChange={(event) =>
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisForm,
                                          summary: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  Source
                                  <br />
                                  <input
                                    value={thisForm.source}
                                    onChange={(event) =>
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisForm,
                                          source: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  Direction
                                  <br />
                                  <select
                                    value={thisForm.direction}
                                    onChange={(event) =>
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisForm,
                                          direction: event.target.value as "SUPPORTS" | "CHALLENGES",
                                        },
                                      }))
                                    }
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  >
                                    <option value="SUPPORTS">Supports</option>
                                    <option value="CHALLENGES">Challenges</option>
                                  </select>
                                </Text>

                                {thisCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisCreateStatus.message}
                                  </Text>
                                )}
                                {thisCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    Could not record this evidence: {thisCreateStatus.message}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitEvidence(observation.observationId)}
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  >
                                    {thisCreateStatus.kind === "submitting"
                                      ? "Submitting…"
                                      : "Submit"}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setEvidenceForm((current) => ({
                                        ...current,
                                        [observation.observationId]: EMPTY_EVIDENCE_FORM,
                                      }));
                                      setEvidenceCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisCreateStatus.kind === "submitting"}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>Knowledge References</Heading>

                            {knowledgeReferenceListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                Loading knowledge references…
                              </Text>
                            )}
                            {knowledgeReferenceListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                Could not load knowledge references:{" "}
                                {knowledgeReferenceListStatus.message}
                              </Text>
                            )}
                            {knowledgeReferenceListStatus.kind === "ready" &&
                              knowledgeReferencesForObservation.length === 0 && (
                                <Text color="secondary">No knowledge references recorded yet.</Text>
                              )}
                            {knowledgeReferenceListStatus.kind === "ready" &&
                              knowledgeReferencesForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {knowledgeReferencesForObservation.map((knowledgeReference) => (
                                    <div key={knowledgeReference.knowledgeReferenceId}>
                                      <Text>
                                        Knowledge Reference {knowledgeReference.knowledgeReferenceId}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        {knowledgeReference.recordedAt}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() =>
                                          deleteKnowledgeReference(
                                            knowledgeReference.knowledgeReferenceId,
                                          )
                                        }
                                        disabled={
                                          knowledgeReferenceDeleteStatus[
                                            knowledgeReference.knowledgeReferenceId
                                          ] === "deleting"
                                        }
                                      >
                                        {knowledgeReferenceDeleteStatus[
                                          knowledgeReference.knowledgeReferenceId
                                        ] === "deleting"
                                          ? "Deleting…"
                                          : "Delete"}
                                      </Button>
                                      {knowledgeReferenceDeleteStatus[
                                        knowledgeReference.knowledgeReferenceId
                                      ] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          Could not delete this knowledge reference.
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisKnowledgeReferenceCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setKnowledgeReferenceCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                + Add Knowledge Reference
                              </Button>
                            )}

                            {thisKnowledgeReferenceCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  Knowledge reference recorded:{" "}
                                  {
                                    thisKnowledgeReferenceCreateStatus.knowledgeReference
                                      .knowledgeReferenceId
                                  }
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() =>
                                    setKnowledgeReferenceCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }))
                                  }
                                >
                                  Add another
                                </Button>
                              </Stack>
                            )}

                            {(thisKnowledgeReferenceCreateStatus.kind === "creating" ||
                              thisKnowledgeReferenceCreateStatus.kind === "submitting" ||
                              thisKnowledgeReferenceCreateStatus.kind === "validation-error" ||
                              thisKnowledgeReferenceCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text color="secondary">
                                  Record a Knowledge Reference for this Observation.
                                </Text>

                                {thisKnowledgeReferenceCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisKnowledgeReferenceCreateStatus.message}
                                  </Text>
                                )}
                                {thisKnowledgeReferenceCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    Could not record this knowledge reference:{" "}
                                    {thisKnowledgeReferenceCreateStatus.message}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() =>
                                      submitKnowledgeReference(observation.observationId)
                                    }
                                    disabled={thisKnowledgeReferenceCreateStatus.kind === "submitting"}
                                  >
                                    {thisKnowledgeReferenceCreateStatus.kind === "submitting"
                                      ? "Submitting…"
                                      : "Submit"}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() =>
                                      setKnowledgeReferenceCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }))
                                    }
                                    disabled={thisKnowledgeReferenceCreateStatus.kind === "submitting"}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>Reasoning Trace</Heading>

                            {reasoningTraceListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                Loading reasoning trace…
                              </Text>
                            )}
                            {reasoningTraceListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                Could not load reasoning trace: {reasoningTraceListStatus.message}
                              </Text>
                            )}
                            {reasoningTraceListStatus.kind === "ready" &&
                              reasoningTracesForObservation.length === 0 && (
                                <Text color="secondary">No reasoning trace recorded yet.</Text>
                              )}
                            {reasoningTraceListStatus.kind === "ready" &&
                              reasoningTracesForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {reasoningTracesForObservation.map((reasoningTrace) => (
                                    <div key={reasoningTrace.reasoningTraceId}>
                                      <Text>Reasoning Trace {reasoningTrace.reasoningTraceId}</Text>
                                      <Text color="tertiary" as="p">
                                        {reasoningTrace.recordedAt}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() =>
                                          deleteReasoningTrace(reasoningTrace.reasoningTraceId)
                                        }
                                        disabled={
                                          reasoningTraceDeleteStatus[
                                            reasoningTrace.reasoningTraceId
                                          ] === "deleting"
                                        }
                                      >
                                        {reasoningTraceDeleteStatus[
                                          reasoningTrace.reasoningTraceId
                                        ] === "deleting"
                                          ? "Deleting…"
                                          : "Delete"}
                                      </Button>
                                      {reasoningTraceDeleteStatus[
                                        reasoningTrace.reasoningTraceId
                                      ] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          Could not delete this reasoning trace.
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisReasoningTraceCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setReasoningTraceCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                + Create Reasoning Trace
                              </Button>
                            )}

                            {thisReasoningTraceCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  Reasoning trace recorded:{" "}
                                  {thisReasoningTraceCreateStatus.reasoningTrace.reasoningTraceId}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() =>
                                    setReasoningTraceCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }))
                                  }
                                >
                                  Add another
                                </Button>
                              </Stack>
                            )}

                            {(thisReasoningTraceCreateStatus.kind === "creating" ||
                              thisReasoningTraceCreateStatus.kind === "submitting" ||
                              thisReasoningTraceCreateStatus.kind === "validation-error" ||
                              thisReasoningTraceCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text color="secondary">
                                  Record a Reasoning Trace supported by this Observation.
                                </Text>

                                {thisReasoningTraceCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisReasoningTraceCreateStatus.message}
                                  </Text>
                                )}
                                {thisReasoningTraceCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    Could not record this reasoning trace:{" "}
                                    {thisReasoningTraceCreateStatus.message}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitReasoningTrace(observation.observationId)}
                                    disabled={thisReasoningTraceCreateStatus.kind === "submitting"}
                                  >
                                    {thisReasoningTraceCreateStatus.kind === "submitting"
                                      ? "Submitting…"
                                      : "Submit"}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() =>
                                      setReasoningTraceCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }))
                                    }
                                    disabled={thisReasoningTraceCreateStatus.kind === "submitting"}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>Judgment</Heading>

                            {judgmentListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                Loading judgment…
                              </Text>
                            )}
                            {judgmentListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                Could not load judgment: {judgmentListStatus.message}
                              </Text>
                            )}
                            {judgmentListStatus.kind === "ready" &&
                              judgmentsForObservation.length === 0 && (
                                <Text color="secondary">No judgment recorded yet.</Text>
                              )}
                            {judgmentListStatus.kind === "ready" &&
                              judgmentsForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {judgmentsForObservation.map((judgment) => (
                                    <div key={judgment.judgmentId}>
                                      <Text>{judgment.characterization}</Text>
                                      <Text color="tertiary" as="p">
                                        {judgment.recordedAt}
                                      </Text>
                                      <Button
                                        variant="tertiary"
                                        onClick={() => deleteJudgment(judgment.judgmentId)}
                                        disabled={
                                          judgmentDeleteStatus[judgment.judgmentId] === "deleting"
                                        }
                                      >
                                        {judgmentDeleteStatus[judgment.judgmentId] === "deleting"
                                          ? "Deleting…"
                                          : "Delete"}
                                      </Button>
                                      {judgmentDeleteStatus[judgment.judgmentId] === "error" && (
                                        <Text color="tertiary" role="alert">
                                          Could not delete this judgment.
                                        </Text>
                                      )}
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisJudgmentCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setJudgmentCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                + Create Judgment
                              </Button>
                            )}

                            {thisJudgmentCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  Judgment recorded: {thisJudgmentCreateStatus.judgment.characterization}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setJudgmentForm((current) => ({
                                      ...current,
                                      [observation.observationId]: "",
                                    }));
                                    setJudgmentCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  Add another
                                </Button>
                              </Stack>
                            )}

                            {(thisJudgmentCreateStatus.kind === "creating" ||
                              thisJudgmentCreateStatus.kind === "submitting" ||
                              thisJudgmentCreateStatus.kind === "validation-error" ||
                              thisJudgmentCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text as="label">
                                  Characterization
                                  <br />
                                  <textarea
                                    value={thisJudgmentForm}
                                    onChange={(event) =>
                                      setJudgmentForm((current) => ({
                                        ...current,
                                        [observation.observationId]: event.target.value,
                                      }))
                                    }
                                    disabled={thisJudgmentCreateStatus.kind === "submitting"}
                                  />
                                </Text>

                                {thisJudgmentCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisJudgmentCreateStatus.message}
                                  </Text>
                                )}
                                {thisJudgmentCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    Could not record this judgment: {thisJudgmentCreateStatus.message}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitJudgment(observation.observationId)}
                                    disabled={thisJudgmentCreateStatus.kind === "submitting"}
                                  >
                                    {thisJudgmentCreateStatus.kind === "submitting"
                                      ? "Submitting…"
                                      : "Submit"}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setJudgmentForm((current) => ({
                                        ...current,
                                        [observation.observationId]: "",
                                      }));
                                      setJudgmentCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisJudgmentCreateStatus.kind === "submitting"}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>Decision</Heading>

                            {decisionListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                Loading decision…
                              </Text>
                            )}
                            {decisionListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                Could not load decision: {decisionListStatus.message}
                              </Text>
                            )}
                            {decisionListStatus.kind === "ready" &&
                              decisionsForObservation.length === 0 && (
                                <Text color="secondary">No decision recorded yet.</Text>
                              )}
                            {decisionListStatus.kind === "ready" &&
                              decisionsForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {decisionsForObservation.map((decision) => (
                                    <div key={decision.id}>
                                      <Text>
                                        {decision.decisionType} — {decision.subject}
                                      </Text>
                                      <Text color="secondary" as="p">
                                        {decision.reason}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        Confidence: {decision.confidence}
                                      </Text>
                                      <Text color="tertiary" as="p">
                                        {decision.decidedAt}
                                      </Text>
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {thisDecisionCreateStatus.kind === "idle" && (
                              <Button
                                variant="tertiary"
                                onClick={() =>
                                  setDecisionCreateStatus((current) => ({
                                    ...current,
                                    [observation.observationId]: { kind: "creating" },
                                  }))
                                }
                              >
                                + Record Decision
                              </Button>
                            )}

                            {thisDecisionCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  Decision recorded: {thisDecisionCreateStatus.decision.decisionType}{" "}
                                  — {thisDecisionCreateStatus.decision.subject}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setDecisionForm((current) => ({
                                      ...current,
                                      [observation.observationId]: EMPTY_DECISION_FORM,
                                    }));
                                    setDecisionCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  Add another
                                </Button>
                              </Stack>
                            )}

                            {(thisDecisionCreateStatus.kind === "creating" ||
                              thisDecisionCreateStatus.kind === "submitting" ||
                              thisDecisionCreateStatus.kind === "validation-error" ||
                              thisDecisionCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                <Text as="label">
                                  Decision Type
                                  <br />
                                  <select
                                    value={thisDecisionForm.decisionType}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          decisionType: event.target.value as
                                            | "BUY"
                                            | "SELL"
                                            | "HOLD"
                                            | "WATCH"
                                            | "PASS",
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  >
                                    <option value="BUY">Buy</option>
                                    <option value="SELL">Sell</option>
                                    <option value="HOLD">Hold</option>
                                    <option value="WATCH">Watch</option>
                                    <option value="PASS">Pass</option>
                                  </select>
                                </Text>
                                <Text as="label">
                                  Subject
                                  <br />
                                  <input
                                    value={thisDecisionForm.subject}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          subject: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  Reason
                                  <br />
                                  <textarea
                                    value={thisDecisionForm.reason}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          reason: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  Confidence (0-100)
                                  <br />
                                  <input
                                    type="number"
                                    min={0}
                                    max={100}
                                    value={thisDecisionForm.confidence}
                                    onChange={(event) =>
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisDecisionForm,
                                          confidence: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  />
                                </Text>

                                {thisDecisionCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisDecisionCreateStatus.message}
                                  </Text>
                                )}
                                {thisDecisionCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    Could not record this decision: {thisDecisionCreateStatus.message}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitDecision(observation.observationId)}
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  >
                                    {thisDecisionCreateStatus.kind === "submitting"
                                      ? "Submitting…"
                                      : "Submit"}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setDecisionForm((current) => ({
                                        ...current,
                                        [observation.observationId]: EMPTY_DECISION_FORM,
                                      }));
                                      setDecisionCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisDecisionCreateStatus.kind === "submitting"}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>

                          <Stack gap="inter-section">
                            <Heading level={4}>Outcome</Heading>

                            {outcomeListStatus.kind === "loading" && (
                              <Text role="status" aria-live="polite">
                                Loading outcome…
                              </Text>
                            )}
                            {outcomeListStatus.kind === "error" && (
                              <Text color="tertiary" role="alert">
                                Could not load outcome: {outcomeListStatus.message}
                              </Text>
                            )}
                            {outcomeListStatus.kind === "ready" &&
                              outcomesForObservation.length === 0 && (
                                <Text color="secondary">No outcome recorded yet.</Text>
                              )}
                            {outcomeListStatus.kind === "ready" &&
                              outcomesForObservation.length > 0 && (
                                <Stack gap="inter-section">
                                  {outcomesForObservation.map((outcome) => (
                                    <div key={outcome.id}>
                                      <Text>{outcome.statement}</Text>
                                      {outcome.note && (
                                        <Text color="secondary" as="p">
                                          {outcome.note}
                                        </Text>
                                      )}
                                      <Text color="tertiary" as="p">
                                        {outcome.occurredAt}
                                      </Text>
                                    </div>
                                  ))}
                                </Stack>
                              )}

                            <Divider tone="hairline" />

                            {decisionsForObservation.length === 0 && (
                              <Text color="secondary">
                                No decision recorded yet — record a Decision first.
                              </Text>
                            )}

                            {decisionsForObservation.length > 0 &&
                              thisOutcomeCreateStatus.kind === "idle" && (
                                <Button
                                  variant="tertiary"
                                  onClick={() =>
                                    setOutcomeCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }))
                                  }
                                >
                                  + Record Outcome
                                </Button>
                              )}

                            {thisOutcomeCreateStatus.kind === "success" && (
                              <Stack gap="inter-section">
                                <Text>
                                  Outcome recorded: {thisOutcomeCreateStatus.outcome.statement}
                                </Text>
                                <Button
                                  variant="tertiary"
                                  onClick={() => {
                                    setOutcomeForm((current) => ({
                                      ...current,
                                      [observation.observationId]: {
                                        ...EMPTY_OUTCOME_FORM,
                                        decisionId:
                                          decisionsForObservation.length === 1
                                            ? decisionsForObservation[0]?.id ?? ""
                                            : "",
                                      },
                                    }));
                                    setOutcomeCreateStatus((current) => ({
                                      ...current,
                                      [observation.observationId]: { kind: "creating" },
                                    }));
                                  }}
                                >
                                  Add another
                                </Button>
                              </Stack>
                            )}

                            {(thisOutcomeCreateStatus.kind === "creating" ||
                              thisOutcomeCreateStatus.kind === "submitting" ||
                              thisOutcomeCreateStatus.kind === "validation-error" ||
                              thisOutcomeCreateStatus.kind === "api-error") && (
                              <Stack gap="inter-section">
                                {decisionsForObservation.length > 1 && (
                                  <Text as="label">
                                    Decision
                                    <br />
                                    <select
                                      value={thisOutcomeForm.decisionId}
                                      onChange={(event) =>
                                        setOutcomeForm((current) => ({
                                          ...current,
                                          [observation.observationId]: {
                                            ...thisOutcomeForm,
                                            decisionId: event.target.value,
                                          },
                                        }))
                                      }
                                      disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                    >
                                      <option value="">Select a decision…</option>
                                      {decisionsForObservation.map((decision) => (
                                        <option key={decision.id} value={decision.id}>
                                          {decision.decisionType} — {decision.subject}
                                        </option>
                                      ))}
                                    </select>
                                  </Text>
                                )}
                                <Text as="label">
                                  Statement
                                  <br />
                                  <textarea
                                    value={thisOutcomeForm.statement}
                                    onChange={(event) =>
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisOutcomeForm,
                                          statement: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  />
                                </Text>
                                <Text as="label">
                                  Note (optional)
                                  <br />
                                  <textarea
                                    value={thisOutcomeForm.note}
                                    onChange={(event) =>
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...thisOutcomeForm,
                                          note: event.target.value,
                                        },
                                      }))
                                    }
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  />
                                </Text>

                                {thisOutcomeCreateStatus.kind === "validation-error" && (
                                  <Text color="tertiary" role="alert">
                                    {thisOutcomeCreateStatus.message}
                                  </Text>
                                )}
                                {thisOutcomeCreateStatus.kind === "api-error" && (
                                  <Text color="tertiary" role="alert">
                                    Could not record this outcome: {thisOutcomeCreateStatus.message}
                                  </Text>
                                )}

                                <div>
                                  <Button
                                    variant="primary"
                                    onClick={() => submitOutcome(observation.observationId)}
                                    disabled={
                                      thisOutcomeCreateStatus.kind === "submitting" ||
                                      !thisOutcomeForm.decisionId
                                    }
                                  >
                                    {thisOutcomeCreateStatus.kind === "submitting"
                                      ? "Submitting…"
                                      : "Submit"}
                                  </Button>{" "}
                                  <Button
                                    variant="tertiary"
                                    onClick={() => {
                                      setOutcomeForm((current) => ({
                                        ...current,
                                        [observation.observationId]: {
                                          ...EMPTY_OUTCOME_FORM,
                                          decisionId:
                                            decisionsForObservation.length === 1
                                              ? decisionsForObservation[0]?.id ?? ""
                                              : "",
                                        },
                                      }));
                                      setOutcomeCreateStatus((current) => ({
                                        ...current,
                                        [observation.observationId]: { kind: "idle" },
                                      }));
                                    }}
                                    disabled={thisOutcomeCreateStatus.kind === "submitting"}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </Stack>
                            )}
                          </Stack>
                        </div>
                      );
                    })}
                  </Stack>
                )}

                <Divider tone="hairline" />

                {createStatus.kind === "idle" && (
                  <Button
                    variant="tertiary"
                    onClick={() => setCreateStatus({ kind: "creating" })}
                  >
                    Add Observation
                  </Button>
                )}

                {createStatus.kind === "success" && (
                  <Stack gap="inter-section">
                    <Text>Observation recorded: {createStatus.observation.subject}</Text>
                    <Button
                      variant="tertiary"
                      onClick={() => {
                        setSubjectInput("");
                        setStatementInput("");
                        setCreateStatus({ kind: "creating" });
                      }}
                    >
                      Add another
                    </Button>
                  </Stack>
                )}

                {(createStatus.kind === "creating" ||
                  createStatus.kind === "submitting" ||
                  createStatus.kind === "validation-error" ||
                  createStatus.kind === "api-error") && (
                  <Stack gap="inter-section">
                    <Text as="label">
                      Subject
                      <br />
                      <input
                        value={subjectInput}
                        onChange={(event) => setSubjectInput(event.target.value)}
                        disabled={createStatus.kind === "submitting"}
                      />
                    </Text>
                    <Text as="label">
                      Statement
                      <br />
                      <textarea
                        value={statementInput}
                        onChange={(event) => setStatementInput(event.target.value)}
                        disabled={createStatus.kind === "submitting"}
                      />
                    </Text>

                    {createStatus.kind === "validation-error" && (
                      <Text color="tertiary" role="alert">
                        {createStatus.message}
                      </Text>
                    )}
                    {createStatus.kind === "api-error" && (
                      <Text color="tertiary" role="alert">
                        Could not record this observation: {createStatus.message}
                      </Text>
                    )}

                    <div>
                      <Button
                        variant="primary"
                        onClick={submitObservation}
                        disabled={createStatus.kind === "submitting"}
                      >
                        {createStatus.kind === "submitting" ? "Submitting…" : "Submit"}
                      </Button>{" "}
                      <Button
                        variant="tertiary"
                        onClick={() => {
                          setSubjectInput("");
                          setStatementInput("");
                          setCreateStatus({ kind: "idle" });
                        }}
                        disabled={createStatus.kind === "submitting"}
                      >
                        Cancel
                      </Button>
                    </div>
                  </Stack>
                )}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        {/* Timeline / History placeholder — UX-012B §20's own Historical
            Indicator concept, and the settled Decision Timeline concept
            (UXD-R-094 / the Atlas Memory Status Investigation). Neither
            is implemented here. */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Timeline</Heading>
            <Text color="secondary">
              Reserved for this Decision's own Decision Timeline in a future commit.
            </Text>
          </Stack>
        </Surface>

        <Divider />

        {/* Footer — UX-012B §20's Workspace Frame "footer" required element. */}
        <Surface tier="primary">
          <Heading level={2}>Footer</Heading>
        </Surface>
      </Stack>
    </Container>
  );
}
