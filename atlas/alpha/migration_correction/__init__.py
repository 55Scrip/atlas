"""Migration-artifact correction: retract transient state a methodology
migration wrote because it ran in the wrong order, and recompute the
transitions that were diffed against it -- through the functions the
production write paths use, never by hand.

**What it corrects.** A methodology migration can compose a Case before
evidence the new method needs has been recorded. The Case is composed again
once it has, and history then holds an intermediate state that never
described the company, plus transitions narrating the migration order as
news (the new method's "no answer" -> its real answer). The clean history is
the one the migration writes when it runs in the right order: the surviving
pre-migration row, then the post-migration row as the new method's first
result, diffed against the pre-migration row exactly as the production `add`
paths diff -- so the methodology boundary re-baselines it
(`atlas.analysis_engine.methodology`).

**How.** Nothing is deleted. A transient row is *retracted*: its
`retracted_by` names its ledger entry (`table.py`) and every history read
skips it. A surviving row whose persisted transition was diffed against a
retracted row has that transition *recomputed* against its surviving
predecessor with `compare_snapshots` / `detect_decision_change`; its content
never changes, and the value it held is kept in the ledger. A change-log
entry narrating the retracted transition is retracted too: it neither
surfaces nor holds its natural key, as if the migration had never produced
it.

**Guards** (each re-derived from the database; one failure refuses the whole
correction and nothing is written):

- targets are explicit row ids of one explicit Case -- never a ticker -- and
  a reason is required; the default is a dry run;
- every target lies inside the declared migration window (at most a day),
  and each surviving predecessor lies before it;
- methodology identity: retracted and recomputed rows were written under the
  methodology this code runs, each surviving predecessor under another -- so
  a correction only ever restores a methodology boundary;
- no external evidence changed inside the window: nothing recorded for the
  Case, no market data, no share evidence -- except evidence retrieved before
  the window (a migration deriving from filings Atlas already held);
- the current head is never retracted and no row's content changes;
- a retracted row's successor is recomputed in the same correction;
- a change-log entry is retracted only when it narrates exactly a retracted
  Decision Memory row -> its successor, and the clean history does not
  reproduce it;
- a recompute target already holding its clean transition is refused as not
  an artifact.

**Idempotent.** The correction id derives from the request; a second run
finds its own ledger entries and writes nothing.

    python -m atlas.dev.correct_migration_artifacts --help
"""
