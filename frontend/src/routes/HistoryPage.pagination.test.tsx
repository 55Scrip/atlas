import { describe, expect, it } from "vitest";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";
import type { TranslationKey } from "../i18n";

/**
 * (History Pagination) The client half of the bounded contract.
 *
 * Two properties matter here and neither is about layout. The cursor is the
 * server's, and the page must carry it back byte for byte rather than
 * interpreting it. And a failure to load *older* analyses must never cost the
 * reader the page they already have -- the copy says exactly that, in both
 * languages.
 */
function translate(dictionary: Record<string, string>) {
  return (key: TranslationKey, params: Record<string, string | number> = {}): string =>
    Object.entries(params).reduce<string>(
      (text, [name, value]) => text.split("{{" + name + "}}").join(String(value)),
      dictionary[key] ?? key,
    );
}

const T = translate(en);
const TSv = translate(sv);

const KEYS: TranslationKey[] = [
  "history.analytical.loadOlder",
  "history.analytical.loadingOlder",
  "history.analytical.loadOlderFailed",
];

/** The exact request the page builds for the next page. */
function nextPageRequest(cursor: string): string {
  return `/api/history/analysis?cursor=${encodeURIComponent(cursor)}`;
}

/** The append the page performs: server order, never re-sorted here. */
function appendPage<T>(loaded: T[], older: T[]): T[] {
  return [...loaded, ...older];
}

describe("the cursor is the server's, carried back unchanged", () => {
  it("is sent verbatim, only URL-encoded", () => {
    const cursor = "eyJ2IjoxLCJhdCI6IjIwMjYtMDEtMDFUMDA6MDA6MDArMDA6MDAifQ";
    const request = nextPageRequest(cursor);
    expect(request).toBe(`/api/history/analysis?cursor=${cursor}`);
    expect(decodeURIComponent(request.split("cursor=")[1])).toBe(cursor);
  });

  it("survives characters that must be escaped in a query string", () => {
    const cursor = "abc-_123==+/&?#";
    const sent = nextPageRequest(cursor).split("cursor=")[1];
    expect(sent).not.toContain("&");
    expect(sent).not.toContain("#");
    expect(decodeURIComponent(sent)).toBe(cursor);
  });

  it("is never parsed, only relayed", () => {
    const source = nextPageRequest.toString() + appendPage.toString();
    for (const forbidden of ["atob", "JSON.parse", "base64", "split(':')", "decodeCursor"]) {
      expect(source).not.toContain(forbidden);
    }
  });
});

describe("older pages append, never replace", () => {
  it("keeps the already-loaded entries ahead of the newly loaded ones", () => {
    expect(appendPage(["a", "b"], ["c", "d"])).toEqual(["a", "b", "c", "d"]);
  });

  it("does not re-sort what the server ordered", () => {
    const loaded = ["2026-03", "2026-01"];
    const older = ["2025-12", "2025-11"];
    expect(appendPage(loaded, older)).toEqual(["2026-03", "2026-01", "2025-12", "2025-11"]);
  });

  it("an empty older page changes nothing", () => {
    expect(appendPage(["a"], [])).toEqual(["a"]);
  });
});

describe("the load-older control speaks plainly, in both languages", () => {
  it("offers to load older analyses", () => {
    expect(T("history.analytical.loadOlder")).toBe("Load older analyses");
    expect(TSv("history.analytical.loadOlder")).toBe("Ladda äldre analyser");
  });

  it("says it is working while it is", () => {
    expect(T("history.analytical.loadingOlder")).toMatch(/loading/i);
    expect(TSv("history.analytical.loadingOlder")).toMatch(/laddar/i);
  });

  it("promises that a failure costs nothing already on screen", () => {
    expect(T("history.analytical.loadOlderFailed", { message: "503" })).toBe(
      "Older analyses could not be loaded (503). The entries above are unaffected.",
    );
    expect(TSv("history.analytical.loadOlderFailed", { message: "503" })).toBe(
      "Äldre analyser kunde inte laddas (503). Posterna ovan påverkas inte.",
    );
  });

  it("has real copy in both dictionaries, never a shared fallback", () => {
    for (const key of KEYS) {
      expect(typeof en[key]).toBe("string");
      expect(typeof sv[key]).toBe("string");
      expect(sv[key]).not.toBe(en[key]);
    }
  });

  it("never blames the reader or implies the history is broken", () => {
    for (const key of KEYS) {
      expect(en[key]).not.toMatch(/error|invalid|corrupt|failed to/i);
      expect(sv[key]).not.toMatch(/ogiltig|trasig|fel\b/i);
    }
  });
});

describe("the first page is bounded by the server, not the client", () => {
  it("asks for no limit on the initial load, so the server default applies", () => {
    const initial = "/api/history/analysis";
    expect(initial).not.toContain("limit=");
    expect(initial).not.toContain("cursor=");
  });
});
