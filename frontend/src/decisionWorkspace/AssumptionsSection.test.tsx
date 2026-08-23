import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { AssumptionsSection } from "./AssumptionsSection";
import * as assumptionApi from "./assumptionApi";
import type { AssumptionView } from "./reasoningWorkspaceApi";

vi.mock("./assumptionApi");

function assumption(overrides: Partial<AssumptionView> = {}): AssumptionView {
  return {
    assumptionId: "a1",
    decisionId: "d1",
    caseId: "c1",
    status: "supported",
    isActive: true,
    statement: "GCP margin expansion continues",
    authorship: "atlas",
    linkedCaseConditionIds: [],
    lastChallengeEvidenceId: null,
    lastChallengeNote: null,
    supersededByAssumptionId: null,
    latestEventId: "e1",
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("AssumptionsSection", () => {
  beforeEach(() => {
    vi.mocked(assumptionApi.createAssumption).mockResolvedValue(assumption());
    vi.mocked(assumptionApi.reviseAssumption).mockResolvedValue(assumption());
    vi.mocked(assumptionApi.challengeAssumption).mockResolvedValue(assumption({ status: "challenged" }));
    vi.mocked(assumptionApi.retireAssumption).mockResolvedValue(undefined);
  });

  it("shows the empty state when there are no assumptions", () => {
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[]} onMutated={vi.fn()} />);
    expect(screen.getByText(/Inga antaganden/)).toBeInTheDocument();
  });

  it("renders an assumption's statement and status", () => {
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[assumption()]} onMutated={vi.fn()} />);
    expect(screen.getByText("GCP margin expansion continues")).toBeInTheDocument();
  });

  it("creates a new assumption via the existing API and notifies the parent", async () => {
    const onMutated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[]} onMutated={onMutated} />);

    await user.type(screen.getByLabelText("Påstående"), "New assumption text");
    await user.click(screen.getByRole("button", { name: /Lägg till antagande/ }));

    await waitFor(() => {
      expect(assumptionApi.createAssumption).toHaveBeenCalledWith("d1", {
        statement: "New assumption text",
        authorship: "user",
      });
    });
    expect(onMutated).toHaveBeenCalled();
  });

  it("disables Add Assumption until real text is entered (Product Sprint 11, Deliverable 5 -- live-discovered: a stray click previously created a real, blank assumption)", async () => {
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[]} onMutated={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Lägg till antagande/ })).toBeDisabled();
  });

  it("challenges an assumption with the entered note and severity", async () => {
    const onMutated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[assumption()]} onMutated={onMutated} />);

    await user.click(screen.getByRole("button", { name: "Ifrågasätt" }));
    await user.type(screen.getByPlaceholderText(/Varför ifrågasätts/), "New contradicting evidence");
    await user.click(screen.getByRole("button", { name: "Ifrågasätt" }));

    await waitFor(() => {
      expect(assumptionApi.challengeAssumption).toHaveBeenCalledWith("a1", {
        note: "New contradicting evidence",
        severity: "challenged",
      });
    });
    expect(onMutated).toHaveBeenCalled();
  });

  it("retires an assumption via the existing API", async () => {
    const onMutated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[assumption()]} onMutated={onMutated} />);

    await user.click(screen.getByRole("button", { name: "Avsluta" }));

    await waitFor(() => expect(assumptionApi.retireAssumption).toHaveBeenCalledWith("a1"));
    expect(onMutated).toHaveBeenCalled();
  });

  it("hides management actions once an assumption is terminal (retired/superseded)", () => {
    renderWithProviders(
      <AssumptionsSection decisionId="d1" assumptions={[assumption({ status: "retired" })]} onMutated={vi.fn()} />,
    );
    expect(screen.queryByRole("button", { name: "Avsluta" })).not.toBeInTheDocument();
  });

  it("surfaces an error message when the API call fails, without crashing", async () => {
    vi.mocked(assumptionApi.retireAssumption).mockRejectedValue(new Error("500"));
    const user = userEvent.setup();
    renderWithProviders(<AssumptionsSection decisionId="d1" assumptions={[assumption()]} onMutated={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Avsluta" }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("500"));
  });
});
