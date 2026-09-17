import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { renderWithProviders } from "../testUtils";
import { CaseChapter, useCaseChapterDeepLink } from "./CaseChapter";
import { CaseChapterNav } from "./CaseChapterNav";
import { CASE_CHAPTER_IDS, type CaseChapterId } from "./caseChapters";
import { en } from "../i18n/translations/en";

const t = ((key: string, params?: Record<string, string | number>) => {
  const value = (en as Record<string, string>)[key] ?? key;
  return params
    ? value.replace(/\{\{(\w+)\}\}/g, (_, name: string) => String(params[name] ?? ""))
    : value;
}) as never;

/**
 * Product Convergence Sprint 1 (Investment Case Hierarchy) -- deep-link
 * behaviour, exercised rather than asserted from source.
 *
 * jsdom implements neither layout nor `scrollIntoView`, so the thing
 * under test is what the hook *does* to the right element: it has to
 * find the chapter by id and move focus to it. Focus is not a proxy for
 * scrolling here -- it is the half of the behaviour that actually
 * matters for a keyboard or screen-reader user, and the half a silent
 * regression would take away.
 */

/** A page that renders its chapters only after "loading" completes,
 * mirroring the real page: the fragment is present from the first
 * render, the chapters are not. */
function FakeCasePage({
  chapters = CASE_CHAPTER_IDS,
  ready: initialReady = false,
}: {
  chapters?: readonly CaseChapterId[];
  ready?: boolean;
}) {
  const [ready, setReady] = useState(initialReady);
  useCaseChapterDeepLink(ready);
  return (
    <div>
      <button onClick={() => setReady(true)}>load</button>
      <CaseChapterNav t={t} />
      {ready &&
        chapters.map((id) => (
          <CaseChapter key={id} id={id} t={t}>
            <p>{`body of ${id}`}</p>
          </CaseChapter>
        ))}
    </div>
  );
}

describe("Investment Case deep links", () => {
  it("reaches the named chapter after the case has finished loading", async () => {
    const user = userEvent.setup();
    renderWithProviders(<FakeCasePage />, { route: "/investment-case/abc#risk" });

    // Nothing to reach yet: the case is still loading.
    expect(document.getElementById("risk")).toBeNull();

    await user.click(screen.getByText("load"));

    const risk = document.getElementById("risk");
    expect(risk).not.toBeNull();
    expect(document.activeElement).toBe(risk);
  });

  it("reaches a chapter that is already rendered on arrival", () => {
    renderWithProviders(<FakeCasePage ready />, { route: "/investment-case/abc#valuation" });
    expect(document.activeElement).toBe(document.getElementById("valuation"));
  });

  it("reaches every chapter this sprint promised", () => {
    for (const id of CASE_CHAPTER_IDS) {
      const { unmount } = renderWithProviders(<FakeCasePage ready />, {
        route: `/investment-case/abc#${id}`,
      });
      expect(document.activeElement, `#${id} should be reachable`).toBe(document.getElementById(id));
      unmount();
    }
  });

  it("degrades safely when the fragment names no chapter", () => {
    renderWithProviders(<FakeCasePage ready />, { route: "/investment-case/abc#not-a-chapter" });
    // Focus stays where the browser left it; nothing throws, and the
    // reader gets the ordinary top-of-page view.
    expect(document.activeElement).toBe(document.body);
  });

  it("degrades safely when the chapter is not on the page for this case", () => {
    renderWithProviders(<FakeCasePage ready chapters={["conclusion", "evidence"]} />, {
      route: "/investment-case/abc#valuation",
    });
    expect(document.getElementById("valuation")).toBeNull();
    expect(document.activeElement).toBe(document.body);
  });

  it("does not drag the reader back to the anchor on a later re-render", async () => {
    const user = userEvent.setup();
    renderWithProviders(<FakeCasePage />, { route: "/investment-case/abc#company" });
    await user.click(screen.getByText("load"));
    expect(document.activeElement).toBe(document.getElementById("company"));

    // The reader moves on; a re-render must not yank them back.
    const loadButton = screen.getByText("load");
    loadButton.focus();
    await user.click(loadButton);
    expect(document.activeElement).toBe(loadButton);
  });
});

describe("Investment Case chapter navigation", () => {
  it("offers a link to every chapter but the conclusion", () => {
    renderWithProviders(<CaseChapterNav t={t} />, { route: "/investment-case/abc" });
    const nav = screen.getByRole("navigation");
    const hrefs = [...nav.querySelectorAll("a")].map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual([
      "#company",
      "#strategy",
      "#forward-view",
      "#valuation",
      "#risk",
      "#portfolio-fit",
      "#evidence",
    ]);
  });

  it("names chapters in the reader's own language", () => {
    renderWithProviders(<CaseChapterNav t={t} />, { route: "/investment-case/abc" });
    expect(screen.getByRole("link", { name: "Risk" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Portfolio fit" })).toBeTruthy();

    // The anchors themselves are language-independent: switching
    // language changes the labels, never the destinations, so a link
    // shared from a Swedish session opens the same chapter in English.
    const swedish = ((key: string) =>
      (
        {
          "investmentCase.chapter.risk": "Risk",
          "investmentCase.chapter.portfolioFit": "Portföljpassform",
          "investmentCase.chapterNav.label": "Kapitel i det här caset",
        } as Record<string, string>
      )[key] ?? key) as never;
    const { container } = renderWithProviders(<CaseChapterNav t={swedish} chapters={["risk", "portfolio-fit"]} />, {
      route: "/investment-case/abc",
    });
    const hrefs = [...container.querySelectorAll("a")].map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual(["#risk", "#portfolio-fit"]);
    expect(container.textContent).toContain("Portföljpassform");
  });
});

describe("Investment Case chapter section", () => {
  it("is an addressable, focusable, labelled landmark", () => {
    const { container } = renderWithProviders(
      <CaseChapter id="risk" t={t}>
        <p>body</p>
      </CaseChapter>,
      { route: "/investment-case/abc" },
    );
    const section = container.querySelector("section");
    expect(section?.id).toBe("risk");
    expect(section?.getAttribute("tabindex")).toBe("-1");
    // Labelled by its own heading, so a screen reader announces which
    // chapter the deep link landed in.
    const heading = screen.getByRole("heading", { level: 2, name: "Risk" });
    expect(section?.getAttribute("aria-labelledby")).toBe(heading.id);
  });

  it("still renders when the chapter has nothing to say", () => {
    // The destination must survive an empty chapter: an inbound link
    // from Portfolio has to keep working for a company Atlas knows
    // little about.
    const { container } = renderWithProviders(
      <CaseChapter id="strategy" t={t}>
        {null}
      </CaseChapter>,
      { route: "/investment-case/abc" },
    );
    expect(container.querySelector("section")?.id).toBe("strategy");
  });
});
