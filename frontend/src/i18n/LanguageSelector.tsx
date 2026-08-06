import { Button } from "../foundation";
import { useTranslation, type Language } from "./LanguageContext";

const OPTIONS: ReadonlyArray<{ code: Language; label: string }> = [
  { code: "sv", label: "🇸🇪 Svenska" },
  { code: "en", label: "🇬🇧 English" },
];

/**
 * Global language selector (Header, top-right per the design brief).
 * Visual Polish Sprint 1: now built on the Foundation `Button` component
 * (per this sprint's "prefer extending existing shared components"
 * rule) instead of bare `<button>` elements — same behavior (the active
 * language renders `disabled`, exactly as before), just the shared
 * button treatment instead of an unstyled native control.
 */
export function LanguageSelector() {
  const { language, setLanguage, t } = useTranslation();

  return (
    <div
      role="group"
      aria-label={t("shell.header.languageAriaLabel")}
      style={{ display: "flex", gap: "var(--space-metadata)" }}
    >
      {OPTIONS.map((option) => (
        <Button
          key={option.code}
          type="button"
          variant={language === option.code ? "primary" : "tertiary"}
          aria-pressed={language === option.code}
          disabled={language === option.code}
          onClick={() => setLanguage(option.code)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  );
}
