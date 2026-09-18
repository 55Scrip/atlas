"""Reading the names a filer gives its own elements.

Fragments are copied from the real linkbases: VST's
`vistra-20251231_lab.xml` (SEC, `link:`-prefixed) and Volvo's
`abvolvo-2022-12-31_lab-sv.xml` (ESEF, bare elements, language-suffixed
filename). The two serialisations are why every rule here reads local
names rather than spellings.
"""
import pytest

from atlas.business_data_providers.taxonomy_labels import (
    TaxonomyLabel,
    is_label_linkbase,
    read_label_linkbase,
)

# SEC: prefixed elements, xlink-prefixed attributes.
SEC = """<?xml version="1.0" encoding="us-ascii"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase"
               xmlns:xlink="http://www.w3.org/1999/xlink">
 <link:labelLink xlink:role="http://www.xbrl.org/2003/role/link" xlink:type="extended">
  <link:loc xlink:type="locator" xlink:href="vistra-20251231.xsd#vistra_ComanchePeakNuclearPowerPlantMember" xlink:label="cp"/>
  <link:label xlink:type="resource" xlink:label="cp_lbl" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="en-US">Comanche Peak Nuclear Power Plant [Member]</link:label>
  <link:label xlink:type="resource" xlink:label="cp_terse" xlink:role="http://www.xbrl.org/2003/role/terseLabel" xml:lang="en-US">Comanche Peak Nuclear Power Plant</link:label>
  <link:labelArc xlink:type="arc" xlink:from="cp" xlink:to="cp_lbl"/>
  <link:labelArc xlink:type="arc" xlink:from="cp" xlink:to="cp_terse"/>
  <link:loc xlink:type="locator" xlink:href="vistra-20251231.xsd#vistra_TexasSegmentMember" xlink:label="tx"/>
  <link:label xlink:type="resource" xlink:label="tx_lbl" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="en-US">Texas Segment [Member]</link:label>
  <link:labelArc xlink:type="arc" xlink:from="tx" xlink:to="tx_lbl"/>
 </link:labelLink>
</link:linkbase>"""

# ESEF: bare elements, no link: prefix anywhere.
ESEF = """<?xml version="1.0" encoding="utf-8"?>
<linkbase xmlns="http://www.xbrl.org/2003/linkbase">
 <labelLink xlink:role="http://www.xbrl.org/2003/role/link" xlink:type="extended"
            xmlns:xlink="http://www.w3.org/1999/xlink">
  <loc xlink:type="locator" xlink:href="abvolvo-2022-12-31.xsd#abvolvo_FinancialServicesMember" xlink:label="fs"/>
  <label xlink:type="resource" xlink:label="fs_lbl" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="sv">Financial Services (member)</label>
  <labelArc xlink:type="arc" xlink:from="fs" xlink:to="fs_lbl"/>
  <loc xlink:type="locator" xlink:href="abvolvo-2022-12-31.xsd#abvolvo_FinancialServciesMember" xlink:label="typo"/>
  <label xlink:type="resource" xlink:label="typo_lbl" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="sv">Financial Servcies (member)</label>
  <labelArc xlink:type="arc" xlink:from="typo" xlink:to="typo_lbl"/>
 </linkbase>"""


def _ids(body):
    return sorted((l.element_id, l.text, l.role) for l in labels(body))


def labels(body, doc="x_lab.xml"):
    return read_label_linkbase(body, source_document=doc, source_locator="acc-1")


def one(body, element_id, role="http://www.xbrl.org/2003/role/label"):
    return next(l for l in labels(body) if l.element_id == element_id and l.role == role)


# -------------------------------------------------- filename detection
@pytest.mark.parametrize("name,expected", [
    ("vistra-20251231_lab.xml", True),
    ("abvolvo-2022-12-31_lab-sv.xml", True),      # ESEF language suffix
    ("sand-2023-12-31_lab-en-GB.xml", True),
    ("vistra-20251231_cal.xml", False),
    ("vistra-20251231_pre.xml", False),
    ("goog-20251231.xsd", False),
])
def test_both_label_filename_conventions_are_recognised(name, expected):
    assert is_label_linkbase(name) is expected


# ------------------------------------------- both serialisations parse
def test_a_prefixed_sec_linkbase_parses():
    assert one(SEC, "vistra_ComanchePeakNuclearPowerPlantMember").text == \
        "Comanche Peak Nuclear Power Plant [Member]"


def test_a_bare_esef_linkbase_parses():
    # The same structure without a single `link:` prefix. A parser that
    # required one would return nothing here -- and nothing looks
    # exactly like "this filer declared no labels".
    assert one(ESEF, "abvolvo_FinancialServicesMember").text == "Financial Services (member)"


def test_the_two_serialisations_yield_the_same_shape():
    assert {type(l) for l in labels(SEC)} == {type(l) for l in labels(ESEF)} == {TaxonomyLabel}


# ------------------------------------------------ structure, not guess
def test_a_label_reaches_an_element_only_through_an_arc():
    # A loc and a label with no arc between them are not a declaration.
    unjoined = SEC.replace('<link:labelArc xlink:type="arc" xlink:from="tx" xlink:to="tx_lbl"/>', "")
    assert not any(l.element_id == "vistra_TexasSegmentMember" for l in labels(unjoined))
    assert any(l.element_id == "vistra_TexasSegmentMember" for l in labels(SEC))


def test_an_arc_pointing_at_nothing_is_skipped_not_guessed():
    # A dangling arc names a locator that does not exist. It is not a
    # declaration, and it must not crash the read of the ones that are.
    dangling = SEC.replace("</link:labelLink>",
                           '<link:labelArc xlink:type="arc" xlink:from="ghost" xlink:to="cp_lbl"/>'
                           "</link:labelLink>")
    assert _ids(dangling) == _ids(SEC)


def test_every_arc_produces_its_own_record():
    # Two arcs from one element to two resources are two labels. A
    # reader that stopped at the first would silently drop the terse
    # label, which is the one without "[Member]" in it.
    records = [l for l in labels(SEC)
               if l.element_id.endswith("ComanchePeakNuclearPowerPlantMember")]
    assert len(records) == 2


def test_the_locator_href_is_preserved_whole():
    label = one(SEC, "vistra_ComanchePeakNuclearPowerPlantMember")
    assert label.element_href == "vistra-20251231.xsd#vistra_ComanchePeakNuclearPowerPlantMember"
    assert label.element_id == "vistra_ComanchePeakNuclearPowerPlantMember"


# ------------------------------------------------- qname and namespace
def test_the_qname_comes_from_the_id_not_from_the_issuer():
    label = one(SEC, "vistra_ComanchePeakNuclearPowerPlantMember")
    assert label.element_qname == "vistra:ComanchePeakNuclearPowerPlantMember"
    assert label.namespace_prefix == "vistra"


def test_an_id_without_a_prefix_yields_no_qname_rather_than_an_invented_one():
    body = SEC.replace("#vistra_ComanchePeakNuclearPowerPlantMember", "#SomeBareId")
    label = one(body, "SomeBareId")
    assert label.element_qname is None
    assert label.namespace_prefix is None


def test_two_issuers_sharing_a_local_name_stay_distinct():
    a = one(SEC, "vistra_ComanchePeakNuclearPowerPlantMember")
    b = one(SEC.replace("vistra_Comanche", "other_Comanche").replace(
        "#vistra_Comanche", "#other_Comanche"), "other_ComanchePeakNuclearPowerPlantMember")
    assert a.element_qname != b.element_qname


# ----------------------------------------------------- role + language
def test_every_role_is_preserved_separately():
    roles = {l.role for l in labels(SEC) if l.element_id.endswith("ComanchePeakNuclearPowerPlantMember")}
    assert roles == {"http://www.xbrl.org/2003/role/label",
                     "http://www.xbrl.org/2003/role/terseLabel"}


def test_multiple_labels_for_one_element_are_all_kept():
    # The standard label carries "[Member]" and the terse one does not.
    # Choosing between them is a consumer's decision.
    texts = {l.text for l in labels(SEC)
             if l.element_id.endswith("ComanchePeakNuclearPowerPlantMember")}
    assert texts == {"Comanche Peak Nuclear Power Plant [Member]",
                     "Comanche Peak Nuclear Power Plant"}


def test_language_is_preserved():
    assert one(SEC, "vistra_TexasSegmentMember").language == "en-US"
    assert one(ESEF, "abvolvo_FinancialServicesMember").language == "sv"


# --------------------------------------------------- spelling fidelity
def test_the_filers_typo_survives_verbatim():
    # Volvo declares two elements one transposed letter apart. Normalising
    # either would erase the distinction identity resolution rests on.
    typo = one(ESEF, "abvolvo_FinancialServciesMember")
    correct = one(ESEF, "abvolvo_FinancialServicesMember")
    assert typo.text == "Financial Servcies (member)"
    assert correct.text == "Financial Services (member)"
    assert typo.text != correct.text


# -------------------------------------------------------- invariants
def _fingerprint(ls):
    return sorted((l.element_id, l.text, l.role, l.language) for l in ls)


def test_parsing_is_deterministic():
    assert _fingerprint(labels(SEC)) == _fingerprint(labels(SEC))


def test_parsing_the_same_body_twice_yields_no_duplicates():
    once = labels(SEC)
    assert len(once) == len(set((l.element_id, l.text, l.role, l.language) for l in once))


def test_document_order_of_arcs_does_not_change_the_result():
    lines = SEC.splitlines()
    arcs = [i for i, l in enumerate(lines) if "labelArc" in l]
    swapped = lines[:]
    swapped[arcs[0]], swapped[arcs[1]] = swapped[arcs[1]], swapped[arcs[0]]
    assert _fingerprint(labels("\n".join(swapped))) == _fingerprint(labels(SEC))


def test_the_reader_has_no_clock_and_reaches_for_nothing():
    import ast
    import pathlib

    source = pathlib.Path(
        "atlas/business_data_providers/taxonomy_labels.py").read_text(encoding="utf-8")
    assert "datetime" not in source
    modules = {n.module for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)}
    assert not any((m or "").startswith("atlas") for m in modules)
    assert "httpx" not in source and "requests" not in source
