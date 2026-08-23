import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { EvidenceGraphSection } from "./EvidenceGraphSection";
import type { EvidenceGraphView } from "./evidenceGraphApi";

function graph(overrides: Partial<EvidenceGraphView> = {}): EvidenceGraphView {
  return {
    caseId: "case-1",
    generatedAt: "2026-01-01T00:00:00Z",
    nodes: [],
    edges: [],
    weakDependencies: [],
    impactedChanges: [],
    summary: {
      nodeCount: 0,
      edgeCount: 0,
      singleSupportCount: 0,
      noSupportCount: 0,
      criticalDependencyCount: 0,
      isolatedChainCount: 0,
      mostCriticalNodeId: null,
    },
    ...overrides,
  };
}

function Wrapper({ graph: g }: { graph: EvidenceGraphView }) {
  const { t } = useTranslation();
  return <EvidenceGraphSection graph={g} t={t} />;
}

function renderSection(g: EvidenceGraphView) {
  return render(
    <LanguageProvider>
      <Wrapper graph={g} />
    </LanguageProvider>,
  );
}

describe("EvidenceGraphSection", () => {
  it("renders nothing when the graph has no nodes", () => {
    const { container } = renderSection(graph());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the compact summary line with real counts", () => {
    renderSection(
      graph({
        nodes: [{ id: "obs-1", kind: "observation", recordedAt: null, details: {} }],
        summary: {
          nodeCount: 1,
          edgeCount: 0,
          singleSupportCount: 0,
          noSupportCount: 2,
          criticalDependencyCount: 1,
          isolatedChainCount: 0,
          mostCriticalNodeId: "f1",
        },
      }),
    );
    expect(screen.getByText(/1 kritiska beroenden/)).toBeInTheDocument();
    expect(screen.getByText(/2 slutsatser utan stöd/)).toBeInTheDocument();
  });

  it("lists each weak dependency using the node's own real statement text", () => {
    renderSection(
      graph({
        nodes: [{ id: "obs-1", kind: "observation", recordedAt: null, details: { statement: "Revenue grew 20%" } }],
        weakDependencies: [{ nodeId: "obs-1", kind: "isolated_chain", detail: 0 }],
        summary: {
          nodeCount: 1,
          edgeCount: 0,
          singleSupportCount: 0,
          noSupportCount: 0,
          criticalDependencyCount: 0,
          isolatedChainCount: 1,
          mostCriticalNodeId: null,
        },
      }),
    );
    expect(screen.getByText("Revenue grew 20%")).toBeInTheDocument();
    expect(screen.getByText("Används inte i någon slutsats")).toBeInTheDocument();
  });

  it("never renders raw technical vocabulary like 'node' or 'edge'", () => {
    renderSection(
      graph({
        nodes: [{ id: "obs-1", kind: "observation", recordedAt: null, details: { statement: "Revenue grew 20%" } }],
        weakDependencies: [{ nodeId: "obs-1", kind: "isolated_chain", detail: 0 }],
        summary: {
          nodeCount: 1,
          edgeCount: 0,
          singleSupportCount: 0,
          noSupportCount: 0,
          criticalDependencyCount: 0,
          isolatedChainCount: 1,
          mostCriticalNodeId: null,
        },
      }),
    );
    expect(screen.queryByText(/\bnode\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bedge\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/dependency graph/i)).not.toBeInTheDocument();
  });
});
