"""The Discovery candidate universe.

Discovery's job is "what investment ideas should I consider that I am
not already following". Before this package it built its candidates
from `nonHeldWatchlistEntries` -- the Watchlist minus Portfolio
holdings -- so the only ideas Atlas could surface were ones the
investor had already found and added themselves. With one active
Watchlist entry, Discovery contained exactly one candidate, and it was
MU, which the investor had put there.

This package answers the question from the other side: which securities
does Atlas already know enough about, and which the investor is *not*
already following?

Sprint 4A is what makes that possible. A Case now carries its own
instrument binding, so a security can have a real, analysable Case
without the investor holding or watching it. The candidate universe is
therefore: bound Cases, minus current holdings, minus active Watchlist
entries, keeping only those Atlas has actually looked at.

Deliberately not a market scanner. Nothing here ingests a universe,
screens the market, detects events or calls a provider. It reads Cases
Atlas already has and filters them by state it already computed. Making
Discovery genuinely broad needs a candidate-generation engine that does
not exist yet; this surfaces what is honestly available today.
"""
