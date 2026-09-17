"""Reading a European filing without inventing anything.

Every rule here exists because a real filing broke a simpler one. The fixtures
are hand-built so each rule can be stated on its own, but the shapes and the
figures are the ones measured in Volvo's, Assa Abloy's, Atlas Copco's,
Investor's and Schneider's 2023/2024 ESEF reports.
"""
from __future__ import annotations

import pytest

from atlas.business_data_providers.esef.normalization import (
    duration_facts,
    instant_facts,
    normalize_filing,
)
from atlas.business_data_providers.esef.taxonomy import EsefTaxonomy, to_qname

SEK = "iso4217:SEK"


def document(*facts) -> dict:
    return {"facts": {str(i): f for i, f in enumerate(facts)}}


def fact(concept, period, value, unit=SEK, **extra_dimensions):
    return {"value": value,
            "dimensions": {"concept": concept, "period": period, "unit": unit,
                           "entity": "scheme:LEI", **extra_dimensions}}


EMPTY = EsefTaxonomy()


# --- Period semantics --------------------------------------------------


def test_a_closing_balance_is_dated_the_following_morning() -> None:
    """XBRL writes the instant as the next midnight. Keying on the date the
    balance actually belongs to finds nothing, and "nothing" is
    indistinguishable from an issuer that tagged no balance sheet at all."""
    doc = document(fact("ifrs-full:Assets", "2025-01-01T00:00:00", 223_605e6))
    assert instant_facts(doc, "ifrs-full:Assets") == {"2024-12-31": (223_605e6, SEK)}


def test_a_period_fact_is_keyed_by_the_year_it_ends_in() -> None:
    doc = document(fact("ifrs-full:Revenue", "2024-01-01T00:00:00/2025-01-01T00:00:00", 150_162e6))
    assert duration_facts(doc, "ifrs-full:Revenue") == {"2024-12-31": (150_162e6, SEK)}


def test_the_literal_period_end_is_not_where_the_balance_lives() -> None:
    """The mutation this guards: dropping the offset. It would report no
    balance sheet for every issuer in Europe."""
    doc = document(fact("ifrs-full:Assets", "2025-01-01T00:00:00", 1.0))
    assert instant_facts(doc, "ifrs-full:Assets").get("2025-01-01") is None


# --- Dimensions --------------------------------------------------------


def test_only_the_undimensioned_fact_is_the_consolidated_figure() -> None:
    """Volvo's 2023 revenue: a segment fact says 533,269 and the consolidated
    total is 552,764. Taking the first match takes the wrong one."""
    doc = document(
        fact("ifrs-full:Revenue", "2023-01-01T00:00:00/2024-01-01T00:00:00", 533_269e6,
             segment="TrucksMember"),
        fact("ifrs-full:Revenue", "2023-01-01T00:00:00/2024-01-01T00:00:00", 552_764e6),
    )
    assert duration_facts(doc, "ifrs-full:Revenue")["2023-12-31"][0] == 552_764e6


# --- Units and currency ------------------------------------------------


def test_the_reporting_currency_comes_from_the_filing() -> None:
    doc = document(fact("ifrs-full:Revenue", "2024-01-01T00:00:00/2025-01-01T00:00:00",
                        38_153e6, unit="iso4217:EUR"))
    assert normalize_filing(doc, EMPTY, "2024-12-31").currency == "EUR"


def test_a_unit_that_is_not_a_currency_is_not_read_as_one() -> None:
    doc = document(fact("ifrs-full:Revenue", "2024-01-01T00:00:00/2025-01-01T00:00:00",
                        1.0, unit="xbrli:shares"))
    assert normalize_filing(doc, EMPTY, "2024-12-31").currency is None


def test_two_currencies_in_one_filing_yield_none_rather_than_a_choice() -> None:
    doc = document(
        fact("ifrs-full:Revenue", "2024-01-01T00:00:00/2025-01-01T00:00:00", 1.0, unit="iso4217:SEK"),
        fact("ifrs-full:Assets", "2025-01-01T00:00:00", 2.0, unit="iso4217:EUR"),
    )
    assert normalize_filing(doc, EMPTY, "2024-12-31").currency is None


# --- Standard concepts, in order ---------------------------------------


def test_revenue_reads_the_alternate_ifrs_concept_when_that_is_what_was_filed() -> None:
    """Schneider files `RevenueFromContractsWithCustomers`; Volvo files
    `Revenue`. Both are correct IFRS, so both are candidates."""
    doc = document(fact("ifrs-full:RevenueFromContractsWithCustomers",
                        "2024-01-01T00:00:00/2025-01-01T00:00:00", 38_153e6, unit="iso4217:EUR"))
    period = normalize_filing(doc, EMPTY, "2024-12-31")
    assert period.values["revenue"] == 38_153e6
    assert period.concepts["revenue"] == ("ifrs-full:RevenueFromContractsWithCustomers",)


def test_the_first_reported_candidate_wins_and_the_rest_are_not_added() -> None:
    """Two spellings of one field must never be summed into a double count."""
    doc = document(
        fact("ifrs-full:Revenue", "2024-01-01T00:00:00/2025-01-01T00:00:00", 100.0),
        fact("ifrs-full:RevenueFromContractsWithCustomers",
             "2024-01-01T00:00:00/2025-01-01T00:00:00", 90.0),
    )
    assert normalize_filing(doc, EMPTY, "2024-12-31").values["revenue"] == 100.0


def test_a_field_nothing_carries_is_withheld_not_guessed() -> None:
    period = normalize_filing(document(), EMPTY, "2024-12-31")
    assert "revenue" in period.withheld
    assert "revenue" not in period.values


# --- Anchored extensions -----------------------------------------------

CAPEX = "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"
VOLVO_ANCHORS = EsefTaxonomy(anchors=(
    (CAPEX, "abvolvo_PurchaseOfTangibleAssetsLessLeasingVehiclesClassifiedAsInvestingActivities"),
    (CAPEX, "abvolvo_PurchaseOfLeasingVehiclesClassifiedAsInvestingActivities"),
))


def test_an_issuers_own_concepts_are_found_through_anchoring() -> None:
    """Volvo tags no standard capex concept at all. Its taxonomy declares two
    concepts of its own to be parts of the standard one, and that declaration
    -- not their names -- is what makes them readable."""
    doc = document(
        fact("abvolvo:PurchaseOfTangibleAssetsLessLeasingVehiclesClassifiedAsInvestingActivities",
             "2023-01-01T00:00:00/2024-01-01T00:00:00", 13_120e6),
        fact("abvolvo:PurchaseOfLeasingVehiclesClassifiedAsInvestingActivities",
             "2023-01-01T00:00:00/2024-01-01T00:00:00", 10_267e6),
    )
    period = normalize_filing(doc, VOLVO_ANCHORS, "2023-12-31")
    assert period.values["capital_expenditure"] == 23_387e6
    assert len(period.concepts["capital_expenditure"]) == 2


def test_every_anchored_part_is_counted_not_just_the_first() -> None:
    """The same completeness failure as the debt case: one part of two looks
    like a whole answer and is 44% of one."""
    doc = document(
        fact("abvolvo:PurchaseOfTangibleAssetsLessLeasingVehiclesClassifiedAsInvestingActivities",
             "2023-01-01T00:00:00/2024-01-01T00:00:00", 13_120e6),
        fact("abvolvo:PurchaseOfLeasingVehiclesClassifiedAsInvestingActivities",
             "2023-01-01T00:00:00/2024-01-01T00:00:00", 10_267e6),
    )
    assert normalize_filing(doc, VOLVO_ANCHORS, "2023-12-31").values["capital_expenditure"] != 13_120e6


def test_anchoring_direction_is_not_symmetric() -> None:
    """`wider` and `narrower` say opposite things. An extension that merely
    *contains* the standard concept is not a substitute for it -- that is the
    distinction which keeps a lease-inclusive bucket out of a debt figure."""
    reversed_anchor = EsefTaxonomy(anchors=(
        ("abvolvo_SomethingBigger", CAPEX),
    ))
    doc = document(fact("abvolvo:SomethingBigger",
                        "2023-01-01T00:00:00/2024-01-01T00:00:00", 99e6))
    assert "capital_expenditure" in normalize_filing(doc, reversed_anchor, "2023-12-31").withheld


def test_an_unanchored_extension_is_never_read_by_its_name() -> None:
    """Its name says capex. Nothing says it is capex, so it is not read."""
    doc = document(fact("abvolvo:PurchaseOfTangibleAssetsClassifiedAsInvestingActivities",
                        "2023-01-01T00:00:00/2024-01-01T00:00:00", 13_120e6))
    assert "capital_expenditure" in normalize_filing(doc, EMPTY, "2023-12-31").withheld


# --- Free cash flow ----------------------------------------------------


def test_free_cash_flow_is_derived_by_atlas_not_read_from_the_filing() -> None:
    doc = document(
        fact("ifrs-full:CashFlowsFromUsedInOperatingActivities",
             "2024-01-01T00:00:00/2025-01-01T00:00:00", 21_391e6),
        fact("ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
             "2024-01-01T00:00:00/2025-01-01T00:00:00", 2_562e6),
    )
    assert normalize_filing(doc, EMPTY, "2024-12-31").free_cash_flow == 18_829e6


def test_free_cash_flow_is_absent_when_either_input_is() -> None:
    doc = document(fact("ifrs-full:CashFlowsFromUsedInOperatingActivities",
                        "2024-01-01T00:00:00/2025-01-01T00:00:00", 21_391e6))
    assert normalize_filing(doc, EMPTY, "2024-12-31").free_cash_flow is None


# --- Concept naming ----------------------------------------------------


@pytest.mark.parametrize("linkbase,qname", [
    ("ifrs-full_Revenue", "ifrs-full:Revenue"),
    ("abvolvo_CurrentOtherLoans", "abvolvo:CurrentOtherLoans"),
    ("schneiderelectric_CostOfDebt", "schneiderelectric:CostOfDebt"),
])
def test_linkbase_names_convert_for_every_prefix_not_just_the_standard_one(linkbase, qname) -> None:
    """Converting only `ifrs-full` leaves every issuer extension unfindable,
    which looks exactly like an issuer that tagged nothing."""
    assert to_qname(linkbase) == qname


def test_nothing_here_is_written_per_issuer() -> None:
    """No rule may name a company. The moment one does, the next issuer needs
    its own, and the layer stops being a normalizer.

    Checked against the executable code only. The docstrings cite real issuers
    constantly -- that is the evidence for why each rule exists, and a plain
    text search would forbid explaining the design.
    """
    import ast
    import inspect

    from atlas.business_data_providers.esef import debt, normalization, taxonomy

    for module in (normalization, taxonomy, debt):
        tree = ast.parse(inspect.getsource(module))
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        }
        literals = [
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in docstrings
        ]
        for literal in literals:
            for name in ("VOLV-B", "ATCO-B", "ASSA-B", "INVE-B", "SU.PA",
                         "abvolvo", "schneiderelectric", "atla_", "ASSAABLOY"):
                assert name not in literal, (
                    f"{name!r} appears in executable code in {module.__name__}: {literal!r}"
                )


# --- A filing that reports a value it cannot carry ---------------------

TRANSFORM_ERROR = "(ixTransformValueError)"


def test_a_converter_error_is_not_a_number() -> None:
    """Inline XBRL writes this into a fact whose source value it could not
    transform. It is a string, and no arithmetic may treat it otherwise."""
    doc = document(fact("ifrs-full:Revenue", "2023-01-01T00:00:00/2024-01-01T00:00:00",
                        TRANSFORM_ERROR))
    assert duration_facts(doc, "ifrs-full:Revenue") == {}


def test_a_broken_value_is_reported_apart_from_an_untagged_concept() -> None:
    """Investor AB's 2023 report carries this on 43% of its facts, including
    its own primary statements; the same issuer's 2021 and 2022 reports carry
    none. Dropping it quietly would make a broken filing look exactly like one
    that never tagged the concept, and only one of those is a fact about the
    company."""
    broken = document(fact("ifrs-full:Revenue", "2023-01-01T00:00:00/2024-01-01T00:00:00",
                           TRANSFORM_ERROR))
    period = normalize_filing(broken, EMPTY, "2023-12-31")
    assert "revenue" in period.withheld
    assert "revenue" in period.reported_but_unusable


def test_a_concept_nobody_tagged_is_not_called_broken() -> None:
    """Investor reports no capital expenditure in any year. That is the
    company's own reporting, not a defect, and must not be described as one."""
    period = normalize_filing(document(), EMPTY, "2023-12-31")
    assert "revenue" in period.withheld
    assert period.reported_but_unusable == ()


def test_one_broken_period_does_not_spoil_a_good_one() -> None:
    """The 2024 filing carries a working 2024 figure and a broken 2023
    comparative. The good year must survive the bad one."""
    doc = document(
        fact("ifrs-full:Revenue", "2024-01-01T00:00:00/2025-01-01T00:00:00", 63_196e6),
        fact("ifrs-full:Revenue", "2023-01-01T00:00:00/2024-01-01T00:00:00", TRANSFORM_ERROR),
    )
    good = normalize_filing(doc, EMPTY, "2024-12-31")
    bad = normalize_filing(doc, EMPTY, "2023-12-31")
    assert good.values["revenue"] == 63_196e6
    assert good.reported_but_unusable == ()
    assert "revenue" in bad.reported_but_unusable


def test_a_broken_balance_value_is_caught_too() -> None:
    doc = document(fact("ifrs-full:Assets", "2024-01-01T00:00:00", TRANSFORM_ERROR))
    period = normalize_filing(doc, EMPTY, "2023-12-31")
    assert "total_assets" in period.reported_but_unusable
