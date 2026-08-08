"""Static validation for `atlas.alpha.case_generation` (ATLAS-027
Phase 31): exactly one canonical Case-generation owner, no automatic
Decision/Recommendation fabrication."""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "atlas" / "alpha" / "case_generation"


def _source_files() -> list[Path]:
    return [p for p in _PACKAGE_DIR.rglob("*.py") if "__pycache__" not in p.parts]


class TestNoAutomaticDecisionOrRecommendation:
    def test_module_never_mentions_decision_or_recommendation_creation(self):
        forbidden = ("DecisionService", "capture_decision", "DirectionalRecommendation", "RecommendationService")
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            for needle in forbidden:
                assert needle not in text, f"{path.name} unexpectedly references {needle!r}"


class TestOneCanonicalCaseGenerationOwner:
    def test_ensure_cases_is_only_called_from_the_known_allowed_set(self):
        """`ensure_cases` must have exactly two callers in production
        code -- `AlphaPortfolioService`'s own live write paths, and the
        ATLAS-029 legacy-holding backfill (`atlas/alpha/portfolio
        /backfill.py`), which reuses this exact same method rather than
        reimplementing Case creation, per that sprint's own explicit
        "do not create another Case generation implementation" rule.
        Scans the whole `atlas/alpha` tree (excluding this package's own
        definition and tests) for any other call site, which would mean
        case-generation logic had started spreading (Phase 20's own
        explicit rule)."""
        alpha_dir = _PACKAGE_DIR.parent
        callers = []
        for path in alpha_dir.rglob("*.py"):
            if "__pycache__" in path.parts or path.parent == _PACKAGE_DIR:
                continue
            text = path.read_text(encoding="utf-8")
            if "ensure_cases(" in text:
                callers.append(path)
        expected = {alpha_dir / "portfolio" / "service.py", alpha_dir / "portfolio" / "backfill.py"}
        assert set(callers) == expected, f"Expected exactly {expected}, found: {callers}"

    def test_case_service_create_call_sites_are_the_known_allowed_set(self):
        """`case_service.create()` should only ever be called from: this
        package (automatic generation) and the Discovery tool-execution
        router (the pre-existing manual "Open Investment Case" flow,
        ATLAS-018, untouched by this sprint). Any other call site would
        be a second, undisclosed Case-creation path (Phase 20's own
        explicit rule)."""
        import atlas as atlas_package

        atlas_dir = Path(atlas_package.__file__).resolve().parent
        allowed = {
            atlas_dir / "alpha" / "case_generation" / "service.py",
            atlas_dir / "ai" / "api" / "router.py",
        }
        callers = []
        for path in atlas_dir.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "case_service.create(" in text or "case_service.create()" in text:
                callers.append(path)
        assert set(callers) == allowed, f"Case-creation call sites changed: {sorted(callers)}"
