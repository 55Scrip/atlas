import { useEffect, useState } from "react";
import { Container, Divider, Heading, Stack, Surface, Text } from "../foundation";

interface DecisionSummary {
  id: string;
  subject: string;
  recordedAt: string;
}

type DecisionsStatus =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; decisions: DecisionSummary[] };

/**
 * Dashboard Shell (Sprint 1, Commit 6) — structural layout only.
 *
 * Section set is UX-012 §14's own five "Required areas" for the
 * Dashboard, verbatim: Portfolio status summary, Active Monitoring
 * Conditions, Recent Decisions summary, Signals list, Navigation to all
 * active Workspaces. Everything except Recent Decisions is a labeled
 * placeholder — none of those five areas' actual product logic exists
 * yet (Portfolio, Monitoring, Signals, and every Workspace are explicitly
 * out of scope for this commit).
 *
 * Single-column layout, no secondary sidebar: UX-012A's own Layout
 * foundations state this directly — "no persistent side panels" and
 * "full-width only for Dashboard signals." There is no UX-012 §14
 * structural text describing a primary/sidebar split for the Dashboard
 * either, so none is built.
 *
 * Responsive layout: a single-column vertical Stack requires no
 * breakpoint to adapt — it reflows correctly at any viewport width by
 * construction. No breakpoint token exists anywhere in the token system
 * (Commits 3/4 found none in the governing corpus), so none is invented
 * here; there is also no multi-column arrangement in this shell that
 * would need one.
 */
export function DashboardPage() {
  const [decisionsStatus, setDecisionsStatus] = useState<DecisionsStatus>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/decisions", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }
        return response.json() as Promise<DecisionSummary[]>;
      })
      .then((decisions) => setDecisionsStatus({ kind: "loaded", decisions }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionsStatus({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, []);

  return (
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>Dashboard</Heading>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Portfolio Status</Heading>
            <Text color="secondary">Not yet implemented.</Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Active Monitoring Conditions</Heading>
            <Text color="secondary">Not yet implemented.</Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Recent Decisions</Heading>
            {decisionsStatus.kind === "loading" && (
              <Text role="status" aria-live="polite">
                Loading…
              </Text>
            )}
            {decisionsStatus.kind === "error" && (
              <Text color="tertiary" role="alert">
                Could not load recent decisions: {decisionsStatus.message}
              </Text>
            )}
            {decisionsStatus.kind === "loaded" && decisionsStatus.decisions.length === 0 && (
              <Text color="secondary">No decisions recorded yet.</Text>
            )}
            {decisionsStatus.kind === "loaded" && decisionsStatus.decisions.length > 0 && (
              <Stack gap="inter-section">
                {decisionsStatus.decisions.map((decision) => (
                  <div key={decision.id}>
                    <Text>{decision.subject}</Text>
                    <Text color="secondary" as="p">
                      {decision.recordedAt}
                    </Text>
                  </div>
                ))}
              </Stack>
            )}
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Signals</Heading>
            <Text color="secondary">Not yet implemented.</Text>
          </Stack>
        </Surface>

        <Divider />

        <Surface tier="primary">
          <Stack gap="inter-section">
            <Heading level={2}>Workspaces</Heading>
            <Text color="secondary">No active Workspaces yet.</Text>
          </Stack>
        </Surface>
      </Stack>
    </Container>
  );
}
