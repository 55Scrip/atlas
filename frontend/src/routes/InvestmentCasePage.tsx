import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Container, Divider, Heading, Link, Stack, Surface, Text } from "../foundation";

interface CaseSummary {
  caseId: string;
  recordedAt: string;
}

type CaseStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; case: CaseSummary };

/**
 * Investment Case Shell (Sprint 1, Commit 8) — structural layout only.
 *
 * TERMINOLOGY: "Investment Case" is a presentation-layer label only.
 * Architecture-Governance.md §8.7.4 and Atlas-Alpha-Baseline-v1.0.md §4
 * both record it as a candidate concept, not yet a settled Atlas concept
 * — UX-012 itself defers it "pending future Investment Case / Portfolio
 * Product Architecture treatment." This page therefore does not adopt
 * UX-012 §15's separately-defined "Investment Workspace" reasoning
 * sequence (Current Conclusion, Supporting Factors, Challenges, ...) —
 * doing so would silently settle an open governance question. It renders
 * exactly one real backend concept, atlas/core's own Case (DO-IMP-001,
 * unchanged, unrenamed), and otherwise uses only generic, content-neutral
 * placeholder regions.
 *
 * atlas/core's Case is deliberately minimal (its own entity docstring:
 * "no further lifecycle, status, title, description, or content is
 * canonically forced, and none is added here") — only `case_id` and
 * `recorded_at` exist. No status field exists to display; none is
 * fabricated here.
 *
 * Empty state: no `caseId` in the route — genuinely nothing has been
 * requested, so nothing is fetched. Error state: a real fetch failure
 * (e.g. the real 404 atlas/core's own CaseNotFoundError produces for an
 * unknown id). Both routes below render this same component.
 *
 * Integration Sprint 1: added the one missing link in the Dashboard ->
 * Investment Case -> Decision Workspace chain — this page previously had
 * no way to reach the Decision Workspace at all, even though that page
 * is where every real workflow for this Case (Observation, Evidence,
 * ... Outcome) already lives. Placed in "Primary Workspace," since that
 * is the reserved home for this Case's own real content and the
 * Decision Workspace is, today, that content. No other behavior changes.
 */
export function InvestmentCasePage() {
  const { caseId } = useParams<{ caseId?: string }>();
  const [status, setStatus] = useState<CaseStatus>({ kind: "loading" });

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

  return (
    <Container>
      <Stack gap="inter-section">
        {/* Page-level header — distinct from the global application shell's
            own Header (shell/Header.tsx). Future home for a case title,
            breadcrumb, and page-level actions. */}
        <Surface tier="primary">
          <Heading level={1}>Investment Case</Heading>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Case Summary</Heading>
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
              <Stack gap="inter-section">
                <Text>Case ID: {status.case.caseId}</Text>
                <Text color="secondary">Recorded at: {status.case.recordedAt}</Text>
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Primary Workspace</Heading>
            {caseId ? (
              <Link href={`/decision-workspace/${caseId}`}>Go to Decision Workspace →</Link>
            ) : (
              <Text color="secondary">
                Reserved for this Investment Case's primary content in a future commit.
              </Text>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Secondary Information</Heading>
            <Text color="secondary">
              Reserved for supporting or contextual content in a future commit.
            </Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Metadata</Heading>
            <Text color="secondary">
              Reserved for additional case metadata in a future commit.
            </Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Heading level={2}>Footer</Heading>
        </Surface>
      </Stack>
    </Container>
  );
}
