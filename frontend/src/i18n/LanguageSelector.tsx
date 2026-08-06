import { useTranslation, type Language } from "./LanguageContext";

const OPTIONS: ReadonlyArray<{ code: Language; label: string }> = [
  { code: "sv", label: "🇸🇪 Svenska" },
  { code: "en", label: "🇬🇧 English" },
];

/**
 * Global language selector (Header, top-right per the design brief).
 * Plain native buttons, matching `Navigation.tsx`'s own precedent of
 * shell wiring using bare elements rather than the Foundation component
 * library — this region has no visual design yet either.
 */
export function LanguageSelector() {
  const { language, setLanguage, t } = useTranslation();

  return (
    <div role="group" aria-label={t("shell.header.languageAriaLabel")}>
      {OPTIONS.map((option) => (
        <button
          key={option.code}
          type="button"
          aria-pressed={language === option.code}
          disabled={language === option.code}
          onClick={() => setLanguage(option.code)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
