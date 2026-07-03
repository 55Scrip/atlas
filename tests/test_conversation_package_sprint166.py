"""Sprint 166: Conversation package audit checkpoint guardrails.

Verifies:
- atlas/conversation/ contains exactly 2 modules (init + engine)
- atlas.conversation.__all__ exports exactly 6 expected symbols
- All 6 exports are importable
- ConversationEngine has an .answer() method
- atlas/conversation/ has no imports from deleted closed-track modules
- atlas/conversation/ does not import YahooFinanceProvider directly
- atlas ask CLI command imports expected conversation symbols
- IntelligenceEngine dependency remains intentional (runtime import present)
- RiskAnalysis dependency remains intentional (runtime import present)
- atlas.reasoning remains deleted
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint166_conversation_package_two_modules_only() -> None:
    """Sprint 166: atlas/conversation/ must contain exactly 2 modules (init + engine)."""
    import atlas.conversation as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/conversation/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint166_conversation_all_has_six_exports() -> None:
    """Sprint 166: atlas.conversation.__all__ must contain exactly 6 exports."""
    import atlas.conversation as pkg

    expected = {
        "ConversationEngine",
        "ConversationInput",
        "ConversationIntent",
        "ConversationResponse",
        "IntentClassifier",
        "render_conversation_response",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.conversation.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint166_all_exports_importable() -> None:
    """Sprint 166: every symbol in atlas.conversation.__all__ must be importable."""
    import atlas.conversation as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.conversation.{name} in __all__ but not importable"


# ── ConversationEngine contract ───────────────────────────────────────────────

def test_sprint166_conversation_engine_has_answer_method() -> None:
    """Sprint 166: ConversationEngine must have an .answer() method."""
    from atlas.conversation import ConversationEngine

    assert callable(getattr(ConversationEngine, "answer", None)), (
        "ConversationEngine must have a callable .answer() method"
    )


# ── Boundary: no stale closed-track imports ───────────────────────────────────

def test_sprint166_conversation_has_no_deleted_module_imports() -> None:
    """Sprint 166: atlas/conversation/ must not import from deleted closed-track modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    conv_dir = Path("atlas/conversation")
    for py_file in conv_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


def test_sprint166_conversation_does_not_import_yahoo_finance_provider_directly() -> None:
    """Sprint 166: atlas/conversation/ must not import YahooFinanceProvider directly."""
    conv_dir = Path("atlas/conversation")
    for py_file in conv_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "YahooFinanceProvider" not in source, (
            f"{py_file}: YahooFinanceProvider must not be imported in atlas/conversation/ "
            "— network access must remain CLI opt-in only"
        )


# ── IntelligenceEngine dependency remains intentional ────────────────────────

def test_sprint166_conversation_imports_intelligence_engine() -> None:
    """Sprint 166: atlas/conversation/engine.py must import IntelligenceEngine (intentional dependency)."""
    source = Path("atlas/conversation/engine.py").read_text(encoding="utf-8")
    assert "from atlas.intelligence import" in source, (
        "atlas/conversation/engine.py must import from atlas.intelligence — "
        "IntelligenceEngine is an intentional dependency for COMPANY_ANALYSIS and GENERAL_INVESTMENT_GUIDANCE intents"
    )
    assert "IntelligenceEngine" in source, (
        "atlas/conversation/engine.py must reference IntelligenceEngine"
    )


# ── RiskAnalysis dependency remains intentional ───────────────────────────────

def test_sprint166_conversation_imports_risk_analysis() -> None:
    """Sprint 166: atlas/conversation/engine.py must import RiskAnalysis (intentional optional context)."""
    source = Path("atlas/conversation/engine.py").read_text(encoding="utf-8")
    assert "from atlas.risk import RiskAnalysis" in source, (
        "atlas/conversation/engine.py must import RiskAnalysis from atlas.risk — "
        "this is an intentional optional caller-supplied context dependency"
    )


# ── CLI ask command active ────────────────────────────────────────────────────

def test_sprint166_cli_ask_command_imports_conversation_engine() -> None:
    """Sprint 166: atlas/cli/main.py must import ConversationEngine for atlas ask command."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "ConversationEngine" in source, (
        "atlas/cli/main.py must import ConversationEngine for atlas ask command"
    )
    assert "render_conversation_response" in source, (
        "atlas/cli/main.py must import render_conversation_response"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint166_reasoning_package_deleted() -> None:
    """Sprint 166: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint166_principles_removed_checks_gone() -> None:
    """Sprint 166: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


def test_sprint166_analysis_cleanup_track_closed() -> None:
    """Sprint 166: deleted atlas.analysis modules must remain not importable."""
    deleted = [
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.watchlist",
        "atlas.analysis.growth",
        "atlas.analysis.scoring",
    ]
    for mod in deleted:
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable (deleted in analysis cleanup track)"
        except ModuleNotFoundError:
            pass
