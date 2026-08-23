import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { InvestmentArgumentSection } from "./InvestmentArgumentSection";
import type { AnalysisHighlightKind, AnalysisOpenQuestionOrigin } from "../changeIntelligence/describeChange";
import type { ReasoningFacts } from "./AtlasReasoningSection";

const NO_FACTS: ReasoningFacts = { supporting: [], contradicting: [] };

function Harness(props: {
  strengthKinds: AnalysisHighlightKind[];
  riskKinds: AnalysisHighlightKind[];
  openQuestionOrigins: AnalysisOpenQuestionOrigin[];
  factsForKind?: (kind: AnalysisHighlightKind) => ReasoningFacts;
}) {
  const { t } = useTranslation();
  return <InvestmentArgumentSection factsForKind={() => NO_FACTS} {...props} t={t} />;
}

function renderSection(props: Partial<Parameters<typeof Harness>[0]> = {}) {
  return render(
    <LanguageProvider>
      <Harness strengthKinds={[]} riskKinds={[]} openQuestionOrigins={[]} {...props} />
    </LanguageProvider>,
  );
}

describe("InvestmentArgumentSection", () => {
  it("renders Supports, Challenges, and Open Questions as three distinct columns", () => {
    renderSection();
    expect(screen.getByText("Talar för caset")).toBeInTheDocument();
    expect(screen.getByText("Talar mot caset")).toBeInTheDocument();
    expect(screen.getByText("Öppna frågor")).toBeInTheDocument();
  });

  it("shows an empty-state message per column when nothing is classified", () => {
    renderSection();
    expect(
      screen.getByText(
        "Inget av Atlas resultat är starkt nog på egen hand för att räknas som en tydlig stödjande faktor — se Atlas resonemang nedan för den fullständiga bilden.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Inget av Atlas resultat är svagt nog på egen hand för att räknas som en tydlig riskfaktor — se Atlas resonemang nedan för den fullständiga bilden.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Inga öppna frågor identifierade för det här caset just nu.")).toBeInTheDocument();
  });

  it("renders a real sentence for each open question origin, reusing the existing open-questions vocabulary", () => {
    renderSection({ openQuestionOrigins: ["growth_mixed", "valuation_inconclusive"] });
    expect(screen.getByText("Är den senaste tillväxten hållbar, eller var den tillfällig?")).toBeInTheDocument();
    expect(
      screen.getByText("Är det aktuella priset billigt eller dyrt? Atlas har ännu inte tillräcklig historisk värderingsdata för att avgöra det."),
    ).toBeInTheDocument();
  });

  it("shows the real supporting/contradicting fact under each argument, not just the category sentence (Product Sprint 13, Deliverable 6)", () => {
    renderSection({
      strengthKinds: ["growth"],
      riskKinds: ["financial_risk"],
      factsForKind: (kind) =>
        kind === "growth"
          ? { supporting: ["Revenue grew 24% year over year"], contradicting: [] }
          : { supporting: [], contradicting: ["Debt-to-equity rose to 2.1x"] },
    });
    expect(screen.getByText("Revenue grew 24% year over year")).toBeInTheDocument();
    expect(screen.getByText("Debt-to-equity rose to 2.1x")).toBeInTheDocument();
  });

  it("never shows a raw evidence-reference id as a fact (Product Sprint 13 -- live-discovered: this field sometimes holds unresolved ids, not prose)", () => {
    renderSection({
      strengthKinds: ["growth"],
      riskKinds: ["financial_risk"],
      factsForKind: () => ({
        supporting: ["21ea5c5cd63a91e1eebaea01df3a9645:v1:free_cash_flow:2017-06-30"],
        contradicting: ["business_finding:capital_allocation"],
      }),
    });
    expect(screen.queryByText(/21ea5c5cd63a91e1eebaea01df3a9645/)).not.toBeInTheDocument();
    expect(screen.queryByText(/business_finding:/)).not.toBeInTheDocument();
  });

  it("never renders a numeric score anywhere in the section", () => {
    renderSection({
      strengthKinds: ["growth"],
      riskKinds: ["financial_risk"],
      openQuestionOrigins: ["growth_mixed"],
    });
    expect(screen.queryByText(/^\d+\/\d+$|^\d+%$/)).not.toBeInTheDocument();
  });
});
