"""Strategic Salience v1 -- the vocabulary.

Strategy Intelligence v1 can say that a company stated a dependency. It
cannot say whether that dependency is what the company's calls are
organised around, or a remark made once in passing. A graph in which
VST's interconnection dependency and its project-financing dependency
look identical is a list, and a longer list is not a better
understanding.

**Salience is not truth.** A statement made in four consecutive quarters
is not more true than one made once; management repeats strategy
language by design, and a scripted line repeated on cue would otherwise
outrank a specific disclosure made once. What recurrence shows is where
attention is organised, and nothing else.

**Salience is not materiality.** A strategically central issue can have
small near-term financial impact, and a large line item need not define
strategy. No field here reads revenue, EBIT, capex or market value.

**Salience is not conviction.** None of Atlas's confidence vocabulary
appears in this package, and no output of it may ever be described in
those terms.

**There is no score.** Every signal is a count or a set with its evidence
attached. "Observed across 3 periods" is a fact a reader can check;
"salience 82/100" is a number nobody can argue with, which is why it is
absent -- see `SalienceEvidence` for what is offered instead.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["SignalSource", "SpeakerRole", "CallSection"]


class CallSection(str, Enum):
    """Where in a call a statement sits.

    Derived from metadata only -- the speaker's role and the statement
    index -- never from what the sentence says. The first analyst turn
    is the boundary: everything before it is management speaking
    unprompted, everything after is the exchange.

    That boundary is stable in the corpus. Across sixteen benchmark
    calls the first analyst turn lands at index 4, 5 or 6 every time.
    The obvious alternative -- finding the operator's "we will now begin
    the question-and-answer session" -- was tried and rejected: it is
    absent from nine of those sixteen calls and matches the wrong
    statement in others, which would have made a wording search decide a
    structural question.
    """

    PREPARED_REMARKS = "prepared_remarks"
    """Before the first analyst turn: what management chose to say."""
    QUESTION_AND_ANSWER = "question_and_answer"
    """From the first analyst turn on: what management was asked."""
    UNKNOWN = "unknown"
    """No analyst ever speaks, so the call has no boundary to find."""


class SpeakerRole(str, Enum):
    """A speaker's role, normalised from the title metadata.

    **No role outranks another.** A CFO is not less strategic than a
    CEO, and a business-unit head discussing their own unit is often the
    most specific voice on a call. Role is recorded so breadth can be
    counted and so analysts can be excluded -- never so that one voice
    can be weighted above another.
    """

    CHIEF_EXECUTIVE = "chief_executive"
    CHIEF_FINANCIAL = "chief_financial"
    OTHER_EXECUTIVE = "other_executive"
    """Any other C-level, president, VP, or head of a business function."""
    INVESTOR_RELATIONS = "investor_relations"
    ANALYST = "analyst"
    OPERATOR = "operator"
    UNKNOWN = "unknown"

    @property
    def is_management(self) -> bool:
        """Investor relations counts as management: IR reads prepared
        remarks and its statements are company-authored. Analysts and
        the operator never do."""
        return self in {
            SpeakerRole.CHIEF_EXECUTIVE,
            SpeakerRole.CHIEF_FINANCIAL,
            SpeakerRole.OTHER_EXECUTIVE,
            SpeakerRole.INVESTOR_RELATIONS,
        }


class SignalSource(str, Enum):
    """Which stored field a signal was read from, so a reader can go and
    check it rather than trusting a counter."""

    STRATEGY_NODE_EVIDENCE = "strategy_node_evidence"
    """The node's own passages, already carrying record ids."""
    TRANSCRIPT_SPEAKER_METADATA = "transcript_speaker_metadata"
    TRANSCRIPT_STATEMENT_INDEX = "transcript_statement_index"
    STRATEGY_GRAPH_EDGE = "strategy_graph_edge"
    FORWARD_EVIDENCE_LINK = "forward_evidence_link"
    """Guidance or customer-commitment evidence, supplied by the caller.
    This package never imports the forward-evidence layer: that layer
    owns guidance, `forward_context` is the one seam that interprets it
    for anything downstream, and a second importer here would be a
    second interpretation path into the same evidence."""
