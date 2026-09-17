import { ACCENT_LINK_STYLE, Inline, Stack, VisuallyHidden } from "../foundation";
import type { TranslationKey } from "../i18n";
import {
  CASE_CHAPTER_LABEL_KEY,
  CASE_CHAPTER_NAV_IDS,
  caseChapterHref,
  type CaseChapterId,
} from "./caseChapters";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * The Investment Case's chapter index -- one link per semantic
 * chapter, in the page's own reading order.
 *
 * Plain `<a href="#chapter">` links inside a `<nav>`, deliberately, not
 * buttons with scroll handlers: the browser already scrolls, already
 * moves focus to a `tabIndex={-1}` target, already updates the address
 * bar to a URL the reader can copy, share or reload, and already
 * supports opening a chapter in a new tab. The page's own deep-link
 * effect covers the one case the browser cannot: a fragment that
 * arrives before the case has finished loading.
 *
 * Labels are chapter names, not statuses. Whether a chapter has
 * anything to say is the chapter's business; hiding a link for an
 * empty chapter would make navigation shift underneath the reader
 * from company to company, and would quietly contradict the inbound
 * deep links other Atlas surfaces are meant to be able to make.
 */
export function CaseChapterNav({
  t,
  chapters = CASE_CHAPTER_NAV_IDS,
}: {
  t: Translate;
  chapters?: readonly CaseChapterId[];
}) {
  return (
    <Stack gap="metadata">
      <nav aria-label={t("investmentCase.chapterNav.label")}>
        <VisuallyHidden>{t("investmentCase.chapterNav.label")}</VisuallyHidden>
        <Inline gap="row" wrap>
          {chapters.map((id) => (
            <a key={id} href={caseChapterHref(id)} style={ACCENT_LINK_STYLE}>
              {t(CASE_CHAPTER_LABEL_KEY[id])}
            </a>
          ))}
        </Inline>
      </nav>
    </Stack>
  );
}
