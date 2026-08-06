import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { en, type TranslationKey } from "./translations/en";
import { sv } from "./translations/sv";

/**
 * The two languages Atlas Alpha ships with. Adding a third is: write
 * `translations/xx.ts` typed as `Record<TranslationKey, string>` (the
 * compiler enforces every key is translated), add it to `DICTIONARIES`
 * below, and add one option to `LanguageSelector` — nothing else in the
 * application changes, because every screen already reads copy through
 * `t()` rather than holding its own strings.
 */
export type Language = "sv" | "en";

const DICTIONARIES: Record<Language, Record<TranslationKey, string>> = { en, sv };

const STORAGE_KEY = "atlas.language";

/**
 * Swedish is the default: Atlas Alpha's first investors are primarily
 * Swedish, and the product should feel native to them out of the box.
 * A returning visitor's own explicit choice (persisted below) always
 * wins over this default.
 */
const DEFAULT_LANGUAGE: Language = "sv";

function isLanguage(value: string | null): value is Language {
  return value === "sv" || value === "en";
}

function readStoredLanguage(): Language {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isLanguage(stored) ? stored : DEFAULT_LANGUAGE;
}

function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (match, name: string) =>
    Object.hasOwn(params, name) ? String(params[name]) : match,
  );
}

export interface LanguageContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  /**
   * Looks up `key` in the current language's dictionary and fills in any
   * `{{name}}` placeholders from `params`. This is for presentation-layer
   * copy only — never pass user-generated content (notes, journal
   * entries, thesis text) through this function; render it verbatim.
   */
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

/**
 * Exported (not just the hook) so `ErrorBoundary`, a class component,
 * can read it via `static contextType` — React hooks aren't available
 * there.
 */
export const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(readStoredLanguage);

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, next);
    }
  }, []);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) =>
      interpolate(DICTIONARIES[language][key], params),
    [language],
  );

  const value = useMemo<LanguageContextValue>(
    () => ({ language, setLanguage, t }),
    [language, setLanguage, t],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useTranslation(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useTranslation must be used within a LanguageProvider.");
  }
  return context;
}
