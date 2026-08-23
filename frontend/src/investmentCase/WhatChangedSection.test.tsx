import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { WhatChangedSection } from "./WhatChangedSection";
import type { ChangeFindingView, AnalysisThesisImpact } from "../changeIntelligence/describeChange";
import type { ReasoningFacts } from "./AtlasReasoningSection";

function change(overrides: Partial<ChangeFindingView>): ChangeFindingView {
  return {
    id: "change-1",
    category: "strength_added",
    direction: "positive",
    previousState: "",
    currentState: "growth",
    details: {},
    evidenceReferences: [],
    sourceFindingId: null,
    ...overrides,
  };
}

function Harness(props: {
  changeIntelligenceAvailable: boolean;
  isBaselineCase: boolean;
  latestChanges: ChangeFindingView[];
  thesisChange: AnalysisThesisImpact;
  factsForDimension?: (dimension: string) => ReasoningFacts;
}) {
  const { t } = useTranslation();
  return <WhatChangedSection {...props} t={t} />;
}

function renderSection(props: Partial<Parameters<typeof Harness>[0]> = {}) {
  return render(
    <LanguageProvider>
      <Harness
        changeIntelligenceAvailable
        isBaselineCase={false}
        latestChanges={[]}
        thesisChange="unchanged"
        {...props}
      />
    </LanguageProvider>,
  );
}

describe("WhatChangedSection", () => {
  it("renders nothing when the capability is unavailable", () => {
    const { container } = renderSection({ changeIntelligenceAvailable: false });
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the baseline note for a baseline case", () => {
    renderSection({ isBaselineCase: true });
    expect(
      screen.getByText("Atlas har etablerat en baslinje för det här caset. Framtida analyser jämförs mot den."),
    ).toBeInTheDocument();
  });

  it("shows the no-material-change note when there are no changes", () => {
    renderSection();
    expect(screen.getByText("Ingen väsentlig förändring sedan föregående analys.")).toBeInTheDocument();
  });

  it("renders the Atlas Thesis impact verdict before the individual change list", () => {
    renderSection({
      latestChanges: [change({ id: "a", category: "risk_added", direction: "negative", currentState: "financial_risk" })],
      thesisChange: "weakened",
    });
    const verdict = screen.getByText("Sammantaget har Atlas tes försvagats, men kvarstår intakt.");
    const sincePrevious = screen.getByText("Sedan föregående analys:");
    expect(verdict.compareDocumentPosition(sincePrevious) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("orders changes negative before neutral before positive, regardless of input order", () => {
    renderSection({
      latestChanges: [
        change({ id: "pos", category: "strength_added", direction: "positive", currentState: "growth" }),
        change({
          id: "neu",
          category: "analytical_coverage_changed",
          direction: "neutral",
          currentState: "moderate",
          details: { dimension: "growth" },
        }),
        change({ id: "neg", category: "risk_added", direction: "negative", currentState: "financial_risk" }),
      ],
      thesisChange: "mixed",
    });
    const rendered = screen.getAllByText(/^(↓|•|↑)/).map((el) => el.textContent?.[0]);
    expect(rendered).toEqual(["↓", "•", "↑"]);
  });

  it("shows the current real fact for the changed dimension when one resolves (Product Sprint 14, Deliverable 3)", () => {
    renderSection({
      latestChanges: [
        change({
          id: "growth-change",
          category: "growth_changed",
          direction: "negative",
          previousState: "strong",
          currentState: "moderate",
          details: { dimension: "growth" },
        }),
      ],
      factsForDimension: (dimension) =>
        dimension === "growth"
          ? { supporting: ["Revenue grew 8% year over year, down from 15% the prior period."], contradicting: [] }
          : { supporting: [], contradicting: [] },
    });
    expect(screen.getByText("Revenue grew 8% year over year, down from 15% the prior period.")).toBeInTheDocument();
  });

  it("shows no evidence line when nothing real resolves, rather than an empty line", () => {
    renderSection({
      latestChanges: [
        change({
          id: "growth-change",
          category: "growth_changed",
          direction: "negative",
          previousState: "strong",
          currentState: "moderate",
          details: { dimension: "growth" },
        }),
      ],
      factsForDimension: () => ({ supporting: [], contradicting: [] }),
    });
    expect(screen.getByText(/Tillväxt/)).toBeInTheDocument();
  });

  it("never shows a raw evidence-reference id as the current-evidence line", () => {
    renderSection({
      latestChanges: [
        change({
          id: "growth-change",
          category: "growth_changed",
          direction: "negative",
          previousState: "strong",
          currentState: "moderate",
          details: { dimension: "growth" },
        }),
      ],
      factsForDimension: () => ({
        supporting: ["21ea5c5cd63a91e1eebaea01df3a9645:v1:free_cash_flow:2017-06-30"],
        contradicting: [],
      }),
    });
    expect(screen.queryByText(/21ea5c5cd63a91e1eebaea01df3a9645/)).not.toBeInTheDocument();
  });
});
