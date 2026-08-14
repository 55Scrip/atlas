"""Boundary tests for `atlas.analysis_engine.valuation.proof` (`DE-015`
§16) -- proves `ProofVerdict`/`PathProof` are internal-only: never a new
public Domain Object, never exported through `support.py`'s own public
contract, never imported by Recommendation, never referenced by any API
schema.
"""
from __future__ import annotations

import pathlib

from atlas.analysis_engine.valuation import support


class TestNotPubliclyExported:
    def test_support_module_all_does_not_name_proof_types(self):
        assert "ProofVerdict" not in support.__all__
        assert "PathProof" not in support.__all__

    def test_support_module_does_not_import_proof_types_into_its_namespace(self):
        assert not hasattr(support, "ProofVerdict")
        assert not hasattr(support, "PathProof")


class TestNotConsumedByRecommendation:
    def test_recommendation_modules_never_reference_proof_types(self):
        repo_root = pathlib.Path(__file__).resolve().parents[4]
        recommendation_files = (
            repo_root / "atlas" / "analysis_engine" / "recommendation.py",
            repo_root / "atlas" / "analysis_engine" / "direction_selector.py",
            repo_root / "atlas" / "analysis_engine" / "recommendation_conviction.py",
        )
        for path in recommendation_files:
            assert path.exists(), path
            source = path.read_text(encoding="utf-8")
            assert "ProofVerdict" not in source
            assert "PathProof" not in source
            assert "valuation.proof" not in source


class TestNotReferencedByApiOrFrontend:
    def test_no_api_schema_references_proof_types(self):
        repo_root = pathlib.Path(__file__).resolve().parents[4]
        schema_path = repo_root / "atlas" / "alpha" / "investment_case" / "api" / "schemas.py"
        assert schema_path.exists()
        source = schema_path.read_text(encoding="utf-8")
        assert "ProofVerdict" not in source
        assert "PathProof" not in source

    def test_no_frontend_source_references_proof_types(self):
        repo_root = pathlib.Path(__file__).resolve().parents[4]
        frontend_dir = repo_root / "frontend" / "src"
        offenders = []
        for path in frontend_dir.rglob("*.ts*"):
            text = path.read_text(encoding="utf-8")
            if "ProofVerdict" in text or "PathProof" in text:
                offenders.append(str(path))
        assert offenders == []


class TestOnlyValuationPackageImportsProof:
    def test_only_valuation_package_modules_import_proof(self):
        repo_root = pathlib.Path(__file__).resolve().parents[4]
        analysis_engine_dir = repo_root / "atlas" / "analysis_engine"
        offenders = []
        for path in analysis_engine_dir.rglob("*.py"):
            if "valuation" in path.parts:
                continue
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "valuation.proof" in text or "valuation import proof" in text:
                offenders.append(str(path))
        assert offenders == []
