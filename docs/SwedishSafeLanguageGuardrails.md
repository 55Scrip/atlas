# Swedish Safe-Language Guardrails

**Sprint:** 247
**Date:** 2026-07-04
**Status:** Specification only — `sv` is not enabled — no Swedish output implemented

---

## Purpose

This document defines the safe-language guardrails that must be satisfied before
Atlas is permitted to generate Swedish-language output.

Atlas may later speak Swedish, but it must not sound like it is giving investment
advice, urging action, promising outcomes, or replacing the user's judgment.

These guardrails are a prerequisite for enabling `sv` in `atlas/locale_support.py`.
They define the Swedish safety layer — not the Swedish renderer implementation.

---

## Scope

This document covers:

- Prohibited Swedish language categories
- Safe Swedish alternatives for Atlas-generated display text
- English-to-Swedish Atlas concept mapping
- Weekly Review Swedish style rules
- Snapshot CLI Swedish style rules
- User-provided Swedish content handling
- Required tests before `sv` can be enabled

---

## Non-Goals

This document does not:

- Enable Swedish output in any renderer
- Add `sv` to `atlas/locale_support.py`
- Translate any runtime string
- Add gettext, translation catalogs, or locale detection
- Define a Swedish renderer implementation
- Translate schema values, enum values, or CLI flags
- Provide Swedish financial analysis guidance

---

## Core Swedish Output Principle

> Atlas kan senare tala svenska, men det får inte låta som att det ger
> investeringsrådgivning, uppmanar till handling, lovar utfall eller ersätter
> användarens omdöme.

In English:

> Atlas may later speak Swedish, but it must not sound like it is giving
> investment advice, urging action, promising outcomes, or replacing the
> user's judgment.

Additionally:

> Internal schemas, enums, status values, warning codes, file paths, and
> CLI flags remain canonical English regardless of output language.

---

## Prohibited Swedish Language Categories

The following categories of Swedish phrasing are prohibited in Atlas-generated
output. Prohibited examples are contained within this section only and are
clearly marked. They must not appear in tests, renderer strings, or constants.

### Category 1 — Direct Recommendation Language

Atlas must not produce Swedish text that functions as a direct investment
recommendation. This includes imperative forms ("köp", "sälj") or explicit
evaluative verdicts ("ett utmärkt köp", "starkt rekommenderat").

> **Prohibited examples (guardrail context only):**
> — "Köp nu"
> — "Sälj omedelbart"
> — "Starkt rekommenderat köp"
> — "Vi rekommenderar att du köper"

### Category 2 — Transaction and Execution Language

Atlas must not instruct the user to execute a financial transaction. This
includes phrasing that implies a specific immediate action in a portfolio.

> **Prohibited examples (guardrail context only):**
> — "Öppna en position"
> — "Öka din exponering"
> — "Minska innehavet"

### Category 3 — Price-Target Framing

Atlas must not state or imply a target price, expected price level, or
valuation conclusion for any security.

> **Prohibited examples (guardrail context only):**
> — "Kursmål: 450 kr"
> — "Förväntas stiga till"
> — "Uppsida till X"

### Category 4 — Urgency Language

Atlas must not create a sense of time pressure or urgency around a decision.

> **Prohibited examples (guardrail context only):**
> — "Agera nu"
> — "Missar du tillfället"
> — "Innan det är för sent"

### Category 5 — Certainty and Promise Language

Atlas must not express certainty about future performance or promise outcomes.

> **Prohibited examples (guardrail context only):**
> — "Garanterat"
> — "Kommer att stiga"
> — "Riskfritt"
> — "Säker avkastning"

### Category 6 — Outperformance Prediction Language

Atlas must not predict that a security will outperform a benchmark, sector,
or peer group.

> **Prohibited examples (guardrail context only):**
> — "Kommer att slå index"
> — "Bättre än marknaden"
> — "Överträffar sektorn"

### Category 7 — Personalized Financial Advice Framing

Atlas must not frame output as personalized advice tailored to the user's
specific financial situation.

> **Prohibited examples (guardrail context only):**
> — "Baserat på din situation rekommenderar vi"
> — "Det bästa valet för dig"
> — "Finansiell rådgivning"

---

## Safe Swedish Alternatives

The following are the approved Swedish equivalents for Atlas safe-language
concepts. These are the only Swedish terms that may appear in Atlas-generated
display text for the corresponding concepts.

| English (canonical) | Swedish (safe equivalent) |
|---------------------|--------------------------|
| Needs More Evidence | Kräver mer underlag |
| Continue Research | Fortsätt undersöka |
| Watchlist | Bevakningslista |
| Suitable for Further Review | Lämplig för vidare granskning |
| Not Suitable Under Current Constraints | Inte lämplig under nuvarande ramar |
| Decision Deferred | Beslut uppskjutet |
| No Action Warranted | Ingen åtgärd motiverad |
| Reason to Wait | Skäl att avvakta |
| Evidence Gap | Underlagslucka |
| Risk to Monitor | Risk att följa |
| Assumption to Recheck | Antagande att kontrollera igen |
| Aging Note | Äldre notering |
| Thesis Refresh | Tesuppdatering |
| Safety Boundary | Säkerhetsgräns |
| Input Status | Indatastatus |
| Input Warnings | Indatavarningar |
| Missing Optional Input | Saknat valfritt indata |
| Review date | Granskningsdatum |
| Investor profile | Investerarprofil |
| Decision journal | Beslutsjournal |
| Company facts | Företagsfakta |
| Financial history | Finansiell historik |
| Research notes | Analysnotisar |
| Portfolio | Portfölj |
| Watchlist | Bevakningslista |
| Available | Tillgänglig |
| Not provided | Inte angivet |
| Warnings | Varningar |

---

## Atlas Concept Mapping: English to Swedish

This table maps Atlas conceptual terms — used in section headings, labels,
and explanatory text — to their Swedish equivalents for future renderer use.

| Atlas concept | English display | Swedish display |
|---------------|----------------|----------------|
| Weekly review title | Atlas Weekly Investment Review | Atlas Veckovis Investeringsöversikt |
| Section 1 | 1. Review Scope | 1. Granskningsomfattning |
| Section 2 | 2. Portfolio Context | 2. Portföljkontext |
| Section 3 | 3. Watchlist Review | 3. Bevakningslistegranskning |
| Section 4 | 4. Company Reviews Needing Attention | 4. Bolagsanalyser som behöver uppmärksamhet |
| Section 5 | 5. Portfolio Fit and Suitability Notes | 5. Portföljpassning och lämplighetsnoteringar |
| Section 6 | 6. Risk and Principle Guardrails | 6. Risk- och principgränser |
| Section 7 | 7. Open Decisions | 7. Öppna beslut |
| Section 8 | 8. Missing Evidence | 8. Saknat underlag |
| Section 9 | 9. Follow-Up Questions | 9. Uppföljningsfrågor |
| Section 10 | 10. Non-Actions / Reasons to Wait | 10. Icke-åtgärder / Skäl att avvakta |
| Disclaimer line 1 | Atlas Weekly Investment Review — deterministic, local-only, no recommendations. | Atlas Veckovis Investeringsöversikt — deterministisk, lokal, utan rekommendationer. |
| Disclaimer line 2 | Atlas supports better judgment. It does not replace it. | Atlas stöder bättre omdöme. Det ersätter det inte. |
| Snapshot validation | Snapshot Draft Validation | Utkastkontroll |
| Snapshot review | Snapshot Draft Review | Utkastgranskning |
| Snapshot confirmation | Snapshot Draft Confirmation | Utkastbekräftelse |
| Snapshot rejection | Snapshot Draft Rejection | Utkastavvisning |
| Research notes export | Research Notes Export | Export av analysnotisar |
| Company facts export | Company Facts Export | Export av företagsfakta |

---

## Swedish Weekly Review Style Rules

These rules apply to all Atlas-generated Swedish text in the Weekly Review.
They do not apply to user-provided content.

1. **Use neutral analytical language.** Prefer "kan vara värt att granska"
   ("may be worth reviewing") over directive phrasing.

2. **Prefer absence framing over action commands.** Use "underlaget saknas"
   ("evidence is missing") rather than "samla in mer underlag" ("collect more evidence").

3. **Use waiting semantics, not urgency.** Use "skäl att avvakta" ("reason to wait")
   not "bråttom att agera" ("urgent to act").

4. **Preserve the 10-section structure.** Section count, section order, and section
   content logic do not change with locale.

5. **Preserve safe-concept semantics.** "Ingen åtgärd motiverad" must carry the
   same meaning as "No Action Warranted" — a reasoned non-action, not a missed
   opportunity.

6. **Preserve ticker symbols.** `MSFT`, `AAPL`, `ASML`, etc. remain as-is in
   Swedish output. They are not translated.

7. **Preserve user-provided research notes.** Swedish users' own notes are not
   rewritten or translated. Atlas-generated framing may surround them in Swedish,
   but the note content itself is kept as-is.

8. **Do not translate schema values or status values.** `confirmed`, `rejected`,
   `needs_user_review`, `research_notes_snapshot`, etc. remain canonical English
   in all files.

9. **Do not produce price commentary.** No Swedish section should contain phrasing
   that implies a price assessment ("är billig", "är dyr", "handlas till rabatt").

10. **Do not produce forward-looking certainty.** Section 10 in Swedish must not
    use certainty framing ("kommer att", "garanterat", "säkert"). Prefer
    "baserat på tillgängligt underlag" ("based on available evidence").

---

## Swedish Snapshot CLI Style Rules

These rules apply to Atlas-generated Swedish text in Snapshot CLI output.

1. **Snapshot status values remain canonical English internally.** `confirmed`,
   `rejected`, `needs_user_review`, `draft` do not change. Swedish display
   labels may surround them.

2. **Exportability explanations must remain cautious and procedural.**
   "Bekräftade utkast kan exporteras" is acceptable. "Exportera nu för bästa
   resultat" is not.

3. **Confirmed/rejected language must describe draft state, not investment judgment.**
   A confirmed snapshot means the user has reviewed it — not that the investment
   thesis is valid.

4. **Safety boundary text must remain explicit.** The "Safety Boundary" block must
   appear in Swedish output as "Säkerhetsgräns" with equivalent factual content:
   no files modified, no data written beyond what was stated.

5. **Error messages must state what happened.** Swedish error messages should
   describe the technical outcome ("Filen kunde inte läsas"), not prescribe a
   financial response ("Investera inte förrän").

6. **Research notes content is not translated.** The research notes content in a
   confirmed Snapshot is user-authored; Atlas does not translate it on export.

---

## User-Provided Swedish Content

Swedish users may write research notes, scope notes, decision journal entries,
investor profiles, and pasted source text in Swedish. This content must be
preserved exactly as provided.

Atlas-generated Swedish headings and labels may surround user-provided content
in future locale=sv output, but:

- Research notes are not rewritten or translated
- Scope notes are not rewritten or translated
- Extracted fields from pasted content are not reformulated
- Journal entries are not reformulated
- Investor profile field values are not translated
- Ticker symbols and company names are not translated

The Atlas rendering boundary for Swedish is between Atlas-generated structural
text (headings, labels, disclaimers, status messages) and user-provided content.
Only the Atlas-generated layer is in scope for localization.

---

## Guardrail-Sensitive Swedish Phrases

The following Swedish phrases are explicitly guardrail-sensitive. A future
Swedish renderer must never produce these in Atlas-generated text (outside
this document's guardrail context section above).

| Phrase category | Notes |
|----------------|-------|
| Imperative buy/sell forms | Prohibited under Category 1 |
| Price-target expressions | Prohibited under Category 3 |
| Urgency time-pressure phrases | Prohibited under Category 4 |
| Certainty-of-outcome expressions | Prohibited under Category 5 |
| Outperformance predictions | Prohibited under Category 6 |
| Personalised advice framing | Prohibited under Category 7 |

Tests for a Swedish renderer must scan generated output for these categories
before `sv` can be enabled. The scan must be equivalent to the English
forbidden-language scan already present in the test suite.

---

## Testing Requirements Before sv Can Be Enabled

The following tests must exist and pass before `atlas/locale_support.py` may
add `"sv"` to its supported set:

1. **Swedish heading output tests** — each Weekly Review section title in Swedish
   matches the approved mapping in this document.

2. **Swedish label output tests** — each repeated label (`Underlagslucka`,
   `Risk att följa`, etc.) appears correctly in Swedish Weekly Review output.

3. **Swedish disclaimer output test** — Swedish disclaimer text matches the
   approved mapping and contains no prohibited phrasing.

4. **Swedish Snapshot heading tests** — each Snapshot CLI heading in Swedish
   matches the approved mapping.

5. **Swedish safety boundary text test** — `Säkerhetsgräns` block appears with
   equivalent factual content in Swedish Snapshot output.

6. **Swedish forbidden-category scan** — generated Swedish output does not contain
   phrasing from any of the 7 prohibited categories defined in this document.

7. **Canonical value preservation tests** — enum values, schema keys, status
   values, warning codes, and ticker symbols remain English in Swedish-locale output.

8. **User-provided content passthrough tests** — research notes, scope notes, and
   journal entries are not modified in Swedish-locale output.

9. **Unsupported locale regression test** — after `sv` is enabled,
   `ensure_supported_locale("fr")` still raises until French is also enabled.

10. **CLI passthrough test** — Swedish output is accessible via direct Python API
    only; `--language` is not added to the CLI.

**Sprint 247 does not enable `sv`. All tests listed here are future requirements.**

---

## Remaining Gaps

The following are not addressed in Sprint 247:

- French guardrail list (Sprint 248 recommendation)
- Swedish renderer implementation (future, after guardrail tests exist)
- Swedish user-facing usage guide
- Swedish investor profile field labels
- Swedish company facts field labels
- Formal Swedish financial language review (not an Atlas responsibility;
  users are responsible for their own jurisdictional compliance)

---

## Recommended Next Step

**Sprint 248:** Create French safe-language guardrail list — apply the same
guardrail specification pattern to French, completing the initial safety
groundwork for the two planned non-English output languages before any
localization behavior is enabled.
