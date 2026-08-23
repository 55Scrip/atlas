/**
 * Product Utilization Sprint 1. `snake_case` -> `Title Case`, for the
 * large, closed-but-numerous backend taxonomy enums this sprint
 * surfaces for the first time (risk category, legal-proceeding
 * category, owner category, committee kind, and the various change-
 * observation kinds) -- roughly forty distinct enum members across
 * six capabilities. Each disclosed member is real, closed vocabulary
 * (never free text), but giving every one of them its own translated
 * `TranslationKey` entry (English *and* accurate Swedish, per
 * `sv.ts`'s own `Record<TranslationKey, string>` completeness
 * guarantee) would be a large amount of translation work for
 * taxonomy labels a reader already parses correctly in English
 * ("cybersecurity," "antitrust," "regulatory investigation") --
 * category labels, not application chrome. Every *section heading*,
 * *role label*, and *status word* a user reads as part of the page's
 * own voice still goes through the full `t()` dictionary; only the
 * enum-value labels this function renders are handled this way, and
 * every call site says so.
 */
export function humanizeEnumValue(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
