import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { EvidenceTimelinePanel } from "./EvidenceTimelinePanel";
import type { EvidenceHistoryView } from "./evidenceTimelineApi";

function Harness({ history }: { history: EvidenceHistoryView }) {
  const { t } = useTranslation();
  return <EvidenceTimelinePanel caseId="case-1" history={history} t={t} />;
}

function renderPanel(history: EvidenceHistoryView) {
  return render(
    <LanguageProvider>
      <Harness history={history} />
    </LanguageProvider>,
  );
}

const CURRENT = "2026-08-20T12:00:00Z";

describe("EvidenceTimelinePanel (Atlas Intelligence Sprint 5/6)", () => {
  it("shows the honest baseline note for a Case's first-ever recorded evidence", () => {
    renderPanel({ isBaseline: true, transitions: [], newSourceEvidence: [], previousCapturedAt: null, currentCapturedAt: CURRENT });
    expect(
      screen.getByText("Det här är första gången Atlas registrerade underlaget för det här caset — det finns ännu ingen historik att jämföra med."),
    ).toBeInTheDocument();
  });

  it("shows the honest no-change note when nothing changed since the last capture", () => {
    renderPanel({ isBaseline: false, transitions: [], newSourceEvidence: [], previousCapturedAt: CURRENT, currentCapturedAt: CURRENT });
    expect(screen.getByText("Inget i underlaget har ändrats sedan Atlas senast tittade.")).toBeInTheDocument();
  });

  it("renders the real, already-translated transition sentence, never a raw category token", () => {
    renderPanel({
      isBaseline: false,
      transitions: [
        { id: "t1", category: "stance_changed", direction: "negative", previousState: "maintain", currentState: "reduce", isMaterial: true },
      ],
      newSourceEvidence: [],
      previousCapturedAt: CURRENT,
      currentCapturedAt: CURRENT,
    });
    expect(screen.getByText("Atlas syn har försvagats.")).toBeInTheDocument();
    expect(screen.queryByText("stance_changed")).not.toBeInTheDocument();
  });

  it("labels the transition category using the shared, translated vocabulary", () => {
    renderPanel({
      isBaseline: false,
      transitions: [
        {
          id: "t1",
          category: "conflict_status_changed",
          direction: "positive",
          previousState: "conflicting",
          currentState: "consistent",
          isMaterial: true,
        },
      ],
      newSourceEvidence: [],
      previousCapturedAt: CURRENT,
      currentCapturedAt: CURRENT,
    });
    expect(screen.getByText("Samstämmighet")).toBeInTheDocument();
    expect(screen.getByText("En motsägelse i underlaget har lösts.")).toBeInTheDocument();
  });

  it("hides a non-material transition, showing an honest 'other changes recorded' note instead", () => {
    renderPanel({
      isBaseline: false,
      transitions: [
        {
          id: "t1",
          category: "confidence_changed",
          direction: "positive",
          previousState: "moderate",
          currentState: "high",
          isMaterial: false,
        },
      ],
      newSourceEvidence: [],
      previousCapturedAt: CURRENT,
      currentCapturedAt: CURRENT,
    });
    expect(screen.queryByText("Atlas tillförlitlighet i den här analysen har ökat.")).not.toBeInTheDocument();
    expect(screen.getByText("Atlas registrerade även andra, mindre betydelsefulla underlagsändringar — se fullständig historik.")).toBeInTheDocument();
  });

  it("renders a new Source Evidence event as a factual sentence, distinct from Analysis History", () => {
    renderPanel({
      isBaseline: false,
      transitions: [],
      newSourceEvidence: [{ factKind: "revenue", period: "FY2024" }],
      previousCapturedAt: CURRENT,
      currentCapturedAt: CURRENT,
    });
    expect(screen.getByText("Atlas har tagit emot nyare underlag för intäkter avseende FY2024.")).toBeInTheDocument();
  });

  it("caps the prominently shown Source Evidence events, folding the rest into an honest overflow note", () => {
    const manyEvents = Array.from({ length: 8 }, (_, i) => ({ factKind: "capital_expenditure", period: `FY${2010 + i}` }));
    renderPanel({
      isBaseline: false,
      transitions: [],
      newSourceEvidence: manyEvents,
      previousCapturedAt: CURRENT,
      currentCapturedAt: CURRENT,
    });
    expect(screen.getAllByText(/Atlas har tagit emot nyare underlag för investeringar/)).toHaveLength(3);
    expect(screen.getByText("5 till nya underlagsposter — se fullständig historik.")).toBeInTheDocument();
  });
});
