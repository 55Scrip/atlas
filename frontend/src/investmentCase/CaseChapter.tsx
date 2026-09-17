import { useEffect, useRef, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { Heading, Inline, Stack, StatusBadge, Text, type StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { CASE_CHAPTER_LABEL_KEY, parseCaseChapterHash, type CaseChapterId } from "./caseChapters";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * One Investment Case chapter -- a real `<section>` carrying the
 * chapter id as its DOM id, so `#risk` is both an inbound deep-link
 * destination and an ordinary browser anchor.
 *
 * `tabIndex={-1}` makes the section programmatically focusable without
 * putting it in the tab order: arriving via a deep link moves keyboard
 * focus to the chapter rather than leaving it stranded at the top of
 * the document, which is what makes the link work for a keyboard or
 * screen-reader user and not only visually.
 *
 * A chapter renders whether or not it has content. The honest empty
 * state belongs to the chapter's body (each chapter says, in its own
 * words, what Atlas does not have); the destination itself must never
 * vanish, or an inbound link from Portfolio would silently land
 * somewhere else on the page.
 */
export function CaseChapter({
  id,
  t,
  status,
  statusTone = "neutral",
  headline,
  subheading,
  children,
}: {
  id: CaseChapterId;
  t: Translate;
  /**
   * Product Convergence Sprint 1B (Investment Case Compression) -- the
   * chapter's own conclusion, on the title row.
   *
   * A deep link from Portfolio lands here and the reader must learn the
   * chapter's answer immediately, without opening anything: `#risk`
   * arrives at "Risk — High", `#valuation` at "Valuation — Expensive".
   * It is always an existing engine status rendered through the same
   * translation maps the rest of the page uses, never a new judgment
   * computed for the heading.
   */
  status?: string | undefined;
  statusTone?: StatusTone;
  /** One line of "why", directly under the title. Kept to a sentence:
   * the detail belongs behind the chapter's own disclosure. */
  headline?: ReactNode;
  /** A quiet scope line, only where the chapter's limits change how its
   * conclusion should be read (Risk naming what it does not cover). */
  subheading?: string;
  children?: ReactNode;
}) {
  const headingId = `${id}-heading`;
  return (
    <section id={id} aria-labelledby={headingId} tabIndex={-1} style={{ scrollMarginTop: "var(--space-inter-section)" }}>
      <Stack gap="metadata">
        <Inline gap="row" align="center" wrap>
          <Heading level={2} id={headingId}>
            {t(CASE_CHAPTER_LABEL_KEY[id])}
          </Heading>
          {status && <StatusBadge label={status} tone={statusTone} />}
        </Inline>
        {headline && (
          <Text as="p" color="secondary">
            {headline}
          </Text>
        )}
        {subheading && (
          <Text as="p" color="tertiary">
            {subheading}
          </Text>
        )}
        {children}
      </Stack>
    </section>
  );
}

/**
 * Deep-link arrival.
 *
 * The Investment Case loads asynchronously, so the browser's own
 * fragment handling has already run and failed by the time a chapter
 * exists in the DOM -- a direct `/investment-case/<id>#risk` load would
 * otherwise land at the top of the page. This waits for the page to
 * report that its chapters are rendered, then scrolls and focuses the
 * chapter the fragment names.
 *
 * It keys off the chapter id, never DOM order or an index, so
 * reordering the page cannot break a link. An unknown fragment, or a
 * chapter that is genuinely not on the page for this case, resolves to
 * nothing happening at all -- the reader keeps the ordinary top-of-page
 * view instead of being moved somewhere arbitrary.
 *
 * `isReady` exists because "the element is in the DOM" is the real
 * precondition and the page is the only thing that knows it. Each
 * (fragment, ready) pair is handled once, so a later re-render does not
 * yank the reader back to the anchor while they are reading elsewhere;
 * clicking the same chapter in the in-page navigation again still
 * works, because that is the browser's own anchor behaviour, not this
 * effect's.
 */
export function useCaseChapterDeepLink(isReady: boolean): void {
  const { hash } = useLocation();
  const handled = useRef<string | null>(null);

  useEffect(() => {
    if (!isReady) return;
    const chapter = parseCaseChapterHash(hash);
    if (chapter === null) {
      handled.current = null;
      return;
    }
    if (handled.current === chapter) return;

    const element = document.getElementById(chapter);
    // Degrades safely: a chapter this case does not render is simply
    // not scrolled to. Nothing throws, nothing is invented.
    if (!element) return;

    handled.current = chapter;
    // jsdom has no layout and therefore no `scrollIntoView`; guarding
    // keeps the focus half of the arrival -- the half that matters to a
    // keyboard or screen-reader user -- working under test rather than
    // throwing before it runs.
    element.scrollIntoView?.({ block: "start" });
    element.focus({ preventScroll: true });
  }, [hash, isReady]);
}
