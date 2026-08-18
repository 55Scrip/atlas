"""Domain errors for the Canonical Security Foundation. Kept separate
from every other package's own errors -- these describe failures of
*this* aggregate's own invariants (Sprint L Phase 2), never a provider
call failure or a Decision/Case validity question."""
from __future__ import annotations


class CanonicalSecurityError(Exception):
    """Base class for this package's own errors."""


class InvalidExchangeCodeError(CanonicalSecurityError):
    """Raised when an `ExchangeCode` would be blank."""

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"ExchangeCode must not be blank, got {value!r}")


class InvalidMicCodeError(CanonicalSecurityError):
    """Raised when a `MicCode` would be blank."""

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"MicCode must not be blank, got {value!r}")


class InvalidTradingCurrencyError(CanonicalSecurityError):
    """Raised when a `TradingCurrency` is not exactly three alphabetic
    characters."""

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"TradingCurrency must be a 3-letter code, got {value!r}")


class UnsupportedSecurityTypeError(CanonicalSecurityError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported security type: {value!r}")


class UnsupportedListingRelationshipError(CanonicalSecurityError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported listing relationship: {value!r}")


class UnsupportedProviderNameError(CanonicalSecurityError):
    """Raised when a `ProviderName` names something other than one of
    the four providers this foundation currently knows about -- a guard
    against silently inventing a new provider label, matching
    `security_confirmation`'s own discovery-source allow-list
    discipline."""

    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported provider name: {value!r}")


class UnsupportedIdentityConfidenceError(CanonicalSecurityError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported identity confidence level: {value!r}")


class UnsupportedVerificationStatusError(CanonicalSecurityError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported verification status: {value!r}")


class UnsupportedResolutionStatusError(CanonicalSecurityError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported resolution status: {value!r}")


class UnsupportedIdentifierTypeError(CanonicalSecurityError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported identifier type: {value!r}")


class EmptyTickerError(CanonicalSecurityError):
    """Raised when a ticker field on the aggregate or a listing would be
    blank -- Sprint L Phase 10's own validation-rules example, "ticker
    cannot be empty," restated as an enforced invariant."""

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        super().__init__(f"{field_name} must not be blank")


class DuplicateListingError(CanonicalSecurityError):
    """Raised when a `ListingRef` with the same `(exchange_mic, ticker)`
    pair already exists on the aggregate -- Sprint L Phase 2's own
    invariant: a CanonicalSecurity may never have two listings sharing
    that pair, since that would itself be an unresolved collision, not a
    valid canonical state."""

    def __init__(self, exchange_mic: str, ticker: str) -> None:
        self.exchange_mic = exchange_mic
        self.ticker = ticker
        super().__init__(
            f"A listing for ({exchange_mic!r}, {ticker!r}) already exists on this CanonicalSecurity"
        )


class DuplicateProviderMappingError(CanonicalSecurityError):
    """Raised when a `ProviderMapping` with the same
    `(provider_name, provider_ticker)` pair already exists and is still
    active (not `SUPERSEDED_MAPPING`) -- Sprint L Phase 10's own
    validation-rules example, "provider mappings must not duplicate.\""""

    def __init__(self, provider_name: str, provider_ticker: str) -> None:
        self.provider_name = provider_name
        self.provider_ticker = provider_ticker
        super().__init__(
            f"An active mapping for provider {provider_name!r} ticker {provider_ticker!r} "
            "already exists on this CanonicalSecurity"
        )


class InvalidResolutionTransitionError(CanonicalSecurityError):
    """Raised when a requested `ResolutionStatus` transition is not one
    of the legal transitions defined in `lifecycle.py` -- Sprint L
    Phase 6's own instruction: "implement legal transitions only, reject
    invalid transitions.\""""

    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"Cannot transition CanonicalSecurity from {current!r} to {requested!r}")


class CanonicalStatusRequiresListingError(CanonicalSecurityError):
    """Raised when a transition to `CANONICAL` or `ACTIVE` is attempted
    on an aggregate with zero listings -- Sprint L Phase 2's own
    invariant: a CanonicalSecurity in either state must have at least
    one `ListingRef`."""

    def __init__(self, requested_status: str) -> None:
        self.requested_status = requested_status
        super().__init__(
            f"Cannot transition to {requested_status!r}: CanonicalSecurity has no listings"
        )
