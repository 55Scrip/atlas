import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Button, Container, Divider, Heading, Link, Stack, Surface, Text } from "../foundation";

interface CaseSummary {
  caseId: string;
  recordedAt: string;
}

type CaseStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; case: CaseSummary };

interface ObservationRecord {
  observationId: string;
  caseId: string;
  subject: string;
  statement: string;
  observedAt: string;
}

type ObservationListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

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

type EvidenceListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

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

type KnowledgeReferenceListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

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

type ReasoningTraceListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

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

type JudgmentListStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready" };

type JudgmentCreateStatus =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "submitting" }
  | { kind: "success"; judgment: JudgmentRecord }
  | { kind: "validation-error"; message: string }
  | { kind: "api-error"; message: string };

/**
 * Decision Workspace Shell (Sprint 1, Commit 9) — structural layout only.
 *
 * Region set is drawn from UX-012B §20's own cross-Workspace components,
 * not invented: Workspace Frame ("identity area, return navigation,
 * body, footer" — required elements) and Workspace Header ("Workspace
 * name, subject identity, return navigation control," with "status
 * indicator" as an optional element). No Decision Workspace-specific
 * content (UX-012 §17's own 13-step reasoning sequence — Proposed
 * Decision, Supporting Factors, Challenges, Final Decision Card, etc.)
 * is implemented; that is reasoning and decision-recording behavior,
 * explicitly out of scope for a structural shell.
 *
 * No Context Panel: UX-012A's own Layout foundations state "no
 * persistent side panels" as a general principle, reinforced by its own
 * Workspace-body text ("not through a persistent sidebar — a persistent
 * sidebar would compete with the document reading experience and would
 * present poorly on smaller screens"). No component named "Context
 * Panel" exists anywhere in UX-012B's own Workspace Components section
 * either. It is not built here, matching the same evidence-based
 * exclusion already applied to the Dashboard's own layout (Commit 6).
 *
 * Live data: reuses the identical `GET /cases/{caseId}` call the
 * Investment Case shell (Commit 8) already makes for the header's
 * subject identity. No Decision or other domain object is fetched.
 *
 * Sprint 1, Commit 10 — Observation Capture Flow: the Primary Work Area
 * now hosts the first real, functional workflow. `GET /observations`
 * (atlas/core, unmodified) has no case_id filter — its own router
 * comment states plainly "No filtering" — so the real, complete list is
 * fetched once and narrowed client-side to this Case's own observations
 * by exact `caseId` match. This is the "Remain inside the current Case"
 * requirement, not the "Filtering" UI feature this commit's own scope
 * excludes (a search/filter control) — no such control exists here, and
 * the fetched-and-matched list is rendered in the order the backend
 * returns it, with no client-side sort.
 *
 * Creating an Observation submits only the two fields atlas/core's own
 * `Subject`/`Statement` value objects require (both reject empty or
 * whitespace-only values, raising a real `ObservationValidationError` ->
 * HTTP 400 — this is the Validation Error state below, not a duplicated
 * client-side rule). `observedAt` is set to the real submission instant
 * (`new Date().toISOString()`), matching the same "record what is true
 * right now" pattern `Case.create()` already uses for `recorded_at` —
 * not a separately exposed field, to keep this flow intentionally small.
 * No Foundation form-input component exists in the library (Commit 5's
 * twelve components have none), and this commit may not add one; the
 * two text fields below are bare native `<input>`/`<textarea>` elements
 * with no custom styling — the same "unstyled until a real token value
 * exists" precedent already applied to the shell's own Header/Navigation
 * placeholders, not a new design choice.
 *
 * Empty state: no `caseId` in the route. Error state: a real fetch
 * failure (the real 404 atlas/core's own CaseNotFoundError produces for
 * an unknown id). Both routes below render this same component.
 *
 * Evidence Sprint 1: each Observation now exposes its own Evidence
 * section directly beneath it — Evidence belongs to exactly one
 * Observation (atlas/core, Evidence Sprint 1 backend investigation:
 * Evidence gained a real `observationId` anchor, following the exact
 * precedent Interpretation already established for the identical
 * relationship). `GET /evidence` (like `GET /observations`) has no
 * server-side filter, so the full list is fetched once and narrowed
 * client-side per Observation by exact `observationId` match — the
 * same required-scoping pattern, not the excluded "Filtering" feature.
 *
 * Field mapping note: the real backend requires `statement` (mapped to
 * the "Summary" label below) and `direction` (SUPPORTS/CHALLENGES — a
 * real, required field with no natural default, so it is a genuine
 * user-facing control here, not silently defaulted) and accepts an
 * optional `source`. There is no backend "Title" field — none is
 * fabricated; only Summary, Source, and Direction are collected.
 * `observedAt` is set to the real submission instant, the same pattern
 * already used for Observation.
 *
 * Knowledge Reference Sprint 1: Knowledge References belong to the
 * Observation, not to an individual Evidence entry — Evidence is not,
 * and cannot become, a valid Knowledge Reference target. atlas/core's
 * `DomainObjectType` is a closed, doctrinally-governed six-member enum
 * (Observation, Knowledge Reference, Reasoning Trace, Judgment,
 * Decision, Outcome); its own docstring explicitly names "Evidence" as
 * a term that must never be coerced into it, and a dedicated repository
 * governance document (`Domain-Object-Type-Set-Discrepancy-
 * Investigation.md`) documents the formal process required to ever
 * change that set — not something available at this layer. Knowledge
 * References are therefore rendered as their own section, a sibling to
 * Evidence under each Observation, never nested inside an Evidence
 * entry or described as belonging to one:
 *
 *   Observation
 *     Evidence
 *       Evidence item 1
 *     Knowledge References
 *       Knowledge Reference 1
 *
 * Creation has no free-text fields at all: the real backend's
 * `CreateKnowledgeReferenceRequest` needs only `caseId` and a `target`
 * (`targetType`/`targetId`), and both are already fully determined by
 * context — `targetType` is always `"Observation"`, `targetId` is
 * always the Observation this section belongs to. There is nothing to
 * type, so "Create" is a confirm step, not a form, per this sprint's
 * own "do not invent fields the backend doesn't require" instruction.
 *
 * Reasoning Trace Sprint 1: rendered as its own section directly
 * beneath Knowledge References, a further sibling under each
 * Observation (not nested inside Evidence or Knowledge References):
 *
 *   Observation
 *     Evidence
 *     Knowledge References
 *     Reasoning Trace
 *
 * atlas/core's `ReasoningTrace.supports` is a non-empty set of typed
 * references to any of the six adopted Domain Object types (INV-013,
 * "one or more"); Evidence is not among them, for the same closed-set
 * reason documented above for Knowledge Reference. This sprint captures
 * the minimal, domain-truthful shape: `supports: [{ targetType:
 * "Observation", targetId: <this Observation's id> }]` — a single-item
 * set anchoring the Trace to the Observation, exactly mirroring how
 * Knowledge Reference's own `target` anchors to the Observation.
 * Multiple Reasoning Traces per Observation are permitted (atlas/core
 * places no upper bound on Traces per supporting object), matching
 * Evidence's and Knowledge Reference's own multi-item sections.
 *
 * Backend note: `list_all()`/`GET /reasoning-traces` and
 * `delete()`/`DELETE /reasoning-traces/{id}` did not exist before this
 * sprint — the governing implementation design document originally,
 * deliberately scoped Reasoning Trace to `add`/`get` only. Both were
 * added this sprint with explicit user authorization after a stop-and-
 * ask escalation; see `atlas/core/domain/reasoning_trace/repository.py`
 * for the full rationale. Creation has no free-text fields either, for
 * the identical reason as Knowledge Reference.
 *
 * Judgment Sprint 1: rendered as its own section directly beneath
 * Reasoning Trace, a further sibling under each Observation:
 *
 *   Observation
 *     Evidence
 *     Knowledge References
 *     Reasoning Trace
 *     Judgment
 *
 * Unlike Knowledge Reference and Reasoning Trace, atlas/core's Judgment
 * carries a real, required free-text field — `characterization` — so
 * this is the first section in this chain with an actual form input
 * again (matching Evidence's own precedent), not a confirm-only step.
 * `subject` is optional on the real backend (Judgment may exist in a
 * subject-less "internal-content" form); this sprint sets it to
 * `{ targetType: "Observation", targetId: <this Observation's id> }`,
 * anchoring the Judgment to its Observation exactly as Knowledge
 * Reference's `target` and Reasoning Trace's `supports` already do — no
 * subject-picker UI is invented. Multiple Judgments per Observation are
 * permitted (atlas/core places no upper bound), matching every prior
 * section's own multi-item list.
 *
 * Backend note: `list_all()`/`GET /judgments` and `delete()`/
 * `DELETE /judgments/{id}` did not exist before this sprint — the
 * governing implementation design document explicitly stated "Delete:
 * forbidden." Both were added this sprint with explicit user
 * authorization after a stop-and-ask escalation, following the same
 * precedent and decision already made for Reasoning Trace; see
 * `atlas/core/domain/judgment/repository.py` for the full rationale.
 */
export function DecisionWorkspacePage() {
  const { caseId } = useParams<{ caseId?: string }>();
  const [status, setStatus] = useState<CaseStatus>({ kind: "loading" });

  const [observations, setObservations] = useState<ObservationRecord[]>([]);
  const [listStatus, setListStatus] = useState<ObservationListStatus>({ kind: "loading" });
  const [createStatus, setCreateStatus] = useState<ObservationCreateStatus>({ kind: "idle" });
  const [subjectInput, setSubjectInput] = useState("");
  const [statementInput, setStatementInput] = useState("");

  const [allEvidence, setAllEvidence] = useState<EvidenceRecord[]>([]);
  const [evidenceListStatus, setEvidenceListStatus] = useState<EvidenceListStatus>({
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
  const [knowledgeReferenceListStatus, setKnowledgeReferenceListStatus] =
    useState<KnowledgeReferenceListStatus>({ kind: "loading" });
  const [knowledgeReferenceCreateStatus, setKnowledgeReferenceCreateStatus] = useState<
    Record<string, KnowledgeReferenceCreateStatus>
  >({});
  const [knowledgeReferenceDeleteStatus, setKnowledgeReferenceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allReasoningTraces, setAllReasoningTraces] = useState<ReasoningTraceRecord[]>([]);
  const [reasoningTraceListStatus, setReasoningTraceListStatus] = useState<ReasoningTraceListStatus>(
    { kind: "loading" },
  );
  const [reasoningTraceCreateStatus, setReasoningTraceCreateStatus] = useState<
    Record<string, ReasoningTraceCreateStatus>
  >({});
  const [reasoningTraceDeleteStatus, setReasoningTraceDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

  const [allJudgments, setAllJudgments] = useState<JudgmentRecord[]>([]);
  const [judgmentListStatus, setJudgmentListStatus] = useState<JudgmentListStatus>({
    kind: "loading",
  });
  const [judgmentCreateStatus, setJudgmentCreateStatus] = useState<
    Record<string, JudgmentCreateStatus>
  >({});
  const [judgmentForm, setJudgmentForm] = useState<Record<string, string>>({});
  const [judgmentDeleteStatus, setJudgmentDeleteStatus] = useState<
    Record<string, "idle" | "deleting" | "error">
  >({});

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

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setEvidenceListStatus({ kind: "loading" });

    fetch("/api/evidence", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<EvidenceRecord[]>;
      })
      .then((records) => {
        setAllEvidence(records);
        setEvidenceListStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setEvidenceListStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [caseId]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setKnowledgeReferenceListStatus({ kind: "loading" });

    fetch("/api/knowledge-references", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<KnowledgeReferenceRecord[]>;
      })
      .then((records) => {
        setAllKnowledgeReferences(records);
        setKnowledgeReferenceListStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setKnowledgeReferenceListStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [caseId]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setReasoningTraceListStatus({ kind: "loading" });

    fetch("/api/reasoning-traces", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<ReasoningTraceRecord[]>;
      })
      .then((records) => {
        setAllReasoningTraces(records);
        setReasoningTraceListStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setReasoningTraceListStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [caseId]);

  useEffect(() => {
    if (!caseId) return;

    const controller = new AbortController();
    setJudgmentListStatus({ kind: "loading" });

    fetch("/api/judgments", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<JudgmentRecord[]>;
      })
      .then((records) => {
        setAllJudgments(records);
        setJudgmentListStatus({ kind: "ready" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setJudgmentListStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [caseId]);

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
    setEvidenceDeleteStatus((current) => ({ ...current, [evidenceId]: "deleting" }));

    fetch(`/api/evidence/${evidenceId}`, { method: "DELETE" })
      .then((response) => {
        if (!response.ok && response.status !== 404) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        setAllEvidence((current) => current.filter((e) => e.evidenceId !== evidenceId));
        setEvidenceDeleteStatus((current) => ({ ...current, [evidenceId]: "idle" }));
      })
      .catch(() => {
        setEvidenceDeleteStatus((current) => ({ ...current, [evidenceId]: "error" }));
      });
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
    setKnowledgeReferenceDeleteStatus((current) => ({
      ...current,
      [knowledgeReferenceId]: "deleting",
    }));

    fetch(`/api/knowledge-references/${knowledgeReferenceId}`, { method: "DELETE" })
      .then((response) => {
        if (!response.ok && response.status !== 404) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        setAllKnowledgeReferences((current) =>
          current.filter((k) => k.knowledgeReferenceId !== knowledgeReferenceId),
        );
        setKnowledgeReferenceDeleteStatus((current) => ({
          ...current,
          [knowledgeReferenceId]: "idle",
        }));
      })
      .catch(() => {
        setKnowledgeReferenceDeleteStatus((current) => ({
          ...current,
          [knowledgeReferenceId]: "error",
        }));
      });
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
    setReasoningTraceDeleteStatus((current) => ({ ...current, [reasoningTraceId]: "deleting" }));

    fetch(`/api/reasoning-traces/${reasoningTraceId}`, { method: "DELETE" })
      .then((response) => {
        if (!response.ok && response.status !== 404) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        setAllReasoningTraces((current) =>
          current.filter((r) => r.reasoningTraceId !== reasoningTraceId),
        );
        setReasoningTraceDeleteStatus((current) => ({ ...current, [reasoningTraceId]: "idle" }));
      })
      .catch(() => {
        setReasoningTraceDeleteStatus((current) => ({ ...current, [reasoningTraceId]: "error" }));
      });
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
    setJudgmentDeleteStatus((current) => ({ ...current, [judgmentId]: "deleting" }));

    fetch(`/api/judgments/${judgmentId}`, { method: "DELETE" })
      .then((response) => {
        if (!response.ok && response.status !== 404) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        setAllJudgments((current) => current.filter((j) => j.judgmentId !== judgmentId));
        setJudgmentDeleteStatus((current) => ({ ...current, [judgmentId]: "idle" }));
      })
      .catch(() => {
        setJudgmentDeleteStatus((current) => ({ ...current, [judgmentId]: "error" }));
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

  const returnDestination = caseId ? `/investment-case/${caseId}` : "/dashboard";

  return (
    <Container>
      <Stack gap="inter-section">
        {/* Workspace Header — UX-012B §20: Workspace name, subject
            identity, return navigation control (all required); status
            indicator (optional). */}
        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={1}>Decision Workspace</Heading>
            <Link href={returnDestination}>
              ← Return to {caseId ? "Investment Case" : "Dashboard"}
            </Link>
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
