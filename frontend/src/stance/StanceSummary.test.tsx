import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { StanceSummary } from "./StanceSummary";
import type { StanceView } from "./stanceApi";
import type { DimensionGap } from "./describeMissingInformation";

function stance(overrides: Partial<StanceView> = {}): StanceView {
  return {
    level: "review",
    reasoning: [{ code: "confidence_moderate" }],
    supportingSignals: [],
    limitingSignals: [{ code: "confidence_moderate" }],
    confidence: "moderate",
    missingInformation: [],
    ...overrides,
  } as StanceView;
}

function Harness({ view, gaps }: { view: StanceView; gaps?: DimensionGap[] | undefined }) {
  const { t } = useTranslation();
  return <StanceSummary stance={view} t={t} {...(gaps ? { gaps } : {})} />;
}

function renderStance(view: StanceView, gaps?: DimensionGap[]) {
  render(
    <LanguageProvider>
      <Harness view={view} gaps={gaps} />
    </LanguageProvider>,
  );
}

describe("StanceSummary -- decision honesty", () => {
  it("reports a company's own missing evidence as the company's", () => {
    renderStance(stance({ missingInformation: ["fcf_yield_relative"] }));
    expect(screen.getByText(/Atlas saknar fortfarande:/)).toBeInTheDocument();
    expect(screen.queryByText(/för något bolag/)).not.toBeInTheDocument();
  });

  /** The defect: an evaluator Atlas has not built, presented as
   * something this particular company is short of. */
  it("never files a capability Atlas lacks for everyone under this company's missing evidence", () => {
    renderStance(stance({ missingInformation: ["thesis_risk"] }));
    expect(screen.getByText(/Det här utvärderar Atlas inte ännu, för något bolag:/)).toBeInTheDocument();
    expect(screen.queryByText(/Atlas saknar fortfarande:/)).not.toBeInTheDocument();
  });

  it("says both, separately, when both are true", () => {
    renderStance(stance({ missingInformation: ["fcf_yield_relative", "thesis_risk"] }));
    expect(screen.getByText(/Atlas saknar fortfarande:/)).toBeInTheDocument();
    expect(screen.getByText(/Det här utvärderar Atlas inte ännu, för något bolag:/)).toBeInTheDocument();
  });

  /** Analysis completeness is not investment conviction. The sentence
   * used to read "Atlas's own confidence in this analysis is moderate",
   * which an investor reads as conviction -- while the value behind it
   * is `assess_coverage().overall_confidence`, a count of how many
   * dimensions Atlas managed to evaluate. Conviction is its own
   * canonical field and can legitimately be Low at the same time. */
  it("describes analysis completeness as completeness, never as confidence in the investment", () => {
    renderStance(stance());
    expect(screen.getByText(/Atlas har utvärderat mycket, men inte allt, i den här analysen\./)).toBeInTheDocument();
    expect(screen.queryByText(/Atlas egen tillförsikt/)).not.toBeInTheDocument();
    expect(screen.queryByText(/confidence in this analysis/)).not.toBeInTheDocument();
  });
});


/**
 * Gap Reason Surface. ASSA-B's hero said "Atlas is still missing: ...
 * Financial", which reads as though Atlas lacks its financial statements;
 * it holds four years of them. The reason -- no verified industry
 * classification -- was in the payload all along.
 */
describe("StanceSummary -- why, not only where", () => {
  const ASSA_B: DimensionGap[] = [
    { dimension: "financial_risk", reasoning: ["industry_unknown"] },
  ];

  it("gives the reason when the Case carries one", () => {
    renderStance(stance({ missingInformation: ["financial_risk"] }), ASSA_B);
    expect(screen.getByText(/Bolagets bransch är okänd/)).toBeInTheDocument();
  });

  it("still names the dimension the reason belongs to", () => {
    renderStance(stance({ missingInformation: ["financial_risk"] }), ASSA_B);
    expect(screen.getByText(/Finansiell/)).toBeInTheDocument();
  });

  it("never prints the raw reason code", () => {
    const { container } = render(
      <LanguageProvider>
        <Harness view={stance({ missingInformation: ["financial_risk"] })} gaps={ASSA_B} />
      </LanguageProvider>,
    );
    expect(container.textContent).not.toContain("industry_unknown");
  });

  it("keeps the previous copy exactly when no reasons are supplied", () => {
    renderStance(stance({ missingInformation: ["financial_risk"] }));
    expect(screen.getByText(/Atlas saknar fortfarande:/)).toBeInTheDocument();
    expect(screen.queryByText(/Bolagets bransch är okänd/)).not.toBeInTheDocument();
  });
});
