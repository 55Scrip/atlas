import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType

import pytest

from atlas.ai import DecisionEngine, DiscoveryService, KnowledgeService, ReasoningService, SummaryService
from atlas.domains import (
    ai,
    authentication,
    daily_brief,
    decision_journal,
    knowledge,
    portfolio,
    research,
    watchlist,
)
from atlas.shared import (
    Company,
    Decision,
    Holding,
    JournalEntry,
    KnowledgeNode,
    MarketEvent,
    Portfolio,
    ResearchNote,
    User,
    Watchlist,
)


def test_shared_entities_are_immutable_and_freeze_metadata() -> None:
    entity = Portfolio(
        id="portfolio-1",
        name="Core",
        holdings=(Holding(company_id="company-1", ticker="NVDA", weight=0.2),),
        metadata={"nested": {"signals": ["quality", "growth"]}},
    )

    with pytest.raises(FrozenInstanceError):
        entity.name = "Changed"  # type: ignore[misc]

    assert isinstance(entity.metadata, MappingProxyType)
    assert isinstance(entity.metadata["nested"], MappingProxyType)
    assert entity.metadata["nested"]["signals"] == ("quality", "growth")


def test_canonical_entities_cover_sprint_36_shared_types() -> None:
    assert Company(id="c1", name="Nvidia", ticker="NVDA").ticker == "NVDA"
    assert Holding(company_id="c1", ticker="NVDA").market_value == 0.0
    assert Portfolio(id="p1", name="Core").holdings == ()
    assert Watchlist(id="w1", name="AI").tickers == ()
    assert ResearchNote(id="r1", title="Note", body="Body", created_at="2026-06-29").title
    assert JournalEntry(id="j1", title="Decision", asset_or_idea="NVDA", thesis="Thesis", created_at="2026-06-29").thesis
    assert User(id="u1", display_name="Investor").display_name == "Investor"
    assert MarketEvent(id="m1", title="Rate decision", occurred_at="2026-06-29").title
    assert Decision(id="d1", title="Review", decision_type="reviewed", created_at="2026-06-29").decision_type
    assert KnowledgeNode(id="k1", label="AI infrastructure", node_type="theme").label


def test_domain_boundaries_export_canonical_models() -> None:
    assert portfolio.Portfolio is Portfolio
    assert portfolio.Holding is Holding
    assert watchlist.Watchlist is Watchlist
    assert research.ResearchNote is ResearchNote
    assert decision_journal.JournalEntry is JournalEntry
    # daily_brief domain is a namespace stub — no re-exported models (Sprint 75)
    assert hasattr(daily_brief, "__all__")
    assert knowledge.KnowledgeNode is KnowledgeNode
    assert ai.ReasoningService is ReasoningService
    assert authentication.User is User


def test_ai_interfaces_are_replaceable_protocols() -> None:
    class DemoAI:
        def reason(self, context: str) -> str:
            return context

        def retrieve(self, query: str) -> tuple[str, ...]:
            return (query,)

        def summarize(self, content: str) -> str:
            return content

        def discover(self, prompt: str) -> tuple[str, ...]:
            return (prompt,)

        def evaluate(self, context: str) -> str:
            return context

    service = DemoAI()

    assert isinstance(service, ReasoningService)
    assert isinstance(service, KnowledgeService)
    assert isinstance(service, SummaryService)
    assert isinstance(service, DiscoveryService)
    assert isinstance(service, DecisionEngine)


def test_foundation_documentation_and_tooling_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    for relative_path in (
        "docs/Architecture.md",
        "docs/ProjectStructure.md",
        "docs/DecisionLog.md",
        "docs/DevelopmentGuide.md",
        "frontend/tsconfig.json",
        "frontend/package.json",
        ".github/workflows/ci.yml",
        ".pre-commit-config.yaml",
    ):
        assert (root / relative_path).exists()

    tsconfig = json.loads((root / "frontend/tsconfig.json").read_text())
    assert tsconfig["compilerOptions"]["strict"] is True
