import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { DecisionExplanationSection } from "./DecisionExplanationSection";
import type { DecisionExplanationView, SupportingFindingView, BlockingFindingView } from "./decisionExplanationApi";

function supporting(id: string, namedBy: SupportingFindingView["namedBy"] = ["investment_decision"]): SupportingFindingView {
  return { reference: { kind: "reason_code", id }, namedBy };
}

function blocking(
  id: string,
  overrides: Partial<Omit<BlockingFindingView, "reference">> = {},
): BlockingFindingView {
  return { reference: { kind: "reason_code", id }, namedBy: ["investment_decision"], isChangeTrigger: false, ...overrides };
}

function explanation(overrides: Partial<DecisionExplanationView> = {}): DecisionExplanationView {
  return {
    caseId: "case-1",
    action: "hold",
    convictionStrength: "moderate",
    chain: {
      caseId: "case-1",
      order: [
        { kind: "supporting", itemCount: 0 },
        { kind: "blocking", itemCount: 0 },
        { kind: "dependency", itemCount: 0 },
        { kind: "historical", itemCount: 0 },
      ],
      supporting: [],
      blocking: [],
      dependencySteps: [],
      historicalReference: null,
    },
    primarySupporting: null,
    primaryBlocking: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ explanation: e }: { explanation: DecisionExplanationView }) {
  const { t } = useTranslation();
  return <DecisionExplanationSection explanation={e} t={t} />;
}

function renderSection(e: DecisionExplanationView) {
  return render(
    <LanguageProvider>
      <Wrapper explanation={e} />
    </LanguageProvider>,
  );
}

describe("DecisionExplanationSection", () => {
  it("shows the current action and conviction strength badges", () => {
    renderSection(explanation());
    expect(screen.getByText("Behåll")).toBeInTheDocument();
    expect(screen.getByText("Måttligt")).toBeInTheDocument();
  });

  it("shows the honest 'no supporting finding' disclosure when there is none", () => {
    renderSection(explanation());
    expect(screen.getByText("Atlas kan för närvarande inte peka ut ett specifikt stödjande skäl.")).toBeInTheDocument();
  });

  it("shows the primary supporting finding when one exists", () => {
    const missingThesis = supporting("missing_thesis_evidence");
    renderSection(
      explanation({
        primarySupporting: supporting("confidence_established"),
        chain: {
          caseId: "case-1",
          order: [
            { kind: "supporting", itemCount: 1 },
            { kind: "blocking", itemCount: 0 },
            { kind: "dependency", itemCount: 0 },
            { kind: "historical", itemCount: 0 },
          ],
          supporting: [missingThesis],
          blocking: [],
          dependencySteps: [],
          historicalReference: null,
        },
      }),
    );
    expect(screen.getByText(/Starkaste stöd:/)).toBeInTheDocument();
  });

  it("flags the primary blocking finding as the change trigger when it is one, inside the expanded detail", () => {
    const trigger = blocking("missing_thesis_evidence", { isChangeTrigger: true });
    renderSection(
      explanation({
        primaryBlocking: trigger,
        chain: {
          caseId: "case-1",
          order: [
            { kind: "supporting", itemCount: 0 },
            { kind: "blocking", itemCount: 1 },
            { kind: "dependency", itemCount: 0 },
            { kind: "historical", itemCount: 0 },
          ],
          supporting: [],
          blocking: [trigger],
          dependencySteps: [],
          historicalReference: null,
        },
      }),
    );
    screen.getByText("Visa fullständig förklaring").click();
    expect(screen.getByText("Skulle mest sannolikt förändra det här beslutet")).toBeInTheDocument();
  });

  it("shows the honest 'no recorded change yet' disclosure when there is no historical reference", () => {
    const item = blocking("some_blocker");
    renderSection(
      explanation({
        primaryBlocking: item,
        chain: {
          caseId: "case-1",
          order: [
            { kind: "supporting", itemCount: 0 },
            { kind: "blocking", itemCount: 1 },
            { kind: "dependency", itemCount: 0 },
            { kind: "historical", itemCount: 0 },
          ],
          supporting: [],
          blocking: [item],
          dependencySteps: [],
          historicalReference: null,
        },
      }),
    );
    screen.getByText("Visa fullständig förklaring").click();
    expect(screen.getByText("Atlas har ännu inte registrerat någon förändring av det här beslutet.")).toBeInTheDocument();
  });

  it("does not show the expand control when there is nothing more to show", () => {
    renderSection(explanation());
    expect(screen.queryByText("Visa fullständig förklaring")).not.toBeInTheDocument();
  });

  it("never renders raw technical or AI/psychology vocabulary", () => {
    renderSection(explanation());
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bAI\b/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bpredict/i)).not.toBeInTheDocument();
  });
});
