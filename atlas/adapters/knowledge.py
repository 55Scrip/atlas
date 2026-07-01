"""Adapter from a local knowledge JSON shape to KnowledgeFact tuples.

Accepted JSON format::

    {
      "facts": [
        {
          "id": "fact-1",
          "subject_node_id": "company-nvda",
          "statement": "NVDA is a leading GPU supplier for data centres.",
          "source": {
            "id": "src-1",
            "name": "10-K 2025",
            "source_type": "Filing",
            "url": ""
          },
          "timestamp": "2026-07-01T00:00:00Z",
          "confidence": 85
        }
      ]
    }

Only ``id``, ``subject_node_id``, ``statement``, and ``source`` are required.
``timestamp`` defaults to an empty string. ``confidence`` defaults to 50.

This adapter is deterministic, side-effect free, and makes no network calls.
"""

from __future__ import annotations

from atlas.domains.knowledge.models import KnowledgeFact, KnowledgeReference, KnowledgeSource


def knowledge_facts_from_dict(data: object, source: str = "<input>") -> tuple[KnowledgeFact, ...]:
    """Build a tuple of KnowledgeFact from a parsed JSON dict.

    Raises ValueError with a clear message on invalid input.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Knowledge JSON in {source} must be a JSON object, got {type(data).__name__}"
        )

    raw_facts = data.get("facts", [])
    if not isinstance(raw_facts, list):
        raise ValueError(f"'facts' in {source} must be a list")

    return tuple(_parse_fact(item, i, source) for i, item in enumerate(raw_facts))


def _parse_fact(data: object, idx: int, source: str) -> KnowledgeFact:
    if not isinstance(data, dict):
        raise ValueError(f"Knowledge fact at index {idx} in {source} must be a JSON object")

    try:
        fact_id = str(data["id"])
        subject_node_id = str(data["subject_node_id"])
        statement = str(data["statement"])
    except KeyError as exc:
        raise ValueError(
            f"Knowledge fact at index {idx} in {source} missing required field {exc}"
        ) from exc

    raw_source = data.get("source", {})
    if not isinstance(raw_source, dict):
        raise ValueError(f"'source' at knowledge fact {idx} in {source} must be an object")

    ks = KnowledgeSource(
        id=str(raw_source.get("id", f"src-{idx}")),
        name=str(raw_source.get("name", "Unknown Source")),
        source_type=str(raw_source.get("source_type", "Unknown")),
        url=str(raw_source.get("url", "")),
    )
    kr = KnowledgeReference(
        id=f"ref-{fact_id}",
        source_id=ks.id,
        citation=str(raw_source.get("name", "Unknown Source")),
    )

    try:
        confidence = int(data.get("confidence", 50))
    except (TypeError, ValueError):
        confidence = 50

    return KnowledgeFact(
        id=fact_id,
        subject_node_id=subject_node_id,
        statement=statement,
        source=ks,
        timestamp=str(data.get("timestamp", "")),
        confidence=confidence,
        evidence_reference=kr,
    )
