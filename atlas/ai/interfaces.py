from typing import Protocol, runtime_checkable


@runtime_checkable
class ReasoningService(Protocol):
    """Interface for future AI-assisted reasoning services."""

    def reason(self, context: str) -> str:
        """Return structured reasoning for supplied context."""


@runtime_checkable
class KnowledgeService(Protocol):
    """Interface for future knowledge retrieval and graph services."""

    def retrieve(self, query: str) -> tuple[str, ...]:
        """Return knowledge records relevant to a query."""


@runtime_checkable
class SummaryService(Protocol):
    """Interface for future summarization services."""

    def summarize(self, content: str) -> str:
        """Return a concise summary of supplied content."""


@runtime_checkable
class DiscoveryService(Protocol):
    """Interface for future discovery and research direction services."""

    def discover(self, prompt: str) -> tuple[str, ...]:
        """Return research directions for a prompt."""


@runtime_checkable
class DecisionEngine(Protocol):
    """Interface for future decision-support orchestration."""

    def evaluate(self, context: str) -> str:
        """Return a deterministic decision-support assessment."""
