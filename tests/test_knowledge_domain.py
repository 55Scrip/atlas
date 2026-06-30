from dataclasses import FrozenInstanceError

import pytest

from atlas.domains.knowledge import (
    KnowledgeCollection,
    KnowledgeFact,
    KnowledgeNode,
    KnowledgeQueryService,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeRelationshipEngine,
    KnowledgeSource,
)


def _node(node_id: str, label: str, node_type: str = "Company") -> KnowledgeNode:
    return KnowledgeNode(id=node_id, label=label, node_type=node_type)


def _source() -> KnowledgeSource:
    return KnowledgeSource(id="source-1", name="Company filing", source_type="Filing")


def _reference() -> KnowledgeReference:
    return KnowledgeReference(
        id="reference-1",
        source_id="source-1",
        citation="Annual report",
        locator="page 12",
    )


def _fact(fact_id: str = "fact-1", subject_node_id: str = "company-nvda") -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        subject_node_id=subject_node_id,
        statement="NVIDIA reports data center revenue.",
        source=_source(),
        timestamp="2026-06-30T00:00:00Z",
        confidence=92,
        evidence_reference=_reference(),
        metadata={"tags": ["filing", "revenue"]},
    )


def test_knowledge_fact_has_source_attribution_and_is_immutable() -> None:
    fact = _fact()

    assert fact.source.name == "Company filing"
    assert fact.timestamp == "2026-06-30T00:00:00Z"
    assert fact.confidence == 92
    assert fact.evidence_reference.citation == "Annual report"
    assert fact.metadata["tags"] == ("filing", "revenue")

    with pytest.raises(FrozenInstanceError):
        fact.statement = "Changed"  # type: ignore[misc]

    with pytest.raises(TypeError):
        fact.metadata["tags"] = ()


def test_relationship_engine_creates_explicit_relationships() -> None:
    engine = KnowledgeRelationshipEngine()
    nvda = _node("company-nvda", "NVIDIA")
    semis = _node("sector-semiconductors", "Semiconductors", "Sector")
    amd = _node("company-amd", "AMD")

    sector_edge = engine.company_to_sector(nvda, semis, fact_id="fact-sector")
    competitor_edge = engine.company_to_competitor(nvda, amd)

    assert sector_edge.relationship == KnowledgeRelationship.COMPANY_SECTOR
    assert sector_edge.from_node_id == "company-nvda"
    assert sector_edge.to_node_id == "sector-semiconductors"
    assert sector_edge.fact_id == "fact-sector"
    assert competitor_edge.relationship == KnowledgeRelationship.COMPANY_COMPETITOR


def test_knowledge_collection_deduplicates_deterministically() -> None:
    nvda_old = _node("company-nvda", "Old NVIDIA")
    nvda_new = _node("company-nvda", "NVIDIA")
    amd = _node("company-amd", "AMD")
    fact = _fact()

    collection = KnowledgeCollection(
        nodes=(nvda_old, amd, nvda_new),
        facts=(fact, fact),
    )

    assert [node.id for node in collection.nodes] == ["company-amd", "company-nvda"]
    assert collection.nodes[1].label == "NVIDIA"
    assert collection.facts == (fact,)


def test_query_service_lists_suppliers_and_competitors() -> None:
    engine = KnowledgeRelationshipEngine()
    nvda = _node("company-nvda", "NVIDIA")
    tsmc = _node("company-tsmc", "TSMC")
    amd = _node("company-amd", "AMD")
    collection = KnowledgeCollection(
        nodes=(nvda, tsmc, amd),
        edges=(
            engine.company_to_supplier(nvda, tsmc),
            engine.company_to_competitor(nvda, amd),
        ),
    )

    query = KnowledgeQueryService(collection)

    assert [node.id for node in query.list_suppliers("company-nvda")] == ["company-tsmc"]
    assert [node.id for node in query.list_competitors("company-nvda")] == ["company-amd"]


def test_query_service_finds_connected_companies_and_theme_members() -> None:
    engine = KnowledgeRelationshipEngine()
    nvda = _node("company-nvda", "NVIDIA")
    amd = _node("company-amd", "AMD")
    msft = _node("company-msft", "Microsoft")
    ai_theme = _node("theme-ai-infrastructure", "AI infrastructure", "Theme")
    collection = KnowledgeCollection(
        nodes=(ai_theme, nvda, msft, amd),
        edges=(
            engine.company_to_customer(nvda, msft),
            engine.company_to_competitor(amd, nvda),
            engine.company_to_theme(nvda, ai_theme),
            engine.company_to_theme(msft, ai_theme),
        ),
    )

    query = KnowledgeQueryService(collection)

    assert [node.id for node in query.find_connected_companies("company-nvda")] == [
        "company-amd",
        "company-msft",
    ]
    assert [node.id for node in query.find_companies_in_theme("theme-ai-infrastructure")] == [
        "company-msft",
        "company-nvda",
    ]


def test_query_service_retrieves_facts_for_company() -> None:
    nvda_fact = _fact("fact-nvda", "company-nvda")
    amd_fact = _fact("fact-amd", "company-amd")
    collection = KnowledgeCollection(facts=(amd_fact, nvda_fact))

    query = KnowledgeQueryService(collection)

    assert [fact.id for fact in query.facts_for_company("company-nvda")] == ["fact-nvda"]


def test_empty_collection_queries_are_safe() -> None:
    query = KnowledgeQueryService(KnowledgeCollection())

    assert query.find_connected_companies("missing") == ()
    assert query.list_suppliers("missing") == ()
    assert query.list_competitors("missing") == ()
    assert query.find_companies_in_theme("missing") == ()
    assert query.facts_for_company("missing") == ()
