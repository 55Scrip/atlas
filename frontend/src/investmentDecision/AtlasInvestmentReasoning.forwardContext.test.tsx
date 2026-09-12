import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { en } from "../i18n/translations/en";
import { AtlasInvestmentReasoning } from "./AtlasInvestmentReasoning";
import { forwardContextLabels, forwardUnknownLabels } from "./describeRecommendationReasoning";
import type { DecisionAction, InvestmentDecisionView } from "./investmentDecisionApi";
import type { ForwardReasoningContextView, RecommendationReasoningView } from "./reasoningContract";

/**
 * Forward context in the reasoning card. The payloads below are the real
 * `/investment-decision` responses for VST (TRIM), AMD (withheld) and
 * GOOGL, captured from a copy of the live database -- fixture data, not
 * rules: nothing in the card knows any ticker.
 */
const VST_FORWARD: ForwardReasoningContextView = {
  "guidance": [
    {
      "signalId": "84b3110dbb11a4400f165f3edd1a32e4:v1:adjusted_ebitda:unspecified_year:2026:revision",
      "subject": "adjusted_ebitda",
      "measureDefinedByManagement": true,
      "horizonPeriod": "2026",
      "horizonKind": "unspecified_year",
      "revision": "reaffirmed",
      "valueText": "$6.8 billion-$7.6 billion",
      "priorValueText": "$6.8 billion to $7.6 billion",
      "sourcePeriod": "2026Q2",
      "revisionCount": 1
    },
    {
      "signalId": "84b3110dbb11a4400f165f3edd1a32e4:v1:free_cash_flow:unspecified_year:2026:revision",
      "subject": "free_cash_flow",
      "measureDefinedByManagement": true,
      "horizonPeriod": "2026",
      "horizonKind": "unspecified_year",
      "revision": "reaffirmed",
      "valueText": "$3.925 billion-$4.725 billion",
      "priorValueText": "$3.925 billion to $4.725 billion",
      "sourcePeriod": "2026Q2",
      "revisionCount": 1
    }
  ],
  "contractedVolume": [
    {
      "signalId": "b81e211a096693463e490e6c2fd450b6:v1:commitment:22c25805236e6559:contracted_volume",
      "sourcePeriod": "2025Q3",
      "counterpartyText": null,
      "agreementText": "power purchase agreement",
      "quantityTexts": [
        "up to 1,200 megawatts of new load"
      ],
      "termYears": 20.0,
      "deliveryStartYears": [],
      "deliveryEndYears": [],
      "notEstablished": [
        "price",
        "revenue_contribution",
        "earnings_contribution",
        "cash_flow_contribution"
      ]
    },
    {
      "signalId": "20733f818ebd42d58b68225fac5895b5:v1:commitment:17e4f5fd4e70bd8a:contracted_volume",
      "sourcePeriod": "2025Q4",
      "counterpartyText": "Amazon",
      "agreementText": "20-year contract",
      "quantityTexts": [
        "1,200 megawatts of capacity"
      ],
      "termYears": 20.0,
      "deliveryStartYears": [],
      "deliveryEndYears": [],
      "notEstablished": [
        "price",
        "revenue_contribution",
        "earnings_contribution",
        "cash_flow_contribution"
      ]
    },
    {
      "signalId": "20733f818ebd42d58b68225fac5895b5:v1:commitment:90274be9f881d0f2:contracted_volume",
      "sourcePeriod": "2025Q4",
      "counterpartyText": "Meta",
      "agreementText": "long-term power purchase agreements",
      "quantityTexts": [
        "2,176 megawatts of operating capacity",
        "433 megawatts of upgrade capacity"
      ],
      "termYears": 20.0,
      "deliveryStartYears": [
        2026,
        2027
      ],
      "deliveryEndYears": [],
      "notEstablished": [
        "price",
        "revenue_contribution",
        "earnings_contribution",
        "cash_flow_contribution"
      ]
    },
    {
      "signalId": "20733f818ebd42d58b68225fac5895b5:v1:commitment:be16ecd2511903b9:contracted_volume",
      "sourcePeriod": "2025Q4",
      "counterpartyText": "Amazon Web Services",
      "agreementText": "20-year agreement",
      "quantityTexts": [
        "1,200 megawatts"
      ],
      "termYears": 20.0,
      "deliveryStartYears": [],
      "deliveryEndYears": [],
      "notEstablished": [
        "price",
        "revenue_contribution",
        "earnings_contribution",
        "cash_flow_contribution"
      ]
    },
    {
      "signalId": "20733f818ebd42d58b68225fac5895b5:v1:commitment:ea51f45583d605a7:contracted_volume",
      "sourcePeriod": "2025Q4",
      "counterpartyText": "Meta",
      "agreementText": "20-year agreements",
      "quantityTexts": [
        "2,176 megawatts of operating capacity",
        "433 megawatts of upgrades"
      ],
      "termYears": 20.0,
      "deliveryStartYears": [],
      "deliveryEndYears": [],
      "notEstablished": [
        "price",
        "revenue_contribution",
        "earnings_contribution",
        "cash_flow_contribution"
      ]
    }
  ],
  "counterpartyTexts": [
    "Amazon",
    "Amazon Web Services",
    "Meta"
  ],
  "unnamedObservationCount": 1,
  "unestablishedEconomics": [
    "price",
    "revenue_contribution",
    "earnings_contribution",
    "cash_flow_contribution"
  ],
  "identityResolved": false
};

const AMD_FORWARD: ForwardReasoningContextView = {
  "guidance": [],
  "contractedVolume": [
    {
      "signalId": "c103ed57ff0e9aa94131f7e09c0a6b3f:v1:commitment:f01dc3cf51d18127:contracted_volume",
      "sourcePeriod": "2025Q3",
      "counterpartyText": "OpenAI",
      "agreementText": "comprehensive multiyear agreement",
      "quantityTexts": [
        "6 gigawatts of Instinct GPUs"
      ],
      "termYears": null,
      "deliveryStartYears": [
        2026
      ],
      "deliveryEndYears": [],
      "notEstablished": [
        "price",
        "revenue_contribution",
        "earnings_contribution",
        "cash_flow_contribution"
      ]
    }
  ],
  "counterpartyTexts": [
    "OpenAI"
  ],
  "unnamedObservationCount": 0,
  "unestablishedEconomics": [
    "price",
    "revenue_contribution",
    "earnings_contribution",
    "cash_flow_contribution"
  ],
  "identityResolved": false
};

const GOOGL_FORWARD: ForwardReasoningContextView = {
  "guidance": [
    {
      "signalId": "db7454b8569d30588ea4a6f99a4aa27e:v1:capital_expenditure:unspecified_year:2026:revision",
      "subject": "capital_expenditure",
      "measureDefinedByManagement": false,
      "horizonPeriod": "2026",
      "horizonKind": "unspecified_year",
      "revision": "raised",
      "valueText": "$195 billion to $205 billion",
      "priorValueText": "$180 billion to $190 billion",
      "sourcePeriod": "2026Q2",
      "revisionCount": 2
    }
  ],
  "contractedVolume": [],
  "counterpartyTexts": [],
  "unnamedObservationCount": 0,
  "unestablishedEconomics": [],
  "identityResolved": false
};

const VST_REASONING: Partial<RecommendationReasoningView> = {
  "primaryDrivers": [],
  "counterDrivers": [
    {
      "kind": "financial_risk_elevated",
      "polarity": "adverse",
      "engine": "financial_risk",
      "sourceStatus": "high"
    }
  ],
  "keyUnknowns": [
    {
      "kind": "analysis_complete_unresolved",
      "engine": "valuation_support"
    },
    {
      "kind": "not_connected_to_direction",
      "engine": "business_quality"
    },
    {
      "kind": "not_connected_to_direction",
      "engine": "industry_context"
    },
    {
      "kind": "not_connected_to_direction",
      "engine": "expected_return"
    }
  ],
  "whatWouldChange": [
    "reduced_risk",
    "valuation_becomes_expensive"
  ]
};

function vst(
  forwardContext: ForwardReasoningContextView | null | undefined,
  action: DecisionAction = "reduce",
): InvestmentDecisionView {
  const reasoning = {
    schemaVersion: 1,
    ...VST_REASONING,
    signalSummary: [],
    recommendationConviction:
      action === "no_decision" ? null : { level: "low", analyticalReasons: [], evidentialReasons: [] },
    ...(forwardContext === undefined ? {} : { forwardContext }),
  } as RecommendationReasoningView;
  return {
    caseId: "case-vst",
    action,
    qualifiers: [],
    supportingReasons: [],
    blockers: [],
    changeTrigger: null,
    generatedAt: "2026-09-12T00:00:00Z",
    reasoning,
  };
}

function Wrapper({ decision }: { decision: InvestmentDecisionView }) {
  const { t } = useTranslation();
  return <AtlasInvestmentReasoning decision={decision} t={t} />;
}

function text(decision: InvestmentDecisionView): string {
  const { container } = render(
    <LanguageProvider>
      <Wrapper decision={decision} />
    </LanguageProvider>,
  );
  return container.textContent ?? "";
}

/** English, through the real dictionary and the same `{{name}}` interpolation. */
function tEn(key: keyof typeof en, params: Record<string, string | number> = {}): string {
  return Object.entries(params).reduce((s, [k, v]) => s.split("{{" + k + "}}").join(String(v)), en[key] as string);
}

describe("forward context -- VST, a directional TRIM", () => {
  it("keeps the concern exactly as it was and adds the forward evidence in its own row", () => {
    const after = text(vst(VST_FORWARD));
    expect(after).toContain("Talar emot: Förhöjd finansiell risk");
    expect(after).toContain("Talar för: Inget i underlaget talar tydligt för.");
    expect(after).toContain("Vad skulle ändra bilden: Lägre risk");
    expect(after).toContain("Framåtblickande underlag:");
  });

  it("states reaffirmed guidance as unchanged, with the management-defined measure qualified", () => {
    const after = text(vst(VST_FORWARD));
    expect(after).toContain(
      "Guidning 2026 för ett EBITDA-mått (ledningens definition) oförändrad: $6.8 billion-$7.6 billion",
    );
    expect(after).toContain(
      "Guidning 2026 för ett kassaflödesmått (ledningens definition) oförändrad: $3.925 billion-$4.725 billion",
    );
  });

  it("describes contracted volume as observations, never as a count of contracts, and sums nothing", () => {
    const after = text(vst(VST_FORWARD));
    expect(after).toContain(
      "Kontrakterad kundvolym som nämner Amazon, Amazon Web Services, Meta, en ej namngiven kund i 5 källobservationer (2025Q3–2025Q4) — samma avtal kan förekomma i flera; angiven löptid: 20 år",
    );
    for (const total of ["3.8", "3,8", "3 800", "3,809", "2,609", "6,009", "5 avtal", "fem avtal"]) {
      expect(after).not.toContain(total);
    }
  });

  it("puts the economics contracted volume does not establish into the main uncertainty", () => {
    const after = text(vst(VST_FORWARD));
    expect(after).toContain(
      "Viktigaste osäkerhet: Går inte att avgöra ännu: värderingsstöd · Avtalspris samt bidrag till intäkter, resultat och kassaflöde är inte fastställda",
    );
  });

  it("renders exactly what it rendered before when there is no forward evidence", () => {
    const without = text(vst(null));
    expect(without).not.toContain("Framåtblickande underlag");
    expect(without).not.toContain("Avtalspris");
    expect(text(vst(undefined))).toBe(without);
  });

  it("uses no polarity or economic-value vocabulary anywhere in the forward context", () => {
    const labels = [
      ...forwardContextLabels(VST_FORWARD, tEn),
      ...forwardUnknownLabels(VST_FORWARD, tEn),
      ...forwardContextLabels(AMD_FORWARD, tEn),
      ...forwardContextLabels(GOOGL_FORWARD, tEn),
    ]
      .join(" ")
      .toLowerCase();
    for (const word of ["support", "positive", "negative", "bullish", "bearish", "offset", "de-risk", "secured",
                        "visibility", "strong", "weak", "attractive", "better", "worse"]) {
      expect(labels).not.toContain(word);
    }
    const sv = text(vst(VST_FORWARD)).toLowerCase();
    for (const word of ["stödjer", "positiv", "negativ", "säkrad", "motverkar", "stark", "attraktiv"]) {
      expect(sv).not.toContain(word);
    }
  });
});

describe("forward context -- English wording", () => {
  it("says unchanged, keeps the qualification, and never drops it for FCF", () => {
    const [ebitda, fcf, volume] = forwardContextLabels(VST_FORWARD, tEn);
    expect(ebitda).toBe(
      "2026 guidance for an EBITDA measure (management's definition) unchanged at $6.8 billion-$7.6 billion",
    );
    expect(fcf).toBe(
      "2026 guidance for a free-cash-flow measure (management's definition) unchanged at $3.925 billion-$4.725 billion",
    );
    expect(volume).toContain("one agreement can appear in more than one");
    expect(forwardUnknownLabels(VST_FORWARD, tEn)).toEqual([
      "Contract price, and contribution to revenue, earnings and cash flow, not established",
    ]);
  });

  it("shows GOOGL's raised capex with both figures and its revision count", () => {
    expect(forwardContextLabels(GOOGL_FORWARD, tEn)).toEqual([
      "2026 guidance for capital expenditure raised to $195 billion to $205 billion (from $180 billion to $190 billion) (2 verified revisions)",
    ]);
    expect(forwardUnknownLabels(GOOGL_FORWARD, tEn)).toEqual([]);
  });

  it("shows a single observation with its own quantities and delivery start", () => {
    expect(forwardContextLabels(AMD_FORWARD, tEn)).toEqual([
      "Contracted customer volume: OpenAI — 6 gigawatts of Instinct GPUs, deliveries from 2026",
    ]);
  });

  it("names each unestablished aspect separately when not all four are missing", () => {
    const partial = { ...AMD_FORWARD, unestablishedEconomics: ["price" as const] };
    expect(forwardUnknownLabels(partial, tEn)).toEqual(["Contract price not established"]);
  });
});

describe("forward context -- a withheld recommendation (AMD)", () => {
  it("keeps the unestablished economics with the volume, not among what blocks a decision", () => {
    const after = text(vst(AMD_FORWARD, "no_decision"));
    expect(after).toContain(
      "Framåtblickande underlag: Kontrakterad kundvolym: OpenAI — 6 gigawatts of Instinct GPUs, leveranser från 2026 · Avtalspris samt bidrag till intäkter, resultat och kassaflöde är inte fastställda",
    );
    const blockers = after.split("Vad som behöver lösas:")[1] ?? "";
    expect(blockers.split("Vad skulle ändra bilden")[0]).not.toContain("Avtalspris");
  });
});
