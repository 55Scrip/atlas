"""Domain errors for the Canonical Security Resolution Service."""
from __future__ import annotations


class CanonicalSecurityResolutionError(Exception):
    """Base class for this package's own errors."""


class EmptySymbolError(CanonicalSecurityResolutionError):
    def __init__(self) -> None:
        super().__init__("ProviderCandidate.symbol must not be blank")


class NoCandidatesToResolveError(CanonicalSecurityResolutionError):
    """Raised when `resolve()` is called with an empty candidate tuple --
    distinct from `NO_MATCH`, which is a legitimate resolution *outcome*
    produced after filtering removes every candidate. An empty request is
    a caller error (nothing was even attempted), not a resolution
    result."""

    def __init__(self) -> None:
        super().__init__("Cannot resolve with zero candidates supplied")


class ManualConfirmationNotApplicableError(CanonicalSecurityResolutionError):
    """Raised when `confirm_manually` is called against a
    `ResolutionResult` whose outcome does not admit a manual choice
    (`NO_MATCH`, `REJECT`, or an outcome that already produced a
    `canonical_security` via `AUTO_ACCEPT`)."""

    def __init__(self, outcome: str) -> None:
        self.outcome = outcome
        super().__init__(f"Manual confirmation is not applicable to outcome {outcome!r}")


class CandidateNotInEvidenceError(CanonicalSecurityResolutionError):
    """Raised when `confirm_manually` is given a candidate that was not
    part of the original resolution's evidence -- manual confirmation
    may only select among candidates Atlas actually considered, never an
    arbitrary new one (that would bypass the resolution algorithm
    entirely)."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"Candidate {symbol!r} was not part of this resolution's evidence")


class ReplayMismatchError(CanonicalSecurityResolutionError):
    """Raised by the Replay Engine when re-running the stored evidence
    under the same algorithm version produces a different outcome,
    confidence, or selected candidate than what was originally recorded
    -- this is the failure the whole replay mechanism exists to detect,
    never silently ignored."""

    def __init__(self, field_name: str, original: object, replayed: object) -> None:
        self.field_name = field_name
        self.original = original
        self.replayed = replayed
        super().__init__(
            f"Replay mismatch on {field_name!r}: original={original!r}, replayed={replayed!r}"
        )


class ReplayVersionMismatchError(CanonicalSecurityResolutionError):
    """Raised when attempting to replay a resolution recorded under a
    different algorithm version than the one currently running -- replay
    equality is only a meaningful guarantee within one version; a
    version change is expected to potentially change output, and
    conflating that with a genuine determinism bug would be dishonest."""

    def __init__(self, recorded_version: str, current_version: str) -> None:
        self.recorded_version = recorded_version
        self.current_version = current_version
        super().__init__(
            f"Cannot replay a resolution recorded under version {recorded_version!r} "
            f"against the current algorithm version {current_version!r}"
        )
