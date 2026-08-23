import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { AtlasReasoningSection, capFacts, isReadableFact, MAX_DISPLAYED_FACTS, type AtlasReasoningInput } from "./AtlasReasoningSection";

const EMPTY_FACTS = { supporting: [], contradicting: [] };

function baseInput(overrides: Partial<AtlasReasoningInput> = {}): AtlasReasoningInput {
  return {
    growthStatus: "not_evaluated",
    growthFacts: EMPTY_FACTS,
    valuationStatus: "not_evaluated",
    valuationFacts: EMPTY_FACTS,
    financialHealthStatus: "not_evaluated",
    financialHealthFacts: EMPTY_FACTS,
    businessQualityStatus: "not_evaluated",
    businessQualityFacts: EMPTY_FACTS,
    ...overrides,
  };
}

function Harness({ input }: { input: AtlasReasoningInput }) {
  const { t } = useTranslation();
  return <AtlasReasoningSection input={input} t={t} />;
}

function renderSection(input: AtlasReasoningInput) {
  return render(
    <LanguageProvider>
      <Harness input={input} />
    </LanguageProvider>,
  );
}

describe("isReadableFact", () => {
  it("rejects raw evidence-reference ids (no whitespace)", () => {
    expect(isReadableFact("21ea5c5cd63a91e1eebaea01df3a9645:v1:free_cash_flow:2017-06-30")).toBe(false);
    expect(isReadableFact("business_finding:growth")).toBe(false);
    expect(isReadableFact("valuation_finding:fcf_yield_relative")).toBe(false);
  });

  it("accepts real prose (contains whitespace)", () => {
    expect(isReadableFact("Revenue grew 24% year over year")).toBe(true);
    expect(isReadableFact("This holding is 33.0% of the portfolio (concentration: Elevated).")).toBe(true);
  });
});

describe("AtlasReasoningSection (Product Sprint 13 -- Company Intelligence Excellence)", () => {
  it("shows the real supporting/contradicting facts under a card's interpretation, not just the generic sentence (Deliverable 2)", () => {
    renderSection(
      baseInput({
        growthStatus: "moderate",
        growthFacts: { supporting: ["Revenue grew 24% year over year to $416B"], contradicting: [] },
      }),
    );
    expect(screen.getByText("Tillväxten är måttlig — en verklig men inte avgörande faktor.")).toBeInTheDocument();
    expect(screen.getByText(/Revenue grew 24% year over year to \$416B/)).toBeInTheDocument();
  });

  it("never shows a raw evidence-reference id even when the backend returns one instead of prose (live-discovered)", () => {
    renderSection(
      baseInput({
        financialHealthStatus: "moderate",
        financialHealthFacts: {
          supporting: ["32bf9128683a664458e51d47cbc6957b:v1:free_cash_flow:2026-06-30", "business_finding:capital_allocation"],
          contradicting: [],
        },
      }),
    );
    expect(screen.queryByText(/32bf9128683a664458e51d47cbc6957b/)).not.toBeInTheDocument();
    expect(screen.queryByText(/business_finding:/)).not.toBeInTheDocument();
  });

  it("shows no fact line at all when no real prose fact exists, rather than an empty label", () => {
    renderSection(baseInput({ growthStatus: "moderate" }));
    expect(screen.queryByText(/Supporting:|Stödjande:/)).not.toBeInTheDocument();
  });

  it("caps a finding evaluated across many periods to a readable count instead of an unreadable wall of text (live-discovered, Deliverable 3)", () => {
    const manyFacts = Array.from({ length: 30 }, (_, i) => `Revenue was ${i} USD for the period ending 20${10 + i}-06-30.`);
    renderSection(
      baseInput({
        growthStatus: "moderate",
        growthFacts: { supporting: manyFacts, contradicting: [] },
      }),
    );
    expect(screen.getByText(manyFacts[0]!, { exact: false })).toBeInTheDocument();
    expect(screen.queryByText(manyFacts[manyFacts.length - 1]!, { exact: false })).not.toBeInTheDocument();
  });
});

describe("capFacts", () => {
  it(`keeps at most ${MAX_DISPLAYED_FACTS} facts, preserving their order`, () => {
    const facts = ["a", "b", "c", "d", "e"];
    expect(capFacts(facts)).toEqual(facts.slice(0, MAX_DISPLAYED_FACTS));
  });

  it("leaves a short list untouched", () => {
    expect(capFacts(["only one"])).toEqual(["only one"]);
  });
});
