import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { en } from "../i18n/translations/en";
import { AtlasInvestmentReasoning } from "./AtlasInvestmentReasoning";
import { valuationBasisLabel, valuationEvidenceLabel } from "./describeRecommendationReasoning";
import type { DecisionAction, InvestmentDecisionView } from "./investmentDecisionApi";
import type { RecommendationReasoningView } from "./reasoningContract";

/**
 * Valuation Observation Integrity in the reasoning card: how much fiscal-year
 * history a valuation rests on, said once and only when it matters. The
 * reasoning payloads below are the real `/investment-decision` reasoning for
 * each ticker, serialized from a copy of the live database (forward context
 * omitted; only the valuation entry of the signal summary kept). Fixture
 * data, not rules: nothing in the card knows a ticker.
 */
const REAL: Record<string, RecommendationReasoningView> = {
  "AAPL": {
    "counterDrivers": [
      {
        "engine": "valuation",
        "kind": "valuation_expensive",
        "polarity": "adverse",
        "sourceStatus": "expensive"
      }
    ],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation_support",
        "kind": "analysis_complete_unresolved"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_not_elevated",
        "polarity": "supportive",
        "sourceStatus": "not_high"
      },
      {
        "engine": "capital_allocation",
        "kind": "capital_allocation_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
      }
    ],
    "recommendationConviction": {
      "analyticalReasons": [],
      "evidentialReasons": [
        "company_fundamentals_evidence_only"
      ],
      "level": "low"
    },
    "riskBasis": {
      "elevatedCategories": [
        "valuation_risk"
      ],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_low",
        "excluded": [
          {
            "factId": "e746ce4c437fda6c28263fe13be5f157:v1:free_cash_flow:2027-09-26",
            "reason": "future_period"
          }
        ],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 10959000000.0,
            "capitalExpenditureFactId": "0cc9c40e49fb19dea490973ac8b70766:v2:capital_expenditure:2023-09-30",
            "freeCashFlow": 99584000000.0,
            "freeCashFlowFactId": "0cc9c40e49fb19dea490973ac8b70766:v2:free_cash_flow:2023-09-30",
            "operatingCashFlow": 110543000000.0,
            "period": "2023-09-30",
            "ratio": 0.9507883809920121,
            "sourceRecordIds": [
              "0cc9c40e49fb19dea490973ac8b70766:v2"
            ],
            "totalDebt": 105103000000.0,
            "totalDebtFactId": "0cc9c40e49fb19dea490973ac8b70766:v2:total_debt:2023-09-30",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 9447000000.0,
            "capitalExpenditureFactId": "432fb31d2151fc0d8f12d8cb6e38f95c:v2:capital_expenditure:2024-09-28",
            "freeCashFlow": 108807000000.0,
            "freeCashFlowFactId": "432fb31d2151fc0d8f12d8cb6e38f95c:v2:free_cash_flow:2024-09-28",
            "operatingCashFlow": 118254000000.0,
            "period": "2024-09-28",
            "ratio": 0.8174099819033606,
            "sourceRecordIds": [
              "432fb31d2151fc0d8f12d8cb6e38f95c:v2"
            ],
            "totalDebt": 96662000000.0,
            "totalDebtFactId": "432fb31d2151fc0d8f12d8cb6e38f95c:v2:total_debt:2024-09-28",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 12715000000.0,
            "capitalExpenditureFactId": "498aa362576368d74688855f1d4bf361:v2:capital_expenditure:2025-09-27",
            "freeCashFlow": 98767000000.0,
            "freeCashFlowFactId": "498aa362576368d74688855f1d4bf361:v2:free_cash_flow:2025-09-27",
            "operatingCashFlow": 111482000000.0,
            "period": "2025-09-27",
            "ratio": 0.8133869144794675,
            "sourceRecordIds": [
              "498aa362576368d74688855f1d4bf361:v2"
            ],
            "totalDebt": 90678000000.0,
            "totalDebtFactId": "498aa362576368d74688855f1d4bf361:v2:total_debt:2025-09-27",
            "unit": "USD"
          }
        ],
        "industry": "CONSUMER ELECTRONICS",
        "latest": {
          "capitalExpenditure": 12715000000.0,
          "capitalExpenditureFactId": "498aa362576368d74688855f1d4bf361:v2:capital_expenditure:2025-09-27",
          "freeCashFlow": 98767000000.0,
          "freeCashFlowFactId": "498aa362576368d74688855f1d4bf361:v2:free_cash_flow:2025-09-27",
          "operatingCashFlow": 111482000000.0,
          "period": "2025-09-27",
          "ratio": 0.8133869144794675,
          "sourceRecordIds": [
            "498aa362576368d74688855f1d4bf361:v2"
          ],
          "totalDebt": 90678000000.0,
          "totalDebtFactId": "498aa362576368d74688855f1d4bf361:v2:total_debt:2025-09-27",
          "unit": "USD"
        },
        "level": "low",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": 0.021401431811316145,
        "engine": "valuation",
        "evidenceEligibility": "eligible",
        "freeCashFlowCagr": null,
        "historicalMedianYield": 0.1066743087186122,
        "historicalObservationCount": 16,
        "historicalPercentile": 0.0,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "expensive",
        "state": "conclusive"
      }
    ],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "lower_valuation",
      "capital_allocation_deteriorates"
    ]
  },
  "ASML": {
    "counterDrivers": [],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "valuation_support",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_not_elevated",
        "polarity": "supportive",
        "sourceStatus": "not_high"
      },
      {
        "engine": "capital_allocation",
        "kind": "capital_allocation_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
      }
    ],
    "recommendationConviction": null,
    "riskBasis": {
      "elevatedCategories": [],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_low",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 2155600000.0,
            "capitalExpenditureFactId": "f6a9faa35221a48886d43be9951462c4:v1:capital_expenditure:2023-12-31",
            "freeCashFlow": 3287800000.0,
            "freeCashFlowFactId": "f6a9faa35221a48886d43be9951462c4:v1:free_cash_flow:2023-12-31",
            "operatingCashFlow": 5443400000.0,
            "period": "2023-12-31",
            "ratio": 0.85086526803101,
            "sourceRecordIds": [
              "f6a9faa35221a48886d43be9951462c4:v1"
            ],
            "totalDebt": 4631600000.0,
            "totalDebtFactId": "f6a9faa35221a48886d43be9951462c4:v1:total_debt:2023-12-31",
            "unit": "EUR"
          },
          {
            "capitalExpenditure": 2067200000.0,
            "capitalExpenditureFactId": "451c6ab22e2b8bb4571cc3344ea09194:v1:capital_expenditure:2024-12-31",
            "freeCashFlow": 9099000000.0,
            "freeCashFlowFactId": "451c6ab22e2b8bb4571cc3344ea09194:v1:free_cash_flow:2024-12-31",
            "operatingCashFlow": 11166200000.0,
            "period": "2024-12-31",
            "ratio": 0.41980261861689744,
            "sourceRecordIds": [
              "451c6ab22e2b8bb4571cc3344ea09194:v1"
            ],
            "totalDebt": 4687600000.0,
            "totalDebtFactId": "451c6ab22e2b8bb4571cc3344ea09194:v1:total_debt:2024-12-31",
            "unit": "EUR"
          },
          {
            "capitalExpenditure": 1573600000.0,
            "capitalExpenditureFactId": "37939bbbdefd73fe611dd111df51a865:v1:capital_expenditure:2025-12-31",
            "freeCashFlow": 11084900000.0,
            "freeCashFlowFactId": "37939bbbdefd73fe611dd111df51a865:v1:free_cash_flow:2025-12-31",
            "operatingCashFlow": 12658500000.0,
            "period": "2025-12-31",
            "ratio": 0.34687364221669237,
            "sourceRecordIds": [
              "37939bbbdefd73fe611dd111df51a865:v1"
            ],
            "totalDebt": 4390900000.0,
            "totalDebtFactId": "37939bbbdefd73fe611dd111df51a865:v1:total_debt:2025-12-31",
            "unit": "EUR"
          }
        ],
        "industry": "SEMICONDUCTOR EQUIPMENT & MATERIALS",
        "latest": {
          "capitalExpenditure": 1573600000.0,
          "capitalExpenditureFactId": "37939bbbdefd73fe611dd111df51a865:v1:capital_expenditure:2025-12-31",
          "freeCashFlow": 11084900000.0,
          "freeCashFlowFactId": "37939bbbdefd73fe611dd111df51a865:v1:free_cash_flow:2025-12-31",
          "operatingCashFlow": 12658500000.0,
          "period": "2025-12-31",
          "ratio": 0.34687364221669237,
          "sourceRecordIds": [
            "37939bbbdefd73fe611dd111df51a865:v1"
          ],
          "totalDebt": 4390900000.0,
          "totalDebtFactId": "37939bbbdefd73fe611dd111df51a865:v1:total_debt:2025-12-31",
          "unit": "EUR"
        },
        "level": "low",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": null,
        "engine": "valuation",
        "evidenceEligibility": "insufficient",
        "freeCashFlowCagr": null,
        "historicalMedianYield": null,
        "historicalObservationCount": null,
        "historicalPercentile": null,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "insufficient_input",
        "state": "inconclusive"
      }
    ],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "capital_allocation_deteriorates"
    ]
  },
  "AZN": {
    "counterDrivers": [],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "valuation_support",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_not_elevated",
        "polarity": "supportive",
        "sourceStatus": "not_high"
      },
      {
        "engine": "capital_allocation",
        "kind": "capital_allocation_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
      }
    ],
    "recommendationConviction": null,
    "riskBasis": {
      "elevatedCategories": [],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_moderate",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 1361000000.0,
            "capitalExpenditureFactId": "700d2b31dbc3a396ed635a399f478ca3:v1:capital_expenditure:2023-12-31",
            "freeCashFlow": 8984000000.0,
            "freeCashFlowFactId": "700d2b31dbc3a396ed635a399f478ca3:v1:free_cash_flow:2023-12-31",
            "operatingCashFlow": 10345000000.0,
            "period": "2023-12-31",
            "ratio": 2.657709038182697,
            "sourceRecordIds": [
              "700d2b31dbc3a396ed635a399f478ca3:v1"
            ],
            "totalDebt": 27494000000.0,
            "totalDebtFactId": "700d2b31dbc3a396ed635a399f478ca3:v1:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 1924000000.0,
            "capitalExpenditureFactId": "f2f6f3cace12ca411fe260e1779e5c0a:v1:capital_expenditure:2024-12-31",
            "freeCashFlow": 9937000000.0,
            "freeCashFlowFactId": "f2f6f3cace12ca411fe260e1779e5c0a:v1:free_cash_flow:2024-12-31",
            "operatingCashFlow": 11861000000.0,
            "period": "2024-12-31",
            "ratio": 2.4317511171064834,
            "sourceRecordIds": [
              "f2f6f3cace12ca411fe260e1779e5c0a:v1"
            ],
            "totalDebt": 28843000000.0,
            "totalDebtFactId": "f2f6f3cace12ca411fe260e1779e5c0a:v1:total_debt:2024-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 2810000000.0,
            "capitalExpenditureFactId": "220c5e3df6df8bcfac078ddb62986f49:v1:capital_expenditure:2025-12-31",
            "freeCashFlow": 11765000000.0,
            "freeCashFlowFactId": "220c5e3df6df8bcfac078ddb62986f49:v1:free_cash_flow:2025-12-31",
            "operatingCashFlow": 14575000000.0,
            "period": "2025-12-31",
            "ratio": 1.9086792452830188,
            "sourceRecordIds": [
              "220c5e3df6df8bcfac078ddb62986f49:v1"
            ],
            "totalDebt": 27819000000.0,
            "totalDebtFactId": "220c5e3df6df8bcfac078ddb62986f49:v1:total_debt:2025-12-31",
            "unit": "USD"
          }
        ],
        "industry": "DRUG MANUFACTURERS - GENERAL",
        "latest": {
          "capitalExpenditure": 2810000000.0,
          "capitalExpenditureFactId": "220c5e3df6df8bcfac078ddb62986f49:v1:capital_expenditure:2025-12-31",
          "freeCashFlow": 11765000000.0,
          "freeCashFlowFactId": "220c5e3df6df8bcfac078ddb62986f49:v1:free_cash_flow:2025-12-31",
          "operatingCashFlow": 14575000000.0,
          "period": "2025-12-31",
          "ratio": 1.9086792452830188,
          "sourceRecordIds": [
            "220c5e3df6df8bcfac078ddb62986f49:v1"
          ],
          "totalDebt": 27819000000.0,
          "totalDebtFactId": "220c5e3df6df8bcfac078ddb62986f49:v1:total_debt:2025-12-31",
          "unit": "USD"
        },
        "level": "moderate",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": 0.04471287476702546,
        "engine": "valuation",
        "evidenceEligibility": "insufficient",
        "freeCashFlowCagr": null,
        "historicalMedianYield": null,
        "historicalObservationCount": null,
        "historicalPercentile": null,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "insufficient_input",
        "state": "inconclusive"
      }
    ],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "capital_allocation_deteriorates"
    ]
  },
  "GOOGL": {
    "counterDrivers": [
      {
        "engine": "valuation",
        "kind": "valuation_expensive",
        "polarity": "adverse",
        "sourceStatus": "expensive"
      }
    ],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation_support",
        "kind": "analysis_complete_unresolved"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_not_elevated",
        "polarity": "supportive",
        "sourceStatus": "not_high"
      },
      {
        "engine": "capital_allocation",
        "kind": "capital_allocation_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
      }
    ],
    "recommendationConviction": {
      "analyticalReasons": [],
      "evidentialReasons": [
        "company_fundamentals_evidence_only"
      ],
      "level": "low"
    },
    "riskBasis": {
      "elevatedCategories": [
        "valuation_risk"
      ],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_low",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 32251000000.0,
            "capitalExpenditureFactId": "1e3e75c8fc74a5d21570a2e377aedef8:v2:capital_expenditure:2023-12-31",
            "freeCashFlow": 69495000000.0,
            "freeCashFlowFactId": "1e3e75c8fc74a5d21570a2e377aedef8:v2:free_cash_flow:2023-12-31",
            "operatingCashFlow": 101746000000.0,
            "period": "2023-12-31",
            "ratio": 0.1264914591237002,
            "sourceRecordIds": [
              "1e3e75c8fc74a5d21570a2e377aedef8:v2"
            ],
            "totalDebt": 12870000000.0,
            "totalDebtFactId": "1e3e75c8fc74a5d21570a2e377aedef8:v2:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 52535000000.0,
            "capitalExpenditureFactId": "dfc34251a9e976ee41327d34ebf46b25:v2:capital_expenditure:2024-12-31",
            "freeCashFlow": 72764000000.0,
            "freeCashFlowFactId": "dfc34251a9e976ee41327d34ebf46b25:v2:free_cash_flow:2024-12-31",
            "operatingCashFlow": 125299000000.0,
            "period": "2024-12-31",
            "ratio": 0.0948291686286403,
            "sourceRecordIds": [
              "dfc34251a9e976ee41327d34ebf46b25:v2"
            ],
            "totalDebt": 11882000000.0,
            "totalDebtFactId": "dfc34251a9e976ee41327d34ebf46b25:v2:total_debt:2024-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 91447000000.0,
            "capitalExpenditureFactId": "397c8c85fc7ce7cb60564022e7be0a70:v2:capital_expenditure:2025-12-31",
            "freeCashFlow": 73266000000.0,
            "freeCashFlowFactId": "397c8c85fc7ce7cb60564022e7be0a70:v2:free_cash_flow:2025-12-31",
            "operatingCashFlow": 164713000000.0,
            "period": "2025-12-31",
            "ratio": 0.29471262134743464,
            "sourceRecordIds": [
              "397c8c85fc7ce7cb60564022e7be0a70:v2"
            ],
            "totalDebt": 48543000000.0,
            "totalDebtFactId": "397c8c85fc7ce7cb60564022e7be0a70:v2:total_debt:2025-12-31",
            "unit": "USD"
          }
        ],
        "industry": "INTERNET CONTENT & INFORMATION",
        "latest": {
          "capitalExpenditure": 91447000000.0,
          "capitalExpenditureFactId": "397c8c85fc7ce7cb60564022e7be0a70:v2:capital_expenditure:2025-12-31",
          "freeCashFlow": 73266000000.0,
          "freeCashFlowFactId": "397c8c85fc7ce7cb60564022e7be0a70:v2:free_cash_flow:2025-12-31",
          "operatingCashFlow": 164713000000.0,
          "period": "2025-12-31",
          "ratio": 0.29471262134743464,
          "sourceRecordIds": [
            "397c8c85fc7ce7cb60564022e7be0a70:v2"
          ],
          "totalDebt": 48543000000.0,
          "totalDebtFactId": "397c8c85fc7ce7cb60564022e7be0a70:v2:total_debt:2025-12-31",
          "unit": "USD"
        },
        "level": "low",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": 0.03587738079015575,
        "engine": "valuation",
        "evidenceEligibility": "eligible",
        "freeCashFlowCagr": null,
        "historicalMedianYield": 0.07962110103166893,
        "historicalObservationCount": 10,
        "historicalPercentile": 0.0,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "expensive",
        "state": "conclusive"
      }
    ],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "lower_valuation",
      "capital_allocation_deteriorates"
    ]
  },
  "GS": {
    "counterDrivers": [],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation_support",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [],
    "recommendationConviction": null,
    "riskBasis": {
      "elevatedCategories": [],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "measure_not_applicable",
        "excluded": [],
        "gaps": [],
        "history": [],
        "industry": "CAPITAL MARKETS",
        "latest": null,
        "level": "not_applicable",
        "measure": null
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": null,
        "engine": "valuation",
        "evidenceEligibility": "not_applicable",
        "freeCashFlowCagr": null,
        "historicalMedianYield": null,
        "historicalObservationCount": null,
        "historicalPercentile": null,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "not_applicable",
        "state": "not_evaluated"
      }
    ],
    "whatWouldChange": [
      "no_credible_trigger_identified"
    ]
  },
  "SHOP": {
    "counterDrivers": [],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "valuation_support",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "financial_risk",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [
      {
        "engine": "growth",
        "kind": "growth_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
      }
    ],
    "recommendationConviction": null,
    "riskBasis": {
      "elevatedCategories": [],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "no_eligible_evidence",
        "excluded": [],
        "gaps": [
          "missing_debt"
        ],
        "history": [],
        "industry": "SOFTWARE - APPLICATION",
        "latest": null,
        "level": "insufficient_input",
        "measure": null
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": 0.010694353733998251,
        "engine": "valuation",
        "evidenceEligibility": "limited",
        "freeCashFlowCagr": null,
        "historicalMedianYield": 0.011691661785013518,
        "historicalObservationCount": 1,
        "historicalPercentile": 0.0,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "insufficient_input",
        "state": "inconclusive"
      }
    ],
    "whatWouldChange": [
      "growth_deteriorates"
    ]
  },
  "TSM": {
    "counterDrivers": [],
    "forwardContext": null,
    "keyUnknowns": [
      {
        "engine": "valuation",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "valuation_support",
        "kind": "analysis_input_missing"
      },
      {
        "engine": "business_quality",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "industry_context",
        "kind": "not_connected_to_direction"
      },
      {
        "engine": "expected_return",
        "kind": "not_connected_to_direction"
      }
    ],
    "primaryDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_not_elevated",
        "polarity": "supportive",
        "sourceStatus": "not_high"
      },
      {
        "engine": "capital_allocation",
        "kind": "capital_allocation_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
      }
    ],
    "recommendationConviction": null,
    "riskBasis": {
      "elevatedCategories": [],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_low",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 35231800000.0,
            "capitalExpenditureFactId": "d0ed4bd3e927b72437269a2fbe720f81:v1:capital_expenditure:2022-12-31",
            "freeCashFlow": 17179500000.0,
            "freeCashFlowFactId": "d0ed4bd3e927b72437269a2fbe720f81:v1:free_cash_flow:2022-12-31",
            "operatingCashFlow": 52411300000.0,
            "period": "2022-12-31",
            "ratio": 0.01494715834180797,
            "sourceRecordIds": [
              "d0ed4bd3e927b72437269a2fbe720f81:v1"
            ],
            "totalDebt": 783400000.0,
            "totalDebtFactId": "d0ed4bd3e927b72437269a2fbe720f81:v1:total_debt:2022-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 31019500000.0,
            "capitalExpenditureFactId": "8d9f870ad703ffaa66c86e760a101a6d:v1:capital_expenditure:2023-12-31",
            "freeCashFlow": 9541200000.0,
            "freeCashFlowFactId": "8d9f870ad703ffaa66c86e760a101a6d:v1:free_cash_flow:2023-12-31",
            "operatingCashFlow": 40560700000.0,
            "period": "2023-12-31",
            "ratio": 0.011010658100082098,
            "sourceRecordIds": [
              "8d9f870ad703ffaa66c86e760a101a6d:v1"
            ],
            "totalDebt": 446600000.0,
            "totalDebtFactId": "8d9f870ad703ffaa66c86e760a101a6d:v1:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 29155400000.0,
            "capitalExpenditureFactId": "d14e6f3875ee7adfb44f2b12d00527a1:v1:capital_expenditure:2024-12-31",
            "freeCashFlow": 26537700000.0,
            "freeCashFlowFactId": "d14e6f3875ee7adfb44f2b12d00527a1:v1:free_cash_flow:2024-12-31",
            "operatingCashFlow": 55693100000.0,
            "period": "2024-12-31",
            "ratio": 0.05020370566551332,
            "sourceRecordIds": [
              "d14e6f3875ee7adfb44f2b12d00527a1:v1"
            ],
            "totalDebt": 2796000000.0,
            "totalDebtFactId": "d14e6f3875ee7adfb44f2b12d00527a1:v1:total_debt:2024-12-31",
            "unit": "USD"
          }
        ],
        "industry": "SEMICONDUCTORS",
        "latest": {
          "capitalExpenditure": 29155400000.0,
          "capitalExpenditureFactId": "d14e6f3875ee7adfb44f2b12d00527a1:v1:capital_expenditure:2024-12-31",
          "freeCashFlow": 26537700000.0,
          "freeCashFlowFactId": "d14e6f3875ee7adfb44f2b12d00527a1:v1:free_cash_flow:2024-12-31",
          "operatingCashFlow": 55693100000.0,
          "period": "2024-12-31",
          "ratio": 0.05020370566551332,
          "sourceRecordIds": [
            "d14e6f3875ee7adfb44f2b12d00527a1:v1"
          ],
          "totalDebt": 2796000000.0,
          "totalDebtFactId": "d14e6f3875ee7adfb44f2b12d00527a1:v1:total_debt:2024-12-31",
          "unit": "USD"
        },
        "level": "low",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [
      {
        "currentYield": 0.012258242985038926,
        "engine": "valuation",
        "evidenceEligibility": "insufficient",
        "freeCashFlowCagr": null,
        "historicalMedianYield": null,
        "historicalObservationCount": null,
        "historicalPercentile": null,
        "influencedDirection": true,
        "revenueCagr": null,
        "sourceStatus": "insufficient_input",
        "state": "inconclusive"
      }
    ],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "capital_allocation_deteriorates"
    ]
  }
};

function plain(text: string | null | undefined): string {
  return (text ?? "").replace(/[  ]/g, " ");
}

function fixture(ticker: string): RecommendationReasoningView {
  const reasoning = REAL[ticker];
  if (!reasoning) throw new Error(`no fixture for ${ticker}`);
  return reasoning;
}

function decision(ticker: string, action: DecisionAction): InvestmentDecisionView {
  return {
    caseId: "case-fixture",
    action,
    qualifiers: [],
    supportingReasons: [],
    blockers: [],
    changeTrigger: null,
    generatedAt: "2026-09-13T00:00:00Z",
    reasoning: fixture(ticker),
  };
}

function Wrapper({ view }: { view: InvestmentDecisionView }) {
  const { t, language } = useTranslation();
  return <AtlasInvestmentReasoning decision={view} t={t} locale={language === "sv" ? "sv-SE" : "en-US"} />;
}

/** Rendered through the real provider (Swedish by default), one line per paragraph. */
function lines(view: InvestmentDecisionView): string[] {
  const { container } = render(
    <LanguageProvider>
      <Wrapper view={view} />
    </LanguageProvider>,
  );
  return Array.from(container.querySelectorAll("p")).map((p) => plain(p.textContent));
}

function tEn(key: keyof typeof en, params: Record<string, string | number> = {}): string {
  return Object.entries(params).reduce((s, [k, v]) => s.split("{{" + k + "}}").join(String(v)), en[key] as string);
}
const T = (key: keyof typeof en, params?: Record<string, string | number>) => tEn(key, params);

function withoutEligibility(ticker: string): RecommendationReasoningView {
  const reasoning = fixture(ticker);
  return {
    ...reasoning,
    signalSummary: (reasoning.signalSummary ?? []).map(({ evidenceEligibility: _drop, ...rest }) => rest),
  };
}

describe("thin valuation history says so, and never reads as a conclusion", () => {
  it("AZN: a current yield with no earlier fiscal year does not affect the recommendation", () => {
    const rendered = lines(decision("AZN", "no_decision"));
    expect(rendered).toContain(
      "Värderingshistorik saknas: dagens FCF-avkastning (4,5 %) har inget tidigare räkenskapsår att jämföras med, så värderingen påverkar inte rekommendationen.",
    );
    expect(rendered.join("\n")).not.toMatch(/Högt värderad|Rimligt värderad|Undervärderad/);
  });

  it("TSM: apparent cheapness against one earlier price is no support and no history", () => {
    const rendered = lines(decision("TSM", "no_decision"));
    expect(rendered.some((l) => l.startsWith("Värderingshistorik saknas: dagens FCF-avkastning (1,2 %)"))).toBe(true);
    expect(rendered.join("\n")).not.toMatch(/Undervärderad|Värderingen ger stöd/);
  });

  it("SHOP: one earlier fiscal year is limited history, not an expensive valuation", () => {
    const rendered = lines(decision("SHOP", "no_decision"));
    expect(rendered).toContain(
      "Begränsat värderingsunderlag: dagens FCF-avkastning (1,1 %) kan bara jämföras med ett tidigare räkenskapsår — för få för att värderingen ska påverka rekommendationen.",
    );
    expect(rendered.join("\n")).not.toMatch(/Högt värderad/);
  });

  it("GS: a bank gets one quiet not-applicable line and no valuation unknown", () => {
    const rendered = lines(decision("GS", "no_decision"));
    expect(rendered).toContain(
      "Värdering: FCF-avkastning används inte för att värdera banker, försäkringsbolag och värdepappersföretag.",
    );
    const unknownRow = rendered.find((l) => l.startsWith("Behöver redas ut:") || l.startsWith("Oklart:")) ?? "";
    expect(unknownRow).not.toMatch(/^.*Värdering:/);
  });
});

describe("deep history stays quiet and says what it rests on", () => {
  it("GOOGL: expensive against ten fiscal years, with the share-count proxy named once", () => {
    const rendered = lines(decision("GOOGL", "hold"));
    expect(rendered).toContain(
      "Högt värderad: dagens FCF-avkastning (3,6 %) är lägre än under alla 10 tidigare räkenskapsår i bolagets egen historik (median 8,0 %) — ingen jämförelse med konkurrenter. Tidigare marknadsvärden bygger på dagens antal aktier.",
    );
    expect(rendered.join("\n")).not.toMatch(/Begränsat värderingsunderlag|Värderingshistorik saknas/);
  });

  it("AAPL: the valuation is today's statement cash flow against sixteen fiscal years", () => {
    const rendered = lines(decision("AAPL", "wait"));
    expect(rendered.some((l) => l.startsWith("Högt värderad: dagens FCF-avkastning (2,1 %) är lägre än under alla 16 tidigare räkenskapsår"))).toBe(true);
  });
});

describe("wording, in English, through the real dictionary", () => {
  it("names the depth and the consequence", () => {
    expect(valuationEvidenceLabel(fixture("SHOP").signalSummary, T, "en-US")).toBe(
      "Limited valuation history: today's FCF yield (1.1%) can only be compared with one earlier fiscal year — too few for valuation to affect the recommendation.",
    );
    expect(valuationEvidenceLabel(fixture("AZN").signalSummary, T, "en-US")).toBe(
      "No valuation history yet: today's FCF yield (4.5%) has no earlier fiscal year to compare with, so valuation does not affect the recommendation.",
    );
    expect(valuationEvidenceLabel(fixture("GS").signalSummary, T, "en-US")).toBe(
      "Valuation: free cash flow yield is not used to value banks, insurers and securities firms.",
    );
  });

  it("is silent for eligible history and for a valuation with no current yield", () => {
    expect(valuationEvidenceLabel(fixture("GOOGL").signalSummary, T, "en-US")).toBeNull();
    expect(valuationEvidenceLabel(fixture("ASML").signalSummary, T, "en-US")).toBeNull();
  });

  it("counts fiscal years, not observations, when the row says it may", () => {
    expect(valuationBasisLabel(fixture("GOOGL").signalSummary, T, "en-US")).toBe(
      "Expensive: today's FCF yield (3.6%) is lower than in all 10 earlier fiscal years of the company's own history (median 8.0%) — not a comparison with peers. Earlier market values use today's share count.",
    );
  });
});

describe("rows stored before eligibility existed keep their own meaning", () => {
  it("a legacy row counts observations and adds no evidence line", () => {
    const legacy = withoutEligibility("GOOGL");
    const basis = valuationBasisLabel(legacy.signalSummary, T, "en-US") ?? "";
    expect(basis).toMatch(/earlier observations/);
    expect(basis).not.toMatch(/share count/);
    expect(valuationEvidenceLabel(withoutEligibility("SHOP").signalSummary, T, "en-US")).toBeNull();
  });
});
