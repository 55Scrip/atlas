from atlas.shared import KnowledgeNode

from atlas.domains.knowledge.models import KnowledgeEdge, KnowledgeRelationship


class KnowledgeRelationshipEngine:
    """Create explicit knowledge relationships without inference."""

    def company_to_sector(
        self,
        company: KnowledgeNode,
        sector: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, sector, KnowledgeRelationship.COMPANY_SECTOR, fact_id)

    def company_to_industry(
        self,
        company: KnowledgeNode,
        industry: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, industry, KnowledgeRelationship.COMPANY_INDUSTRY, fact_id)

    def company_to_country(
        self,
        company: KnowledgeNode,
        country: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, country, KnowledgeRelationship.COMPANY_COUNTRY, fact_id)

    def company_to_competitor(
        self,
        company: KnowledgeNode,
        competitor: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, competitor, KnowledgeRelationship.COMPANY_COMPETITOR, fact_id)

    def company_to_supplier(
        self,
        company: KnowledgeNode,
        supplier: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, supplier, KnowledgeRelationship.COMPANY_SUPPLIER, fact_id)

    def company_to_customer(
        self,
        company: KnowledgeNode,
        customer: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, customer, KnowledgeRelationship.COMPANY_CUSTOMER, fact_id)

    def company_to_technology(
        self,
        company: KnowledgeNode,
        technology: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, technology, KnowledgeRelationship.COMPANY_TECHNOLOGY, fact_id)

    def company_to_theme(
        self,
        company: KnowledgeNode,
        theme: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(company, theme, KnowledgeRelationship.COMPANY_THEME, fact_id)

    def theme_to_theme(
        self,
        theme: KnowledgeNode,
        related_theme: KnowledgeNode,
        fact_id: str | None = None,
    ) -> KnowledgeEdge:
        return _edge(theme, related_theme, KnowledgeRelationship.THEME_THEME, fact_id)


def _edge(
    from_node: KnowledgeNode,
    to_node: KnowledgeNode,
    relationship: KnowledgeRelationship,
    fact_id: str | None,
) -> KnowledgeEdge:
    return KnowledgeEdge(
        id=f"{from_node.id}:{relationship.name.lower()}:{to_node.id}",
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        relationship=relationship,
        fact_id=fact_id,
    )
