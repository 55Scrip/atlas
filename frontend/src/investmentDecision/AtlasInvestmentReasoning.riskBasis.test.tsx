import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { en } from "../i18n/translations/en";
import { AtlasInvestmentReasoning } from "./AtlasInvestmentReasoning";
import { formatMultiple, formatReportedAmount, riskBasisLabel } from "./describeRecommendationReasoning";
import type { DecisionAction, InvestmentDecisionView } from "./investmentDecisionApi";
import type { RecommendationReasoningView, RiskDriverBasisView } from "./reasoningContract";

/**
 * Financial Risk v2 in the reasoning card. The reasoning payloads below are
 * the real `/investment-decision` reasoning for each ticker, serialized from
 * a copy of the live database (signal summary and forward context omitted)
 * -- fixture data, not rules: nothing in the card knows a ticker.
 */
const REAL: Record<string, RecommendationReasoningView> = {
  "AVGO": {
    "counterDrivers": [],
    "forwardContext": null,
    "keyUnknowns": [
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
        "engine": "valuation_support",
        "kind": "valuation_supported",
        "polarity": "supportive",
        "sourceStatus": "supported"
      },
      {
        "engine": "growth",
        "kind": "growth_strong",
        "polarity": "supportive",
        "sourceStatus": "strong"
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
        "industry": "SEMICONDUCTORS",
        "latest": null,
        "level": "insufficient_input",
        "measure": null
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "valuation_becomes_expensive",
      "valuation_support_lost",
      "growth_deteriorates",
      "capital_allocation_deteriorates"
    ]
  },
  "CAT": {
    "counterDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_elevated",
        "polarity": "adverse",
        "sourceStatus": "high"
      },
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
        "financial_risk",
        "valuation_risk"
      ],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_high",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 1597000000.0,
            "capitalExpenditureFactId": "7e620b80d5eb49ea88cfe9410beedc39:v1:capital_expenditure:2023-12-31",
            "freeCashFlow": 11288000000.0,
            "freeCashFlowFactId": "7e620b80d5eb49ea88cfe9410beedc39:v1:free_cash_flow:2023-12-31",
            "operatingCashFlow": 12885000000.0,
            "period": "2023-12-31",
            "ratio": 2.2596041909196742,
            "sourceRecordIds": [
              "7e620b80d5eb49ea88cfe9410beedc39:v1"
            ],
            "totalDebt": 29115000000.0,
            "totalDebtFactId": "7e620b80d5eb49ea88cfe9410beedc39:v1:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 1988000000.0,
            "capitalExpenditureFactId": "bb5c55fa2a3d5a9cfd3da1469822ac3b:v1:capital_expenditure:2024-12-31",
            "freeCashFlow": 10047000000.0,
            "freeCashFlowFactId": "bb5c55fa2a3d5a9cfd3da1469822ac3b:v1:free_cash_flow:2024-12-31",
            "operatingCashFlow": 12035000000.0,
            "period": "2024-12-31",
            "ratio": 2.63764021603656,
            "sourceRecordIds": [
              "bb5c55fa2a3d5a9cfd3da1469822ac3b:v1"
            ],
            "totalDebt": 31744000000.0,
            "totalDebtFactId": "bb5c55fa2a3d5a9cfd3da1469822ac3b:v1:total_debt:2024-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 2821000000.0,
            "capitalExpenditureFactId": "93859c641ca5bbaba4f861c7577fd8c0:v1:capital_expenditure:2025-12-31",
            "freeCashFlow": 8918000000.0,
            "freeCashFlowFactId": "93859c641ca5bbaba4f861c7577fd8c0:v1:free_cash_flow:2025-12-31",
            "operatingCashFlow": 11739000000.0,
            "period": "2025-12-31",
            "ratio": 3.0845898287758753,
            "sourceRecordIds": [
              "93859c641ca5bbaba4f861c7577fd8c0:v1"
            ],
            "totalDebt": 36210000000.0,
            "totalDebtFactId": "93859c641ca5bbaba4f861c7577fd8c0:v1:total_debt:2025-12-31",
            "unit": "USD"
          }
        ],
        "industry": "FARM & HEAVY CONSTRUCTION MACHINERY",
        "latest": {
          "capitalExpenditure": 2821000000.0,
          "capitalExpenditureFactId": "93859c641ca5bbaba4f861c7577fd8c0:v1:capital_expenditure:2025-12-31",
          "freeCashFlow": 8918000000.0,
          "freeCashFlowFactId": "93859c641ca5bbaba4f861c7577fd8c0:v1:free_cash_flow:2025-12-31",
          "operatingCashFlow": 11739000000.0,
          "period": "2025-12-31",
          "ratio": 3.0845898287758753,
          "sourceRecordIds": [
            "93859c641ca5bbaba4f861c7577fd8c0:v1"
          ],
          "totalDebt": 36210000000.0,
          "totalDebtFactId": "93859c641ca5bbaba4f861c7577fd8c0:v1:total_debt:2025-12-31",
          "unit": "USD"
        },
        "level": "high",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "lower_valuation",
      "capital_allocation_deteriorates"
    ]
  },
  "GOOGL": {
    "counterDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_elevated",
        "polarity": "adverse",
        "sourceStatus": "high"
      },
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
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
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
    "signalSummary": [],
    "whatWouldChange": [
      "valuation_becomes_expensive"
    ]
  },
  "INTC": {
    "counterDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_elevated",
        "polarity": "adverse",
        "sourceStatus": "high"
      },
      {
        "engine": "capital_allocation",
        "kind": "capital_allocation_weak",
        "polarity": "adverse",
        "sourceStatus": "weak"
      }
    ],
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
    "primaryDrivers": [],
    "recommendationConviction": {
      "analyticalReasons": [],
      "evidentialReasons": [
        "company_fundamentals_evidence_only"
      ],
      "level": "low"
    },
    "riskBasis": {
      "elevatedCategories": [
        "financial_risk"
      ],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_high",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 25750000000.0,
            "capitalExpenditureFactId": "afde05a950d82a660f3b104d1146ee40:v1:capital_expenditure:2023-12-30",
            "freeCashFlow": -14279000000.0,
            "freeCashFlowFactId": "afde05a950d82a660f3b104d1146ee40:v1:free_cash_flow:2023-12-30",
            "operatingCashFlow": 11471000000.0,
            "period": "2023-12-30",
            "ratio": 4.294830441984134,
            "sourceRecordIds": [
              "afde05a950d82a660f3b104d1146ee40:v1"
            ],
            "totalDebt": 49266000000.0,
            "totalDebtFactId": "afde05a950d82a660f3b104d1146ee40:v1:total_debt:2023-12-30",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 23944000000.0,
            "capitalExpenditureFactId": "a5d77843e6be3b6e8a1567a52ff8922a:v1:capital_expenditure:2024-12-28",
            "freeCashFlow": -15656000000.0,
            "freeCashFlowFactId": "a5d77843e6be3b6e8a1567a52ff8922a:v1:free_cash_flow:2024-12-28",
            "operatingCashFlow": 8288000000.0,
            "period": "2024-12-28",
            "ratio": 6.0341457528957525,
            "sourceRecordIds": [
              "a5d77843e6be3b6e8a1567a52ff8922a:v1"
            ],
            "totalDebt": 50011000000.0,
            "totalDebtFactId": "a5d77843e6be3b6e8a1567a52ff8922a:v1:total_debt:2024-12-28",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 14646000000.0,
            "capitalExpenditureFactId": "3a877697c6ebf96e23eef5f909d399d8:v1:capital_expenditure:2025-12-27",
            "freeCashFlow": -4949000000.0,
            "freeCashFlowFactId": "3a877697c6ebf96e23eef5f909d399d8:v1:free_cash_flow:2025-12-27",
            "operatingCashFlow": 9697000000.0,
            "period": "2025-12-27",
            "ratio": 4.804063112302774,
            "sourceRecordIds": [
              "3a877697c6ebf96e23eef5f909d399d8:v1"
            ],
            "totalDebt": 46585000000.0,
            "totalDebtFactId": "3a877697c6ebf96e23eef5f909d399d8:v1:total_debt:2025-12-27",
            "unit": "USD"
          }
        ],
        "industry": "SEMICONDUCTORS",
        "latest": {
          "capitalExpenditure": 14646000000.0,
          "capitalExpenditureFactId": "3a877697c6ebf96e23eef5f909d399d8:v1:capital_expenditure:2025-12-27",
          "freeCashFlow": -4949000000.0,
          "freeCashFlowFactId": "3a877697c6ebf96e23eef5f909d399d8:v1:free_cash_flow:2025-12-27",
          "operatingCashFlow": 9697000000.0,
          "period": "2025-12-27",
          "ratio": 4.804063112302774,
          "sourceRecordIds": [
            "3a877697c6ebf96e23eef5f909d399d8:v1"
          ],
          "totalDebt": 46585000000.0,
          "totalDebtFactId": "3a877697c6ebf96e23eef5f909d399d8:v1:total_debt:2025-12-27",
          "unit": "USD"
        },
        "level": "high",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "improved_capital_allocation_evidence"
    ]
  },
  "META": {
    "counterDrivers": [],
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
            "capitalExpenditure": 27045000000.0,
            "capitalExpenditureFactId": "8c8afbd05ec3a4bed7965883ac4a3db4:v1:capital_expenditure:2023-12-31",
            "freeCashFlow": 44068000000.0,
            "freeCashFlowFactId": "8c8afbd05ec3a4bed7965883ac4a3db4:v1:free_cash_flow:2023-12-31",
            "operatingCashFlow": 71113000000.0,
            "period": "2023-12-31",
            "ratio": 0.25853219523856397,
            "sourceRecordIds": [
              "8c8afbd05ec3a4bed7965883ac4a3db4:v1"
            ],
            "totalDebt": 18385000000.0,
            "totalDebtFactId": "8c8afbd05ec3a4bed7965883ac4a3db4:v1:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 37256000000.0,
            "capitalExpenditureFactId": "1435a46fdaf8206586c9749add8ccdbc:v1:capital_expenditure:2024-12-31",
            "freeCashFlow": 54072000000.0,
            "freeCashFlowFactId": "1435a46fdaf8206586c9749add8ccdbc:v1:free_cash_flow:2024-12-31",
            "operatingCashFlow": 91328000000.0,
            "period": "2024-12-31",
            "ratio": 0.31563156972669937,
            "sourceRecordIds": [
              "1435a46fdaf8206586c9749add8ccdbc:v1"
            ],
            "totalDebt": 28826000000.0,
            "totalDebtFactId": "1435a46fdaf8206586c9749add8ccdbc:v1:total_debt:2024-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 69691000000.0,
            "capitalExpenditureFactId": "2adddd1608791c901ab7a4e838d554bb:v1:capital_expenditure:2025-12-31",
            "freeCashFlow": 46109000000.0,
            "freeCashFlowFactId": "2adddd1608791c901ab7a4e838d554bb:v1:free_cash_flow:2025-12-31",
            "operatingCashFlow": 115800000000.0,
            "period": "2025-12-31",
            "ratio": 0.5072884283246978,
            "sourceRecordIds": [
              "2adddd1608791c901ab7a4e838d554bb:v1"
            ],
            "totalDebt": 58744000000.0,
            "totalDebtFactId": "2adddd1608791c901ab7a4e838d554bb:v1:total_debt:2025-12-31",
            "unit": "USD"
          }
        ],
        "industry": "INTERNET CONTENT & INFORMATION",
        "latest": {
          "capitalExpenditure": 69691000000.0,
          "capitalExpenditureFactId": "2adddd1608791c901ab7a4e838d554bb:v1:capital_expenditure:2025-12-31",
          "freeCashFlow": 46109000000.0,
          "freeCashFlowFactId": "2adddd1608791c901ab7a4e838d554bb:v1:free_cash_flow:2025-12-31",
          "operatingCashFlow": 115800000000.0,
          "period": "2025-12-31",
          "ratio": 0.5072884283246978,
          "sourceRecordIds": [
            "2adddd1608791c901ab7a4e838d554bb:v1"
          ],
          "totalDebt": 58744000000.0,
          "totalDebtFactId": "2adddd1608791c901ab7a4e838d554bb:v1:total_debt:2025-12-31",
          "unit": "USD"
        },
        "level": "low",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "valuation_becomes_expensive"
    ]
  },
  "SHOP": {
    "counterDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_elevated",
        "polarity": "adverse",
        "sourceStatus": "high"
      },
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
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "lower_valuation",
      "growth_deteriorates"
    ]
  },
  "UNP": {
    "counterDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_elevated",
        "polarity": "adverse",
        "sourceStatus": "high"
      },
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
        "financial_risk",
        "valuation_risk"
      ],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_high",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 3606000000.0,
            "capitalExpenditureFactId": "d23bc8a452e14bc682619cb876305e10:v1:capital_expenditure:2023-12-31",
            "freeCashFlow": 4773000000.0,
            "freeCashFlowFactId": "d23bc8a452e14bc682619cb876305e10:v1:free_cash_flow:2023-12-31",
            "operatingCashFlow": 8379000000.0,
            "period": "2023-12-31",
            "ratio": 3.888172812984843,
            "sourceRecordIds": [
              "d23bc8a452e14bc682619cb876305e10:v1"
            ],
            "totalDebt": 32579000000.0,
            "totalDebtFactId": "d23bc8a452e14bc682619cb876305e10:v1:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 3452000000.0,
            "capitalExpenditureFactId": "d4cb371cda724603f1065eba995d393e:v1:capital_expenditure:2024-12-31",
            "freeCashFlow": 5894000000.0,
            "freeCashFlowFactId": "d4cb371cda724603f1065eba995d393e:v1:free_cash_flow:2024-12-31",
            "operatingCashFlow": 9346000000.0,
            "period": "2024-12-31",
            "ratio": 3.3374705756473357,
            "sourceRecordIds": [
              "d4cb371cda724603f1065eba995d393e:v1"
            ],
            "totalDebt": 31192000000.0,
            "totalDebtFactId": "d4cb371cda724603f1065eba995d393e:v1:total_debt:2024-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 3791000000.0,
            "capitalExpenditureFactId": "540240c7a0633e6af181e585bfbde405:v1:capital_expenditure:2025-12-31",
            "freeCashFlow": 5499000000.0,
            "freeCashFlowFactId": "540240c7a0633e6af181e585bfbde405:v1:free_cash_flow:2025-12-31",
            "operatingCashFlow": 9290000000.0,
            "period": "2025-12-31",
            "ratio": 3.4245425188374594,
            "sourceRecordIds": [
              "540240c7a0633e6af181e585bfbde405:v1"
            ],
            "totalDebt": 31814000000.0,
            "totalDebtFactId": "540240c7a0633e6af181e585bfbde405:v1:total_debt:2025-12-31",
            "unit": "USD"
          }
        ],
        "industry": "RAILROADS",
        "latest": {
          "capitalExpenditure": 3791000000.0,
          "capitalExpenditureFactId": "540240c7a0633e6af181e585bfbde405:v1:capital_expenditure:2025-12-31",
          "freeCashFlow": 5499000000.0,
          "freeCashFlowFactId": "540240c7a0633e6af181e585bfbde405:v1:free_cash_flow:2025-12-31",
          "operatingCashFlow": 9290000000.0,
          "period": "2025-12-31",
          "ratio": 3.4245425188374594,
          "sourceRecordIds": [
            "540240c7a0633e6af181e585bfbde405:v1"
          ],
          "totalDebt": 31814000000.0,
          "totalDebtFactId": "540240c7a0633e6af181e585bfbde405:v1:total_debt:2025-12-31",
          "unit": "USD"
        },
        "level": "high",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "lower_valuation",
      "capital_allocation_deteriorates"
    ]
  },
  "V": {
    "counterDrivers": [],
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
            "capitalExpenditure": 1059000000.0,
            "capitalExpenditureFactId": "1b3dc8edcf91ba403781b043b18eef82:v1:capital_expenditure:2023-09-30",
            "freeCashFlow": 19696000000.0,
            "freeCashFlowFactId": "1b3dc8edcf91ba403781b043b18eef82:v1:free_cash_flow:2023-09-30",
            "operatingCashFlow": 20755000000.0,
            "period": "2023-09-30",
            "ratio": 0.9859311009395326,
            "sourceRecordIds": [
              "1b3dc8edcf91ba403781b043b18eef82:v1"
            ],
            "totalDebt": 20463000000.0,
            "totalDebtFactId": "1b3dc8edcf91ba403781b043b18eef82:v1:total_debt:2023-09-30",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 1257000000.0,
            "capitalExpenditureFactId": "988e043b2fc52684f8cfc87e7292cf5f:v1:capital_expenditure:2024-09-30",
            "freeCashFlow": 18693000000.0,
            "freeCashFlowFactId": "988e043b2fc52684f8cfc87e7292cf5f:v1:free_cash_flow:2024-09-30",
            "operatingCashFlow": 19950000000.0,
            "period": "2024-09-30",
            "ratio": 1.0444110275689222,
            "sourceRecordIds": [
              "988e043b2fc52684f8cfc87e7292cf5f:v1"
            ],
            "totalDebt": 20836000000.0,
            "totalDebtFactId": "988e043b2fc52684f8cfc87e7292cf5f:v1:total_debt:2024-09-30",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 1482000000.0,
            "capitalExpenditureFactId": "8ce2e7bafc90ee105b23c47567fccd5f:v1:capital_expenditure:2025-09-30",
            "freeCashFlow": 21577000000.0,
            "freeCashFlowFactId": "8ce2e7bafc90ee105b23c47567fccd5f:v1:free_cash_flow:2025-09-30",
            "operatingCashFlow": 23059000000.0,
            "period": "2025-09-30",
            "ratio": 1.0915911357821242,
            "sourceRecordIds": [
              "8ce2e7bafc90ee105b23c47567fccd5f:v1"
            ],
            "totalDebt": 25171000000.0,
            "totalDebtFactId": "8ce2e7bafc90ee105b23c47567fccd5f:v1:total_debt:2025-09-30",
            "unit": "USD"
          }
        ],
        "industry": "CREDIT SERVICES",
        "latest": {
          "capitalExpenditure": 1482000000.0,
          "capitalExpenditureFactId": "8ce2e7bafc90ee105b23c47567fccd5f:v1:capital_expenditure:2025-09-30",
          "freeCashFlow": 21577000000.0,
          "freeCashFlowFactId": "8ce2e7bafc90ee105b23c47567fccd5f:v1:free_cash_flow:2025-09-30",
          "operatingCashFlow": 23059000000.0,
          "period": "2025-09-30",
          "ratio": 1.0915911357821242,
          "sourceRecordIds": [
            "8ce2e7bafc90ee105b23c47567fccd5f:v1"
          ],
          "totalDebt": 25171000000.0,
          "totalDebtFactId": "8ce2e7bafc90ee105b23c47567fccd5f:v1:total_debt:2025-09-30",
          "unit": "USD"
        },
        "level": "low",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "valuation_becomes_expensive",
      "capital_allocation_deteriorates"
    ]
  },
  "VST": {
    "counterDrivers": [
      {
        "engine": "financial_risk",
        "kind": "financial_risk_elevated",
        "polarity": "adverse",
        "sourceStatus": "high"
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
    "primaryDrivers": [],
    "recommendationConviction": {
      "analyticalReasons": [],
      "evidentialReasons": [
        "company_fundamentals_evidence_only"
      ],
      "level": "low"
    },
    "riskBasis": {
      "elevatedCategories": [
        "financial_risk"
      ],
      "financialRisk": {
        "bands": {
          "highFrom": 3.0,
          "lowBelow": 1.25
        },
        "condition": "debt_burden_high",
        "excluded": [],
        "gaps": [],
        "history": [
          {
            "capitalExpenditure": 1676000000.0,
            "capitalExpenditureFactId": "dbe1766dac2fe3fb810374d9182556a7:v2:capital_expenditure:2023-12-31",
            "freeCashFlow": 3777000000.0,
            "freeCashFlowFactId": "dbe1766dac2fe3fb810374d9182556a7:v2:free_cash_flow:2023-12-31",
            "operatingCashFlow": 5453000000.0,
            "period": "2023-12-31",
            "ratio": 2.6411149825783973,
            "sourceRecordIds": [
              "dbe1766dac2fe3fb810374d9182556a7:v2"
            ],
            "totalDebt": 14402000000.0,
            "totalDebtFactId": "dbe1766dac2fe3fb810374d9182556a7:v2:total_debt:2023-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 2078000000.0,
            "capitalExpenditureFactId": "6ac828192c0ca9a7dd473731f6b625f5:v2:capital_expenditure:2024-12-31",
            "freeCashFlow": 2485000000.0,
            "freeCashFlowFactId": "6ac828192c0ca9a7dd473731f6b625f5:v2:free_cash_flow:2024-12-31",
            "operatingCashFlow": 4563000000.0,
            "period": "2024-12-31",
            "ratio": 3.571772956388341,
            "sourceRecordIds": [
              "6ac828192c0ca9a7dd473731f6b625f5:v2"
            ],
            "totalDebt": 16298000000.0,
            "totalDebtFactId": "6ac828192c0ca9a7dd473731f6b625f5:v2:total_debt:2024-12-31",
            "unit": "USD"
          },
          {
            "capitalExpenditure": 2752000000.0,
            "capitalExpenditureFactId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:capital_expenditure:2025-12-31",
            "freeCashFlow": 1318000000.0,
            "freeCashFlowFactId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:free_cash_flow:2025-12-31",
            "operatingCashFlow": 4070000000.0,
            "period": "2025-12-31",
            "ratio": 4.187469287469288,
            "sourceRecordIds": [
              "7bbcd2dc44f7748f6ad87212a2eee37a:v2"
            ],
            "totalDebt": 17043000000.0,
            "totalDebtFactId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:total_debt:2025-12-31",
            "unit": "USD"
          }
        ],
        "industry": "UTILITIES - INDEPENDENT POWER PRODUCERS",
        "latest": {
          "capitalExpenditure": 2752000000.0,
          "capitalExpenditureFactId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:capital_expenditure:2025-12-31",
          "freeCashFlow": 1318000000.0,
          "freeCashFlowFactId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:free_cash_flow:2025-12-31",
          "operatingCashFlow": 4070000000.0,
          "period": "2025-12-31",
          "ratio": 4.187469287469288,
          "sourceRecordIds": [
            "7bbcd2dc44f7748f6ad87212a2eee37a:v2"
          ],
          "totalDebt": 17043000000.0,
          "totalDebtFactId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:total_debt:2025-12-31",
          "unit": "USD"
        },
        "level": "high",
        "measure": "gross_debt_to_operating_cash_flow"
      },
      "version": 2
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "valuation_becomes_expensive"
    ]
  }
};

/** Intl separates number and unit with a no-break space; compare as plain text. */
function plain(text: string | null | undefined): string {
  return (text ?? "").replace(/[  ]/g, " ");
}

function fixture(ticker: string): RecommendationReasoningView {
  const reasoning = REAL[ticker];
  if (!reasoning) throw new Error(`no fixture for ${ticker}`);
  return reasoning;
}

function decision(reasoning: RecommendationReasoningView, action: DecisionAction = "reduce"): InvestmentDecisionView {
  return {
    caseId: "case-fixture",
    action,
    qualifiers: [],
    supportingReasons: [],
    blockers: [],
    changeTrigger: null,
    generatedAt: "2026-09-12T00:00:00Z",
    reasoning,
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

function basisLine(view: InvestmentDecisionView): string | undefined {
  return lines(view).find((line) => line.startsWith("Förhöjd finansiell risk:") || line.startsWith("Grund för förhöjd"));
}

/** English, through the real dictionary and the same `{{name}}` interpolation. */
function tEn(key: keyof typeof en, params: Record<string, string | number> = {}): string {
  return Object.entries(params).reduce((s, [k, v]) => s.split("{{" + k + "}}").join(String(v)), en[key] as string);
}
const T = (key: keyof typeof en, params?: Record<string, string | number>) => tEn(key, params);

function withBasis(ticker: string, basis: RiskDriverBasisView | null | undefined): RecommendationReasoningView {
  const { riskBasis: _drop, ...rest } = fixture(ticker);
  return basis === undefined ? rest : { ...rest, riskBasis: basis };
}

const SCOPE_SV =
  "Bedömningen bygger på redovisad skuld och kassaflöde — inte på kreditbetyg, räntekostnader, förfallostruktur eller likviditet.";

describe("VST -- elevated because debt is large relative to operating cash flow", () => {
  it("states the level first, the trend second, directly beneath the against-row", () => {
    const all = lines(decision(fixture("VST")));
    const against = all.indexOf("Talar emot: Förhöjd finansiell risk");
    expect(against).toBeGreaterThanOrEqual(0);
    expect(all[against + 1]).toBe(
      "Förhöjd finansiell risk: total skuld motsvarar 4,2× kassaflödet från rörelsen (2025). " +
        "Skuldbördan har ökat från 2,6× 2023. " +
        SCOPE_SV,
    );
  });

  it("renders the same in English", () => {
    expect(plain(riskBasisLabel(fixture("VST").riskBasis, T, "en-US"))).toBe(
      "Elevated financial risk: total debt is 4.2× the cash generated by operations (2025). " +
        "The debt burden has risen from 2.6× in 2023. " +
        "The assessment reads reported debt and cash flow — not credit ratings, interest costs, debt maturities or liquidity.",
    );
  });

  it("makes no credit, default, liquidity or forecast claim", () => {
    const line = basisLine(decision(fixture("VST"))) ?? "";
    for (const claim of ["kreditrisken är", "konkurs", "betalningsinställ", "likviditeten är", "kommer att", "förväntas"]) {
      expect(line).not.toContain(claim);
    }
  });

  it("leaves every other row exactly as it was", () => {
    const all = lines(decision(fixture("VST")));
    expect(all).toContain("Talar för: Inget i underlaget talar tydligt för.");
    expect(all).toContain("Vad skulle ändra bilden: Lägre risk · Om värderingen blir hög");
  });
});

describe("other real Cases", () => {
  it("META: rising but small debt is not elevated, and stays quiet", () => {
    const all = lines(decision(fixture("META"), "hold"));
    expect(all.join("\n")).not.toMatch(/Förhöjd finansiell risk|Grund för/);
    expect(all[1]).toMatch(/^Talar för: Ingen förhöjd finansiell risk/);
  });

  it("INTC: burden, not the free-cash-flow sign", () => {
    expect(basisLine(decision(fixture("INTC"), "no_decision"))).toBe(
      "Förhöjd finansiell risk: total skuld motsvarar 4,8× kassaflödet från rörelsen (2025). " +
        "Skuldbördan har ökat från 4,3× 2023. " +
        SCOPE_SV,
    );
  });

  it("UNP: a falling burden reads as falling, the level still high", () => {
    expect(basisLine(decision(fixture("UNP"), "no_decision"))).toContain(
      "total skuld motsvarar 3,4× kassaflödet från rörelsen (2025). Skuldbördan har minskat från 3,9× 2023.",
    );
  });

  it("CAT: high burden and high valuation risk are both stated", () => {
    const line = basisLine(decision(fixture("CAT"), "no_decision")) ?? "";
    expect(line).toContain("3,1× kassaflödet från rörelsen (2025)");
    expect(line).toContain("Värderingsrisken bedöms också som hög.");
  });

  it("GOOGL: raised by valuation alone -- no financial explanation is borrowed", () => {
    expect(basisLine(decision(fixture("GOOGL"), "no_decision"))).toBe(
      "Grund för förhöjd finansiell risk: värderingsrisken bedöms som hög — värderingen är hög jämfört med bolagets egen historik. " +
        "Den finansiella risken i sig: låg.",
    );
  });

  it("SHOP: raised by valuation while financial risk could not be assessed -- says so", () => {
    expect(basisLine(decision(fixture("SHOP"), "no_decision"))).toContain("Den finansiella risken i sig: kunde inte bedömas.");
  });

  it("GS: not applicable is one quiet line, never a reassurance and never a warning", () => {
    const all = lines(decision(fixture("GS"), "no_decision"));
    expect(all).toContain(
      "Finansiell risk: Atlas generella mått för skuld och kassaflöde används inte för banker, försäkringsbolag och värdepappersföretag.",
    );
    expect(all.join("\n")).not.toMatch(/Ingen förhöjd finansiell risk|Förhöjd finansiell risk|Underlag saknas: finansiell risk/);
  });

  it("AVGO: insufficient evidence is an unknown, never a reassurance", () => {
    const all = lines(decision(fixture("AVGO"), "hold")).join("\n");
    expect(all).not.toContain("Ingen förhöjd finansiell risk");
    expect(all).toContain("Underlag saknas: finansiell risk");
  });

  it("V: a rising burden inside the low band stays quiet", () => {
    const all = lines(decision(fixture("V"), "no_decision")).join("\n");
    expect(all).not.toMatch(/Förhöjd finansiell risk|Skuldbördan/);
  });
});

describe("absence, versions and edge states", () => {
  it("a legacy row without a basis renders the card exactly as before", () => {
    const all = lines(decision(withBasis("VST", undefined)));
    expect(all).toContain("Talar emot: Förhöjd finansiell risk");
    expect(basisLine(decision(withBasis("VST", undefined)))).toBeUndefined();
  });

  it("a basis of another version is never read", () => {
    const v1 = { ...(fixture("VST").riskBasis as RiskDriverBasisView), version: 1 };
    expect(basisLine(decision(withBasis("VST", v1)))).toBeUndefined();
    const unversioned = { ...(fixture("VST").riskBasis as RiskDriverBasisView) } as Partial<RiskDriverBasisView>;
    delete unversioned.version;
    expect(riskBasisLabel(unversioned as RiskDriverBasisView, T, "en-US")).toBeNull();
  });

  it("a basis never appears without the driver it explains", () => {
    expect(basisLine(decision(withBasis("META", fixture("VST").riskBasis), "hold"))).toBeUndefined();
  });

  it("operations that consumed cash are named as exactly that", () => {
    const vst = fixture("VST").riskBasis as RiskDriverBasisView;
    const latest = { ...vst.financialRisk.latest!, freeCashFlow: -5e9, capitalExpenditure: 1e9, operatingCashFlow: -4e9, ratio: null };
    const burned: RiskDriverBasisView = {
      ...vst,
      financialRisk: { ...vst.financialRisk, condition: "operating_cash_flow_negative", latest, history: [latest] },
    };
    expect(plain(riskBasisLabel(burned, T, "en-US"))).toBe(
      "Elevated financial risk: cash flow from operations was negative (2025: -$4.0B) — operations consumed cash. " +
        "The assessment reads reported debt and cash flow — not credit ratings, interest costs, debt maturities or liquidity.",
    );
  });

  it("zero operating cash flow is stated without a ratio", () => {
    const vst = fixture("VST").riskBasis as RiskDriverBasisView;
    const latest = { ...vst.financialRisk.latest!, operatingCashFlow: 0, ratio: null };
    const zero: RiskDriverBasisView = {
      ...vst,
      financialRisk: { ...vst.financialRisk, condition: "operating_cash_flow_zero", latest, history: [latest] },
    };
    expect(plain(riskBasisLabel(zero, T, "en-US"))).toContain("operations generated no cash (2025).");
  });

  it("formats multiples and amounts in the reader's language", () => {
    expect(formatMultiple(4.19, "sv-SE")).toBe("4,2×");
    expect(formatMultiple(4.19, "en-US")).toBe("4.2×");
    expect(plain(formatReportedAmount(17_043_000_000, "USD", "sv-SE"))).toBe("17,0 md US$");
    expect(plain(formatReportedAmount(300_000_000_000, "unspecified", "en-US"))).toBe("300.0B");
  });
});
