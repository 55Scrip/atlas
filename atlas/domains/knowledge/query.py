from atlas.shared import KnowledgeNode

from atlas.domains.knowledge.models import (
    KnowledgeCollection,
    KnowledgeFact,
    KnowledgeRelationship,
)


class KnowledgeQueryService:
    """Deterministic query layer for knowledge collections."""

    def __init__(self, collection: KnowledgeCollection) -> None:
        self.collection = collection

    def find_connected_companies(self, company_id: str) -> tuple[KnowledgeNode, ...]:
        relationships = {
            KnowledgeRelationship.COMPANY_COMPETITOR,
            KnowledgeRelationship.COMPANY_SUPPLIER,
            KnowledgeRelationship.COMPANY_CUSTOMER,
        }
        node_ids = {
            edge.to_node_id
            for edge in self.collection.edges
            if edge.from_node_id == company_id and edge.relationship in relationships
        }
        node_ids.update(
            edge.from_node_id
            for edge in self.collection.edges
            if edge.to_node_id == company_id and edge.relationship in relationships
        )
        return _nodes_by_ids(self.collection.nodes, node_ids, node_type="Company")

    def list_suppliers(self, company_id: str) -> tuple[KnowledgeNode, ...]:
        return self._related_nodes(company_id, KnowledgeRelationship.COMPANY_SUPPLIER)

    def list_competitors(self, company_id: str) -> tuple[KnowledgeNode, ...]:
        forward = set(self._related_node_ids(company_id, KnowledgeRelationship.COMPANY_COMPETITOR))
        reverse = {
            edge.from_node_id
            for edge in self.collection.edges
            if edge.to_node_id == company_id
            and edge.relationship == KnowledgeRelationship.COMPANY_COMPETITOR
        }
        return _nodes_by_ids(self.collection.nodes, forward | reverse, node_type="Company")

    def find_companies_in_theme(self, theme_id: str) -> tuple[KnowledgeNode, ...]:
        company_ids = {
            edge.from_node_id
            for edge in self.collection.edges
            if edge.to_node_id == theme_id
            and edge.relationship == KnowledgeRelationship.COMPANY_THEME
        }
        return _nodes_by_ids(self.collection.nodes, company_ids, node_type="Company")

    def facts_for_company(self, company_id: str) -> tuple[KnowledgeFact, ...]:
        return tuple(
            sorted(
                (
                    fact
                    for fact in self.collection.facts
                    if fact.subject_node_id == company_id
                ),
                key=lambda fact: fact.id,
            )
        )

    def _related_nodes(
        self,
        company_id: str,
        relationship: KnowledgeRelationship,
    ) -> tuple[KnowledgeNode, ...]:
        return _nodes_by_ids(
            self.collection.nodes,
            set(self._related_node_ids(company_id, relationship)),
        )

    def _related_node_ids(
        self,
        company_id: str,
        relationship: KnowledgeRelationship,
    ) -> tuple[str, ...]:
        return tuple(
            edge.to_node_id
            for edge in self.collection.edges
            if edge.from_node_id == company_id and edge.relationship == relationship
        )


def _nodes_by_ids(
    nodes: tuple[KnowledgeNode, ...],
    node_ids: set[str],
    node_type: str | None = None,
) -> tuple[KnowledgeNode, ...]:
    return tuple(
        sorted(
            (
                node
                for node in nodes
                if node.id in node_ids and (node_type is None or node.node_type == node_type)
            ),
            key=lambda node: node.id,
        )
    )
