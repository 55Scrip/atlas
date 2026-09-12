import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { en } from "../i18n/translations/en";
import { AtlasInvestmentReasoning } from "./AtlasInvestmentReasoning";
import { formatReportedAmount, riskBasisLabel } from "./describeRecommendationReasoning";
import type { DecisionAction, InvestmentDecisionView } from "./investmentDecisionApi";
import type { RecommendationReasoningView, RiskDriverBasisView } from "./reasoningContract";

/**
 * Financial-risk basis in the reasoning card. The reasoning payloads below
 * are the real `/investment-decision` reasoning for each ticker, captured
 * from a copy of the live database (signal summary and forward context
 * omitted) -- fixture data, not rules: nothing in the card knows a ticker.
 */
const REAL: Record<string, RecommendationReasoningView> = {
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
        "determining": [
          "capital_allocation",
          "cash_generation"
        ],
        "level": "low",
        "rule": "core_signals_both_low",
        "signals": [
          {
            "condition": "capital_allocation_strong",
            "level": "low",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_not_negative",
            "level": "low",
            "observations": [
              {
                "factId": "397c8c85fc7ce7cb60564022e7be0a70:v2:free_cash_flow:2025-12-31",
                "metric": "free_cash_flow",
                "period": "2025-12-31",
                "sourceRecordId": "397c8c85fc7ce7cb60564022e7be0a70:v2",
                "unit": "USD",
                "value": 73266000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_no_consistent_direction",
            "level": "insufficient_input",
            "observations": [
              {
                "factId": "8ac50c2ffbeef541c181f5a9876d5748:v2:total_debt:2015-12-31",
                "metric": "total_debt",
                "period": "2015-12-31",
                "sourceRecordId": "8ac50c2ffbeef541c181f5a9876d5748:v2",
                "unit": "USD",
                "value": 3225000000.0
              },
              {
                "factId": "68ee4551f87a5237fecf664bde24a7da:v2:total_debt:2016-12-31",
                "metric": "total_debt",
                "period": "2016-12-31",
                "sourceRecordId": "68ee4551f87a5237fecf664bde24a7da:v2",
                "unit": "USD",
                "value": 4000000000.0
              },
              {
                "factId": "f6f95fad78dfef472c932eec64f3790a:v2:total_debt:2017-12-31",
                "metric": "total_debt",
                "period": "2017-12-31",
                "sourceRecordId": "f6f95fad78dfef472c932eec64f3790a:v2",
                "unit": "USD",
                "value": 4026000000.0
              },
              {
                "factId": "d4c414fd35e97d852aef78338e90e8eb:v2:total_debt:2018-12-31",
                "metric": "total_debt",
                "period": "2018-12-31",
                "sourceRecordId": "d4c414fd35e97d852aef78338e90e8eb:v2",
                "unit": "USD",
                "value": 4062000000.0
              },
              {
                "factId": "366a4570e1195d6acb5019917d93664f:v2:total_debt:2019-12-31",
                "metric": "total_debt",
                "period": "2019-12-31",
                "sourceRecordId": "366a4570e1195d6acb5019917d93664f:v2",
                "unit": "USD",
                "value": 3958000000.0
              },
              {
                "factId": "9d8e701f8c3a71aba963ff8948762ee4:v2:total_debt:2020-12-31",
                "metric": "total_debt",
                "period": "2020-12-31",
                "sourceRecordId": "9d8e701f8c3a71aba963ff8948762ee4:v2",
                "unit": "USD",
                "value": 15319000000.0
              },
              {
                "factId": "6337a9f88308c0e2cfb6679a9ef37d35:v2:total_debt:2021-12-31",
                "metric": "total_debt",
                "period": "2021-12-31",
                "sourceRecordId": "6337a9f88308c0e2cfb6679a9ef37d35:v2",
                "unit": "USD",
                "value": 15440000000.0
              },
              {
                "factId": "6c30264588597c1ec60b034fdc81fca3:v2:total_debt:2022-12-31",
                "metric": "total_debt",
                "period": "2022-12-31",
                "sourceRecordId": "6c30264588597c1ec60b034fdc81fca3:v2",
                "unit": "USD",
                "value": 15312000000.0
              },
              {
                "factId": "1e3e75c8fc74a5d21570a2e377aedef8:v2:total_debt:2023-12-31",
                "metric": "total_debt",
                "period": "2023-12-31",
                "sourceRecordId": "1e3e75c8fc74a5d21570a2e377aedef8:v2",
                "unit": "USD",
                "value": 12870000000.0
              },
              {
                "factId": "dfc34251a9e976ee41327d34ebf46b25:v2:total_debt:2024-12-31",
                "metric": "total_debt",
                "period": "2024-12-31",
                "sourceRecordId": "dfc34251a9e976ee41327d34ebf46b25:v2",
                "unit": "USD",
                "value": 11882000000.0
              },
              {
                "factId": "397c8c85fc7ce7cb60564022e7be0a70:v2:total_debt:2025-12-31",
                "metric": "total_debt",
                "period": "2025-12-31",
                "sourceRecordId": "397c8c85fc7ce7cb60564022e7be0a70:v2",
                "unit": "USD",
                "value": 48543000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
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
        "determining": [
          "cash_generation"
        ],
        "level": "high",
        "rule": "any_signal_high",
        "signals": [
          {
            "condition": "capital_allocation_moderate",
            "level": "moderate",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_negative",
            "level": "high",
            "observations": [
              {
                "factId": "0fc0e6c19545c1fbde916c2d9caa4feb:v1:free_cash_flow:2025-12-31",
                "metric": "free_cash_flow",
                "period": "2025-12-31",
                "sourceRecordId": "0fc0e6c19545c1fbde916c2d9caa4feb:v1",
                "unit": "USD",
                "value": -47218000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_no_consistent_direction",
            "level": "insufficient_input",
            "observations": [
              {
                "factId": "f38d1e152196dee1047f8c06ce55df43:v1:total_debt:2010-12-31",
                "metric": "total_debt",
                "period": "2010-12-31",
                "sourceRecordId": "f38d1e152196dee1047f8c06ce55df43:v1",
                "unit": "USD",
                "value": 260618000000.0
              },
              {
                "factId": "73d9bdc4eeec24b9906f9c6909a50823:v4:total_debt:2011-12-31",
                "metric": "total_debt",
                "period": "2011-12-31",
                "sourceRecordId": "73d9bdc4eeec24b9906f9c6909a50823:v4",
                "unit": "USD",
                "value": 259947000000.0
              },
              {
                "factId": "f5495a7e2c344169832c4d03516d2be9:v1:total_debt:2014-12-31",
                "metric": "total_debt",
                "period": "2014-12-31",
                "sourceRecordId": "f5495a7e2c344169832c4d03516d2be9:v1",
                "unit": "USD",
                "value": 234650000000.0
              },
              {
                "factId": "fc8dbe57356e4082cb9d083d0a44d8bd:v1:total_debt:2015-12-31",
                "metric": "total_debt",
                "period": "2015-12-31",
                "sourceRecordId": "fc8dbe57356e4082cb9d083d0a44d8bd:v1",
                "unit": "USD",
                "value": 242962000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
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
        "determining": [
          "capital_allocation",
          "cash_generation"
        ],
        "level": "high",
        "rule": "any_signal_high",
        "signals": [
          {
            "condition": "capital_allocation_weak",
            "level": "high",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_negative",
            "level": "high",
            "observations": [
              {
                "factId": "3a877697c6ebf96e23eef5f909d399d8:v1:free_cash_flow:2025-12-27",
                "metric": "free_cash_flow",
                "period": "2025-12-27",
                "sourceRecordId": "3a877697c6ebf96e23eef5f909d399d8:v1",
                "unit": "USD",
                "value": -4949000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_no_consistent_direction",
            "level": "insufficient_input",
            "observations": [
              {
                "factId": "6ab2191f108366560c43012a2a6a5013:v1:total_debt:2009-12-26",
                "metric": "total_debt",
                "period": "2009-12-26",
                "sourceRecordId": "6ab2191f108366560c43012a2a6a5013:v1",
                "unit": "USD",
                "value": 2206000000.0
              },
              {
                "factId": "102d604915fcbd74914888b417924ce8:v1:total_debt:2013-12-28",
                "metric": "total_debt",
                "period": "2013-12-28",
                "sourceRecordId": "102d604915fcbd74914888b417924ce8:v1",
                "unit": "USD",
                "value": 13165000000.0
              },
              {
                "factId": "08e09cc3e239ed1d140853a4e3ad4ae6:v1:total_debt:2014-12-27",
                "metric": "total_debt",
                "period": "2014-12-27",
                "sourceRecordId": "08e09cc3e239ed1d140853a4e3ad4ae6:v1",
                "unit": "USD",
                "value": 13147000000.0
              },
              {
                "factId": "b09bcafa022923c347306f097e795626:v1:total_debt:2015-12-26",
                "metric": "total_debt",
                "period": "2015-12-26",
                "sourceRecordId": "b09bcafa022923c347306f097e795626:v1",
                "unit": "USD",
                "value": 22638000000.0
              },
              {
                "factId": "bdce15a429a82af10351f1b649c845c0:v1:total_debt:2016-12-31",
                "metric": "total_debt",
                "period": "2016-12-31",
                "sourceRecordId": "bdce15a429a82af10351f1b649c845c0:v1",
                "unit": "USD",
                "value": 25258000000.0
              },
              {
                "factId": "385e66d77c0ecee8dfb481675a891728:v1:total_debt:2017-12-30",
                "metric": "total_debt",
                "period": "2017-12-30",
                "sourceRecordId": "385e66d77c0ecee8dfb481675a891728:v1",
                "unit": "USD",
                "value": 26776000000.0
              },
              {
                "factId": "d9f05af437f6d1f2599543f1749d0baf:v1:total_debt:2018-12-29",
                "metric": "total_debt",
                "period": "2018-12-29",
                "sourceRecordId": "d9f05af437f6d1f2599543f1749d0baf:v1",
                "unit": "USD",
                "value": 25859000000.0
              },
              {
                "factId": "c75892fc8dd0ee81886b90a242559105:v1:total_debt:2019-12-28",
                "metric": "total_debt",
                "period": "2019-12-28",
                "sourceRecordId": "c75892fc8dd0ee81886b90a242559105:v1",
                "unit": "USD",
                "value": 29003000000.0
              },
              {
                "factId": "208ae51f5c3c178c8b00e333eb26fbf1:v1:total_debt:2020-12-26",
                "metric": "total_debt",
                "period": "2020-12-26",
                "sourceRecordId": "208ae51f5c3c178c8b00e333eb26fbf1:v1",
                "unit": "USD",
                "value": 36401000000.0
              },
              {
                "factId": "7598c8b6e456052b2bf7e644d76af637:v1:total_debt:2021-12-25",
                "metric": "total_debt",
                "period": "2021-12-25",
                "sourceRecordId": "7598c8b6e456052b2bf7e644d76af637:v1",
                "unit": "USD",
                "value": 38101000000.0
              },
              {
                "factId": "6f1add2d411b2bdeb47051f08e79adcb:v1:total_debt:2022-12-31",
                "metric": "total_debt",
                "period": "2022-12-31",
                "sourceRecordId": "6f1add2d411b2bdeb47051f08e79adcb:v1",
                "unit": "USD",
                "value": 38107000000.0
              },
              {
                "factId": "afde05a950d82a660f3b104d1146ee40:v1:total_debt:2023-12-30",
                "metric": "total_debt",
                "period": "2023-12-30",
                "sourceRecordId": "afde05a950d82a660f3b104d1146ee40:v1",
                "unit": "USD",
                "value": 49266000000.0
              },
              {
                "factId": "a5d77843e6be3b6e8a1567a52ff8922a:v1:total_debt:2024-12-28",
                "metric": "total_debt",
                "period": "2024-12-28",
                "sourceRecordId": "a5d77843e6be3b6e8a1567a52ff8922a:v1",
                "unit": "USD",
                "value": 50011000000.0
              },
              {
                "factId": "3a877697c6ebf96e23eef5f909d399d8:v1:total_debt:2025-12-27",
                "metric": "total_debt",
                "period": "2025-12-27",
                "sourceRecordId": "3a877697c6ebf96e23eef5f909d399d8:v1",
                "unit": "USD",
                "value": 46585000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "improved_capital_allocation_evidence"
    ]
  },
  "MA": {
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
        "determining": [
          "capital_allocation",
          "cash_generation"
        ],
        "level": "low",
        "rule": "core_signals_both_low",
        "signals": [
          {
            "condition": "capital_allocation_strong",
            "level": "low",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_not_negative",
            "level": "low",
            "observations": [
              {
                "factId": "84cffbe868a9f4d0183f0db5290a7ecc:v2:free_cash_flow:2025-12-31",
                "metric": "free_cash_flow",
                "period": "2025-12-31",
                "sourceRecordId": "84cffbe868a9f4d0183f0db5290a7ecc:v2",
                "unit": "USD",
                "value": 17159000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_no_consistent_direction",
            "level": "insufficient_input",
            "observations": [
              {
                "factId": "7e9754e2f2cbda6d40b057b8a179f3b3:v2:total_debt:2008-12-31",
                "metric": "total_debt",
                "period": "2008-12-31",
                "sourceRecordId": "7e9754e2f2cbda6d40b057b8a179f3b3:v2",
                "unit": "USD",
                "value": 168767000.0
              },
              {
                "factId": "afb8d9b2bb567a040b9cb46a9c8f77c0:v2:total_debt:2009-12-31",
                "metric": "total_debt",
                "period": "2009-12-31",
                "sourceRecordId": "afb8d9b2bb567a040b9cb46a9c8f77c0:v2",
                "unit": "USD",
                "value": 22000000.0
              },
              {
                "factId": "2ca9928e19b5b3177972d765aa9ad191:v2:total_debt:2017-12-31",
                "metric": "total_debt",
                "period": "2017-12-31",
                "sourceRecordId": "2ca9928e19b5b3177972d765aa9ad191:v2",
                "unit": "USD",
                "value": 5424000000.0
              },
              {
                "factId": "0ee2f65f55b4cb48eee4cea4c6788e07:v2:total_debt:2018-12-31",
                "metric": "total_debt",
                "period": "2018-12-31",
                "sourceRecordId": "0ee2f65f55b4cb48eee4cea4c6788e07:v2",
                "unit": "USD",
                "value": 6334000000.0
              },
              {
                "factId": "b05da9b654ad5d80b8eaec7e1f00301e:v2:total_debt:2019-12-31",
                "metric": "total_debt",
                "period": "2019-12-31",
                "sourceRecordId": "b05da9b654ad5d80b8eaec7e1f00301e:v2",
                "unit": "USD",
                "value": 8527000000.0
              },
              {
                "factId": "1e982e085fffc97e34d969c591e80702:v2:total_debt:2020-12-31",
                "metric": "total_debt",
                "period": "2020-12-31",
                "sourceRecordId": "1e982e085fffc97e34d969c591e80702:v2",
                "unit": "USD",
                "value": 12672000000.0
              },
              {
                "factId": "90238dc03e54e59282ecbbeabb1d5c45:v2:total_debt:2021-12-31",
                "metric": "total_debt",
                "period": "2021-12-31",
                "sourceRecordId": "90238dc03e54e59282ecbbeabb1d5c45:v2",
                "unit": "USD",
                "value": 13901000000.0
              },
              {
                "factId": "e8fd09c634da7009495fba9d5e9b9f31:v2:total_debt:2022-12-31",
                "metric": "total_debt",
                "period": "2022-12-31",
                "sourceRecordId": "e8fd09c634da7009495fba9d5e9b9f31:v2",
                "unit": "USD",
                "value": 14023000000.0
              },
              {
                "factId": "2f23565189e64272453e1396fb1d1ee5:v2:total_debt:2023-12-31",
                "metric": "total_debt",
                "period": "2023-12-31",
                "sourceRecordId": "2f23565189e64272453e1396fb1d1ee5:v2",
                "unit": "USD",
                "value": 15681000000.0
              },
              {
                "factId": "31e2dc6ee8f74719c69759b4d19146be:v2:total_debt:2024-12-31",
                "metric": "total_debt",
                "period": "2024-12-31",
                "sourceRecordId": "31e2dc6ee8f74719c69759b4d19146be:v2",
                "unit": "USD",
                "value": 18226000000.0
              },
              {
                "factId": "84cffbe868a9f4d0183f0db5290a7ecc:v2:total_debt:2025-12-31",
                "metric": "total_debt",
                "period": "2025-12-31",
                "sourceRecordId": "84cffbe868a9f4d0183f0db5290a7ecc:v2",
                "unit": "USD",
                "value": 19000000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "financial_risk_becomes_elevated",
      "valuation_becomes_expensive",
      "capital_allocation_deteriorates"
    ]
  },
  "META": {
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
        "determining": [
          "debt_trend"
        ],
        "level": "high",
        "rule": "any_signal_high",
        "signals": [
          {
            "condition": "capital_allocation_moderate",
            "level": "moderate",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_not_negative",
            "level": "low",
            "observations": [
              {
                "factId": "2adddd1608791c901ab7a4e838d554bb:v1:free_cash_flow:2025-12-31",
                "metric": "free_cash_flow",
                "period": "2025-12-31",
                "sourceRecordId": "2adddd1608791c901ab7a4e838d554bb:v1",
                "unit": "USD",
                "value": 46109000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_increased_every_period",
            "level": "high",
            "observations": [
              {
                "factId": "25532794e6627fd0a6a08d6aa89c0ede:v1:total_debt:2022-12-31",
                "metric": "total_debt",
                "period": "2022-12-31",
                "sourceRecordId": "25532794e6627fd0a6a08d6aa89c0ede:v1",
                "unit": "USD",
                "value": 9923000000.0
              },
              {
                "factId": "8c8afbd05ec3a4bed7965883ac4a3db4:v1:total_debt:2023-12-31",
                "metric": "total_debt",
                "period": "2023-12-31",
                "sourceRecordId": "8c8afbd05ec3a4bed7965883ac4a3db4:v1",
                "unit": "USD",
                "value": 18385000000.0
              },
              {
                "factId": "1435a46fdaf8206586c9749add8ccdbc:v1:total_debt:2024-12-31",
                "metric": "total_debt",
                "period": "2024-12-31",
                "sourceRecordId": "1435a46fdaf8206586c9749add8ccdbc:v1",
                "unit": "USD",
                "value": 28826000000.0
              },
              {
                "factId": "2adddd1608791c901ab7a4e838d554bb:v1:total_debt:2025-12-31",
                "metric": "total_debt",
                "period": "2025-12-31",
                "sourceRecordId": "2adddd1608791c901ab7a4e838d554bb:v1",
                "unit": "USD",
                "value": 58744000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "valuation_becomes_expensive"
    ]
  },
  "MU": {
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
    "recommendationConviction": null,
    "riskBasis": {
      "elevatedCategories": [],
      "financialRisk": {
        "determining": [
          "capital_allocation"
        ],
        "level": "moderate",
        "rule": "core_signal_not_low",
        "signals": [
          {
            "condition": "capital_allocation_moderate",
            "level": "moderate",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_not_negative",
            "level": "low",
            "observations": [
              {
                "factId": "6918ad0b671aa39054936b1cbf5e5b2f:v1:free_cash_flow:2025-08-28",
                "metric": "free_cash_flow",
                "period": "2025-08-28",
                "sourceRecordId": "6918ad0b671aa39054936b1cbf5e5b2f:v1",
                "unit": "USD",
                "value": 1668000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_no_consistent_direction",
            "level": "insufficient_input",
            "observations": [
              {
                "factId": "26921f1c8715238eb8e745b8961ca65f:v1:total_debt:2010-09-02",
                "metric": "total_debt",
                "period": "2010-09-02",
                "sourceRecordId": "26921f1c8715238eb8e745b8961ca65f:v1",
                "unit": "USD",
                "value": 2360000000.0
              },
              {
                "factId": "287c607389d3e99995122d2cbd759372:v1:total_debt:2011-09-01",
                "metric": "total_debt",
                "period": "2011-09-01",
                "sourceRecordId": "287c607389d3e99995122d2cbd759372:v1",
                "unit": "USD",
                "value": 2001000000.0
              },
              {
                "factId": "9bd3dd69d9e6ac16f62ddc5818770a66:v1:total_debt:2012-08-30",
                "metric": "total_debt",
                "period": "2012-08-30",
                "sourceRecordId": "9bd3dd69d9e6ac16f62ddc5818770a66:v1",
                "unit": "USD",
                "value": 3262000000.0
              },
              {
                "factId": "abfa9b8a34c12f4210a5258fd4c1cdf4:v1:total_debt:2020-09-03",
                "metric": "total_debt",
                "period": "2020-09-03",
                "sourceRecordId": "abfa9b8a34c12f4210a5258fd4c1cdf4:v1",
                "unit": "USD",
                "value": 6157000000.0
              },
              {
                "factId": "23ba157bb3b9432cf8e382005907919f:v1:total_debt:2021-09-02",
                "metric": "total_debt",
                "period": "2021-09-02",
                "sourceRecordId": "23ba157bb3b9432cf8e382005907919f:v1",
                "unit": "USD",
                "value": 5968000000.0
              },
              {
                "factId": "986c97eafb0dffe72ccc26448d32165c:v1:total_debt:2022-09-01",
                "metric": "total_debt",
                "period": "2022-09-01",
                "sourceRecordId": "986c97eafb0dffe72ccc26448d32165c:v1",
                "unit": "USD",
                "value": 6020000000.0
              },
              {
                "factId": "5a84e023262e65a4a37caa3bde2d0c0f:v1:total_debt:2023-08-31",
                "metric": "total_debt",
                "period": "2023-08-31",
                "sourceRecordId": "5a84e023262e65a4a37caa3bde2d0c0f:v1",
                "unit": "USD",
                "value": 12049000000.0
              },
              {
                "factId": "5ce1d159f8bf989667cb896d9d1540b7:v1:total_debt:2024-08-29",
                "metric": "total_debt",
                "period": "2024-08-29",
                "sourceRecordId": "5ce1d159f8bf989667cb896d9d1540b7:v1",
                "unit": "USD",
                "value": 11343000000.0
              },
              {
                "factId": "6918ad0b671aa39054936b1cbf5e5b2f:v1:total_debt:2025-08-28",
                "metric": "total_debt",
                "period": "2025-08-28",
                "sourceRecordId": "6918ad0b671aa39054936b1cbf5e5b2f:v1",
                "unit": "USD",
                "value": 11533000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
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
        "determining": [
          "capital_allocation"
        ],
        "level": "moderate",
        "rule": "core_signal_not_low",
        "signals": [
          {
            "condition": "capital_allocation_moderate",
            "level": "moderate",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_not_negative",
            "level": "low",
            "observations": [
              {
                "factId": "ac98e736bb57a9697407d312adc24ece:v1:free_cash_flow:2025-12-31",
                "metric": "free_cash_flow",
                "period": "2025-12-31",
                "sourceRecordId": "ac98e736bb57a9697407d312adc24ece:v1",
                "unit": "USD",
                "value": 2007000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_fewer_than_two_periods",
            "level": "insufficient_input",
            "observations": [],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
    },
    "schemaVersion": 1,
    "signalSummary": [],
    "whatWouldChange": [
      "reduced_risk",
      "lower_valuation",
      "growth_deteriorates"
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
        "determining": [
          "debt_trend"
        ],
        "level": "high",
        "rule": "any_signal_high",
        "signals": [
          {
            "condition": "capital_allocation_moderate",
            "level": "moderate",
            "observations": [],
            "signal": "capital_allocation",
            "sourceFindingId": "business_finding:capital_allocation"
          },
          {
            "condition": "latest_free_cash_flow_not_negative",
            "level": "low",
            "observations": [
              {
                "factId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:free_cash_flow:2025-12-31",
                "metric": "free_cash_flow",
                "period": "2025-12-31",
                "sourceRecordId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2",
                "unit": "USD",
                "value": 1318000000.0
              }
            ],
            "signal": "cash_generation",
            "sourceFindingId": null
          },
          {
            "condition": "total_debt_increased_every_period",
            "level": "high",
            "observations": [
              {
                "factId": "dbe1766dac2fe3fb810374d9182556a7:v2:total_debt:2023-12-31",
                "metric": "total_debt",
                "period": "2023-12-31",
                "sourceRecordId": "dbe1766dac2fe3fb810374d9182556a7:v2",
                "unit": "USD",
                "value": 14402000000.0
              },
              {
                "factId": "6ac828192c0ca9a7dd473731f6b625f5:v2:total_debt:2024-12-31",
                "metric": "total_debt",
                "period": "2024-12-31",
                "sourceRecordId": "6ac828192c0ca9a7dd473731f6b625f5:v2",
                "unit": "USD",
                "value": 16298000000.0
              },
              {
                "factId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2:total_debt:2025-12-31",
                "metric": "total_debt",
                "period": "2025-12-31",
                "sourceRecordId": "7bbcd2dc44f7748f6ad87212a2eee37a:v2",
                "unit": "USD",
                "value": 17043000000.0
              }
            ],
            "signal": "debt_trend",
            "sourceFindingId": null
          }
        ]
      }
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
  return (text ?? "").replace(/[\u00a0\u202f]/g, " ");
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
  return lines(view).find((line) => line.startsWith("Grund för förhöjd finansiell risk"));
}

/** English, through the real dictionary and the same `{{name}}` interpolation. */
function tEn(key: keyof typeof en, params: Record<string, string | number> = {}): string {
  return Object.entries(params).reduce((s, [k, v]) => s.split("{{" + k + "}}").join(String(v)), en[key] as string);
}

function withBasis(ticker: string, basis: RiskDriverBasisView | null | undefined): RecommendationReasoningView {
  const { riskBasis: _drop, ...rest } = fixture(ticker);
  return basis === undefined ? rest : { ...rest, riskBasis: basis };
}

describe("VST -- elevated financial risk resting on total debt alone", () => {
  it("explains the existing against-row directly beneath it, with every evaluated period", () => {
    const all = lines(decision(fixture("VST")));
    const against = all.findIndex((line) => line === "Talar emot: Förhöjd finansiell risk");
    expect(against).toBeGreaterThanOrEqual(0);
    expect(all[against + 1]).toBe(
      "Grund för förhöjd finansiell risk: total skuld ökade från varje utvärderad period till nästa " +
        "(2023: 14,4 md US$ → 2024: 16,3 md US$ → 2025: 17,0 md US$). " +
        "Bedömningen bygger på redovisade historiska belopp — inte på skuldsättningsgrad, räntetäckning, likviditet eller kreditbetyg.",
    );
  });

  it("names only the signal that fired -- positive free cash flow and moderate capital allocation are not causes", () => {
    const line = basisLine(decision(fixture("VST"))) ?? "";
    expect(line).not.toMatch(/kassaflöde|kapitalallokering/);
  });

  it("reads as history, never as a forecast or a credit judgment", () => {
    const line = basisLine(decision(fixture("VST"))) ?? "";
    for (const word of ["ökar", "kommer", "förväntas", "belåningen är", "kreditrisk är", "hög skuldsättning"]) {
      expect(line).not.toContain(word);
    }
  });

  it("leaves every existing row exactly as it was", () => {
    const all = lines(decision(fixture("VST")));
    expect(all).toContain("Talar för: Inget i underlaget talar tydligt för.");
    expect(all).toContain("Talar emot: Förhöjd finansiell risk");
    expect(all).toContain("Vad skulle ändra bilden: Lägre risk · Om värderingen blir hög");
  });

  it("renders the same figures in English", () => {
    const t = (key: keyof typeof en, params?: Record<string, string | number>) => tEn(key, params);
    expect(plain(riskBasisLabel(fixture("VST").riskBasis, t, "en-US"))).toBe(
      "Basis for elevated financial risk: total debt rose from each evaluated period to the next " +
        "(2023: $14.4B → 2024: $16.3B → 2025: $17.0B). The assessment reads reported historical amounts — not leverage ratios, interest coverage, liquidity or credit ratings.",
    );
  });

  it("shows the basis on a withheld outcome too, beneath the relabelled row", () => {
    const all = lines(decision(fixture("VST"), "no_decision"));
    const against = all.findIndex((line) => line === "Underlaget talar emot: Förhöjd finansiell risk");
    expect(all[against + 1]).toMatch(/^Grund för förhöjd finansiell risk: total skuld ökade/);
  });
});

describe("other real Cases", () => {
  it("META: the same rule over four periods, every period shown", () => {
    expect(basisLine(decision(fixture("META")))).toContain(
      "(2022: 9,9 md US$ → 2023: 18,4 md US$ → 2024: 28,8 md US$ → 2025: 58,7 md US$)",
    );
  });

  it("INTC: two firing signals, each kept, in the evaluator's order, none netted", () => {
    expect(basisLine(decision(fixture("INTC"), "no_decision"))).toContain(
      "Grund för förhöjd finansiell risk: kapitalallokeringen bedöms som svag; " +
        "det senaste fria kassaflödet var negativt (2025: −4,9 md US$).",
    );
  });

  it("GS: negative free cash flow is the whole basis", () => {
    const line = basisLine(decision(fixture("GS"), "no_decision")) ?? "";
    expect(line).toContain("det senaste fria kassaflödet var negativt (2025: −47,2 md US$)");
    expect(line).not.toContain("skuld ökade");
  });

  it("GOOGL: raised by valuation risk alone -- no financial basis is invented", () => {
    const line = basisLine(decision(fixture("GOOGL"), "no_decision")) ?? "";
    expect(line).toBe(
      "Grund för förhöjd finansiell risk: värderingsrisken bedöms som hög — värderingen är hög jämfört med bolagets egen historik. " +
        "Den finansiella risken i sig bedöms som låg.",
    );
    expect(line).not.toMatch(/skuld|kassaflöde|kapitalallokering/);
  });

  it("SHOP: raised by valuation risk while financial risk is moderate -- says moderate", () => {
    expect(basisLine(decision(fixture("SHOP"), "no_decision"))).toContain("Den finansiella risken i sig bedöms som måttlig.");
  });

  it("MA (low) and MU (moderate): not elevated, so the card stays quiet", () => {
    for (const ticker of ["MA", "MU"]) {
      const all = lines(decision(fixture(ticker), ticker === "MU" ? "no_decision" : "hold"));
      expect(all.join("\n")).not.toContain("Grund för");
    }
  });
});

describe("absence and inconsistency", () => {
  it("a legacy row without a basis renders the card exactly as before", () => {
    const all = lines(decision(withBasis("VST", undefined)));
    expect(all).toContain("Talar emot: Förhöjd finansiell risk");
    expect(all.join("\n")).not.toContain("Grund för");
  });

  it("a null basis renders nothing", () => {
    expect(basisLine(decision(withBasis("VST", null)))).toBeUndefined();
  });

  it("a basis never appears without the driver it explains", () => {
    const vst = fixture("VST");
    const reasoning = { ...withBasis("MA", vst.riskBasis) };
    expect(basisLine(decision(reasoning, "hold"))).toBeUndefined();
  });

  it("a basis whose determining signal did not fire is not rendered as a cause", () => {
    const vst = fixture("VST").riskBasis as RiskDriverBasisView;
    const tampered: RiskDriverBasisView = {
      ...vst,
      financialRisk: { ...vst.financialRisk, determining: ["cash_generation"] },
    };
    expect(basisLine(decision(withBasis("VST", tampered)))).toBeUndefined();
  });
});

describe("reported amounts", () => {
  it("uses the fact's own unit and never guesses a currency", () => {
    expect(plain(formatReportedAmount(14_402_000_000, "USD", "sv-SE"))).toBe("14,4 md US$");
    expect(plain(formatReportedAmount(14_402_000_000, "USD", "en-US"))).toBe("$14.4B");
    expect(plain(formatReportedAmount(300_000_000_000, "unspecified", "en-US"))).toBe("300.0B");
    expect(plain(formatReportedAmount(2_500_000, "MWh", "en-US"))).toBe("2.5M MWh");
  });

  it("falls back to full period-end dates when a year would be ambiguous", () => {
    const vst = fixture("VST").riskBasis as RiskDriverBasisView;
    const debt = vst.financialRisk.signals.find((s) => s.signal === "debt_trend");
    if (!debt) throw new Error("fixture has no debt signal");
    const sameYear: RiskDriverBasisView = {
      ...vst,
      financialRisk: {
        ...vst.financialRisk,
        signals: vst.financialRisk.signals.map((s) =>
          s.signal === "debt_trend"
            ? {
                ...debt,
                observations: [
                  { ...debt.observations[0]!, period: "2024-01-02" },
                  { ...debt.observations[1]!, period: "2024-12-31" },
                ],
              }
            : s,
        ),
      },
    };
    const t = (key: keyof typeof en, params?: Record<string, string | number>) => tEn(key, params);
    expect(plain(riskBasisLabel(sameYear, t, "en-US"))).toContain("(2024-01-02: $14.4B → 2024-12-31: $16.3B)");
  });
});
