import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { CaseConditionsSection } from "./CaseConditionsSection";
import * as caseConditionApi from "./caseConditionApi";
import type { CaseConditionView } from "./reasoningWorkspaceApi";

vi.mock("./caseConditionApi");

function condition(overrides: Partial<CaseConditionView> = {}): CaseConditionView {
  return {
    conditionId: "c1",
    caseId: "case-1",
    decisionId: "d1",
    status: "active",
    isActive: true,
    predicateText: "China revenue trend",
    role: "monitoring",
    authorship: "atlas",
    structuredKind: null,
    thresholdDate: null,
    thresholdMetric: null,
    thresholdOperator: null,
    thresholdValue: null,
    lastObservedValue: null,
    supersededByConditionId: null,
    latestEventId: "e1",
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("CaseConditionsSection", () => {
  beforeEach(() => {
    vi.mocked(caseConditionApi.createCaseCondition).mockResolvedValue(condition());
    vi.mocked(caseConditionApi.reviseCaseCondition).mockResolvedValue(condition());
    vi.mocked(caseConditionApi.evaluateCaseCondition).mockResolvedValue({
      satisfied: true,
      transitioned: true,
      condition: condition({ status: "satisfied" }),
    });
    vi.mocked(caseConditionApi.retireCaseCondition).mockResolvedValue(undefined);
  });

  it("shows the empty state when there are no conditions", () => {
    renderWithProviders(<CaseConditionsSection caseId="case-1" decisionId="d1" caseConditions={[]} onMutated={vi.fn()} />);
    expect(screen.getByText(/Inga CaseConditions/)).toBeInTheDocument();
  });

  it("renders a condition's predicate and role", () => {
    renderWithProviders(
      <CaseConditionsSection caseId="case-1" decisionId="d1" caseConditions={[condition()]} onMutated={vi.fn()} />,
    );
    expect(screen.getByText("China revenue trend")).toBeInTheDocument();
    // "Bevakning" appears twice once the create-form's own role <select> is
    // also on screen (its own option text) -- assert the role indicator
    // specifically, not the select's option.
    expect(screen.getByText("Bevakning", { selector: "span" })).toBeInTheDocument();
  });

  it("disables Add CaseCondition until real text is entered (Product Sprint 11, Deliverable 5 -- same live-discovered guard gap as AssumptionsSection)", async () => {
    renderWithProviders(<CaseConditionsSection caseId="case-1" decisionId="d1" caseConditions={[]} onMutated={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Lägg till villkor/ })).toBeDisabled();
  });

  it("creates a new condition with the selected role, anchored to the current decision", async () => {
    const onMutated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<CaseConditionsSection caseId="case-1" decisionId="d1" caseConditions={[]} onMutated={onMutated} />);

    await user.type(screen.getByLabelText("Villkor"), "New predicate text");
    await user.click(screen.getByRole("button", { name: /Lägg till villkor/ }));

    await waitFor(() => {
      expect(caseConditionApi.createCaseCondition).toHaveBeenCalledWith("case-1", {
        decisionId: "d1",
        predicateText: "New predicate text",
        role: "monitoring",
        authorship: "user",
      });
    });
    expect(onMutated).toHaveBeenCalled();
  });

  it("evaluates a free-text condition via the human-assertion checkbox", async () => {
    const onMutated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <CaseConditionsSection caseId="case-1" decisionId="d1" caseConditions={[condition()]} onMutated={onMutated} />,
    );

    await user.click(screen.getByLabelText(/Markera som uppfyllt/));
    await user.click(screen.getByRole("button", { name: "Utvärdera" }));

    await waitFor(() => {
      expect(caseConditionApi.evaluateCaseCondition).toHaveBeenCalledWith("c1", { humanAssertedSatisfied: true });
    });
    expect(onMutated).toHaveBeenCalled();
  });

  it("does not show the human-assertion checkbox for a structured condition", () => {
    renderWithProviders(
      <CaseConditionsSection
        caseId="case-1"
        decisionId="d1"
        caseConditions={[condition({ structuredKind: "date" })]}
        onMutated={vi.fn()}
      />,
    );
    expect(screen.queryByLabelText(/Markera som uppfyllt/)).not.toBeInTheDocument();
  });

  it("retires a condition via the existing API", async () => {
    const onMutated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <CaseConditionsSection caseId="case-1" decisionId="d1" caseConditions={[condition()]} onMutated={onMutated} />,
    );

    await user.click(screen.getByRole("button", { name: "Avsluta" }));

    await waitFor(() => expect(caseConditionApi.retireCaseCondition).toHaveBeenCalledWith("c1"));
    expect(onMutated).toHaveBeenCalled();
  });

  it("hides management actions once a condition is terminal", () => {
    renderWithProviders(
      <CaseConditionsSection
        caseId="case-1"
        decisionId="d1"
        caseConditions={[condition({ status: "retired" })]}
        onMutated={vi.fn()}
      />,
    );
    expect(screen.queryByRole("button", { name: "Avsluta" })).not.toBeInTheDocument();
  });
});
