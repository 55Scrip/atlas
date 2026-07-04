# Swedish CLI Usage Guide

**Sprint:** 260
**Date:** 2026-07-04
**Status:** Current — CLI language support complete for all Phase 1 and Phase 2 commands.

---

## Purpose

This guide explains how to request Swedish-language output from the Atlas CLI,
which commands support it, what changes when `--language sv` is used, what
remains canonical English in all circumstances, and what Atlas will never
translate.

Atlas is a deterministic, local-only investment review tool. Language selection
changes display text only. It does not change reasoning, schemas, data, or
written file content.

---

## Quick Start

Request Swedish output by adding `--language sv` to any supported command:

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --language sv
```

```bash
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot.json \
  --language sv
```

```bash
atlas snapshot confirm draft.json \
  --output-draft confirmed.json \
  --language sv
```

Request English output explicitly with `--language en`:

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --language en
```

Omit `--language` to get the default English output — identical to `--language en`:

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json
```

---

## Supported Commands

The `--language {en,sv}` option is available on all seven Atlas CLI commands
that produce user-facing display text:

| Command | --language supported |
|---------|---------------------|
| `atlas weekly-review` | ✓ (Phase 1, Sprint 257) |
| `atlas snapshot validate` | ✓ (Phase 1, Sprint 257) |
| `atlas snapshot review` | ✓ (Phase 1, Sprint 257) |
| `atlas snapshot confirm` | ✓ (Phase 2, Sprint 259) |
| `atlas snapshot reject` | ✓ (Phase 2, Sprint 259) |
| `atlas snapshot export-research-notes` | ✓ (Phase 2, Sprint 259) |
| `atlas snapshot export-company-facts` | ✓ (Phase 2, Sprint 259) |

For each command, `--language` changes CLI display text only.

---

## Default Behavior

If `--language` is omitted, Atlas always outputs English.

```
atlas weekly-review ...                  → English (default)
atlas weekly-review ... --language en    → English (identical to default)
atlas weekly-review ... --language sv    → Swedish
```

Atlas does not detect or infer language automatically. There is no:

- Environment variable (`LANG`, `LC_ALL`, `ATLAS_LANGUAGE`, etc.)
- Configuration file language setting
- System locale detection (`locale.getlocale()`)
- Terminal locale inference

The absence of `--language` always means English output.

---

## Examples

### Weekly Review in Swedish

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json \
  --profile my_review/investor_profile.json \
  --journal my_review/decision_journal.json \
  --as-of 2026-01-05 \
  --language sv
```

### Snapshot validation in Swedish

```bash
atlas snapshot validate draft.json --language sv
```

### Snapshot review in Swedish

```bash
atlas snapshot review draft.json --language sv
```

### Snapshot confirm in Swedish (display only — written file unchanged)

```bash
atlas snapshot confirm draft.json \
  --output-draft confirmed.json \
  --language sv
```

### Research notes export in Swedish (display only — notes.md unchanged)

```bash
atlas snapshot export-research-notes confirmed_research_notes.json \
  --output-dir my_research \
  --language sv
```

### Company facts export in Swedish (display only — JSON unchanged)

```bash
atlas snapshot export-company-facts confirmed_company_facts.json \
  --output-dir my_facts \
  --language sv
```

---

## What Changes With --language sv

When `--language sv` is used, Atlas-generated headings, section titles, status
messages, and safety boundary labels appear in Swedish. Examples:

**Weekly Review headings:**
```
Atlas veckovis investeringsgranskning
Granskningens omfattning
Portföljkontext
Bevakningslistegranskning
Bolagsgranskningar som kräver uppmärksamhet
Portföljpassform och lämplighetsnotisar
Risk- och principskyddsräcken
Öppna beslut
Saknad evidens
Uppföljningsfrågor
Ej-åtgärder / Skäl att vänta
```

**Snapshot CLI headings:**
```
Validering av Snapshot Draft
Granskning av Snapshot Draft
Bekräftelse av Snapshot Draft
Avvisning av Snapshot Draft
Export av analysnotisar
Export av företagsfakta
Säkerhetsgräns
```

**Status labels:**
```
Status: giltig
Status: bekräftad
Status: avvisad
Status: skriven
Status: blockerad
```

These are the only changes. Everything else remains as documented in the
following sections.

---

## What Remains Canonical English

The following remain English in all circumstances, regardless of `--language`:

**Snapshot schema values:**
```
research_notes_snapshot    company_facts_snapshot
portfolio_snapshot         watchlist_snapshot
open_orders_snapshot       news_snapshot
external_analysis_snapshot unknown_snapshot

confirmed    rejected    draft    needs_user_review    superseded

high    medium    low    unknown
```

**Warning codes:**
```
missing_optional_profile    missing_optional_journal
missing_optional_financials  missing_optional_company_facts
missing_watchlist_status    unknown_watchlist_status
missing_sector              missing_market_value
```

**CLI commands and flags:**
```
weekly-review
snapshot validate    snapshot review
snapshot confirm     snapshot reject
snapshot export-research-notes    snapshot export-company-facts
--portfolio    --watchlist    --profile    --journal
--company-facts    --financials    --research-notes
--as-of    --scope-notes    --output-draft    --output-dir
--overwrite    --language
```

**Ticker symbols:**
```
ASML    MSFT    NOVO    XYL    CASH    (any ticker symbol)
```

**File paths and directory names:**
```
Any path passed by the user or written to disk.
```

**JSON keys in all written files:**
```
snapshot_type    confirmation_status    confidence
extracted_fields    target_local_file    draft_id
source_description    raw_source_reference    notes
related_tickers    created_at
```

The distinction: Atlas-generated *display labels* and *section headings* may
appear in Swedish. Canonical identifiers that appear in JSON files, schema keys,
enum values, warning codes, and CLI flag names always remain English.

---

## What Atlas Does Not Translate

Atlas does not translate user-provided content. Regardless of `--language`, the
following remain in the language the user wrote them:

- Pasted or typed notes (`notes` field in Snapshot drafts)
- Scope notes (`--scope-notes` in weekly-review)
- Research note text (all sections of notes.md files)
- Watchlist reasons and evidence-needed lists
- Decision journal entries
- Investor profile field values
- Snapshot `source_description` values
- Snapshot `raw_source_reference` values
- Values within `extracted_fields`
- Company facts values (all fields)

Only Atlas-generated display labels, section headings, status strings, and
safety boundary messages are localized. User-provided content is never
translated — not automatically, not by any renderer path.

**Example:** If a user writes Swedish research notes, those notes appear as
Swedish in the Weekly Review output regardless of `--language`. If a user writes
English research notes, those notes appear as English in the Weekly Review
output regardless of `--language`.

---

## Written File Behavior

For write-producing Snapshot commands (`snapshot confirm`, `snapshot reject`,
`snapshot export-research-notes`, `snapshot export-company-facts`), the
`--language` option affects only the terminal display text.

Written files are **identical** regardless of `--language`:

```
snapshot confirm:
  confirmed draft JSON  → same for default, --language en, --language sv

snapshot reject:
  rejected draft JSON   → same for default, --language en, --language sv

snapshot export-research-notes:
  notes.md              → same for default, --language en, --language sv

snapshot export-company-facts:
  TICKER.json           → same for default, --language en, --language sv
```

This has been verified with byte-for-byte file comparison tests.

Specifically, the following do not change based on `--language`:

- `confirmation_status` value in written draft JSON
- `snapshot_type` value in written draft JSON
- All schema keys in written files
- User-provided field values in written files
- Output file paths
- `target_local_file` values
- `raw_source_reference` values
- Research note Markdown content
- Company facts JSON field values

---

## Unsupported Languages

Only `en` and `sv` are supported. All other values fail clearly.

**What fails:**
```
--language fr
--language de
--language ja
--language EN       (case-sensitive — uppercase fails)
--language SV       (case-sensitive — uppercase fails)
--language en-US    (no region codes)
--language sv-SE    (no region codes)
--language xx
```

**What happens when an unsupported value is passed:**

- Non-zero exit code
- Error message names the unsupported value
- Error message lists supported values (`en`, `sv`)
- No partial rendered output
- No output files created or modified (for write-producing commands)

**No fallback.** An unsupported value does not silently fall back to English or
Swedish. It fails. This is intentional — explicit user choice is required.

**No case normalization.** `EN` and `SV` are not accepted. Use lowercase `en`
and `sv`.

**No region-code expansion.** `en-US` and `sv-SE` are not accepted. Use `en`
and `sv`.

---

## Safety Boundaries

Language selection does not change Atlas's safety behavior:

- Atlas does not provide investment recommendations in any language.
- Atlas does not replace the user's judgment.
- Language selection does not change reasoning, schemas, or data.
- Language selection changes display labels and headings only.
- Swedish output avoids urgency, certainty, price-target, execution, and
  personalized-advice phrasing — the same categories prohibited in English.
- Section 10 of the Weekly Review ("Ej-åtgärder / Skäl att vänta") continues
  to state that no action may be the appropriate outcome.

The Swedish safe-language guardrails that govern all Swedish output are
documented in `docs/SwedishSafeLanguageGuardrails.md`. These guardrails were
verified across 7 prohibited categories before Swedish was activated.

---

## Troubleshooting

**`--language sv` not recognized:**

Confirm the atlas CLI version is Sprint 257+ (Phase 1) or Sprint 259+ (Phase 2).
Run `atlas weekly-review --help` — if `--language` does not appear, the CLI
predates Phase 1.

**Output is still English after `--language sv`:**

Verify the command is one of the seven supported commands listed above. Commands
not in that list do not accept `--language`.

**Error: unsupported language:**

Check for typos, case errors (`EN` instead of `en`), or region codes (`sv-SE`
instead of `sv`). Only exact lowercase `en` and `sv` are accepted.

**Written file content changed unexpectedly:**

Language selection does not change written file content. If file content changed,
a different flag or input changed — not `--language`.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [docs/AtlasLocalizationBoundary.md](AtlasLocalizationBoundary.md) | Canonical/display boundary definition |
| [docs/SwedishSafeLanguageGuardrails.md](SwedishSafeLanguageGuardrails.md) | Swedish safe-language requirements |
| [docs/SwedishLocalizationReadinessChecklist.md](SwedishLocalizationReadinessChecklist.md) | B1–B14 activation checklist |
| [docs/CLILanguageOptionPlan.md](CLILanguageOptionPlan.md) | Full CLI language option design |
| [docs/Phase2SnapshotCLILanguagePlan.md](Phase2SnapshotCLILanguagePlan.md) | Phase 2 write-command language plan |
