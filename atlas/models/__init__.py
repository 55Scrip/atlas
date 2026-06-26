from typing import Any

__all__ = ["Company", "FinancialHistory"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from atlas.models.entities import Company, FinancialHistory

        return {"Company": Company, "FinancialHistory": FinancialHistory}[name]
    raise AttributeError(f"module 'atlas.models' has no attribute {name!r}")
