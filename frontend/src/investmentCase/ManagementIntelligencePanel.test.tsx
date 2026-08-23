import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { ManagementIntelligencePanel } from "./ManagementIntelligencePanel";
import type {
  ExecutiveChangeIntelligenceView,
  ExecutiveCompensationIntelligenceView,
  ExecutiveTrackRecordIntelligenceView,
  GovernanceIntelligenceView,
  InsiderAlignmentIntelligenceView,
  OwnershipIntelligenceView,
  RegulatoryFilingView,
} from "./managementIntelligenceApi";

const EMPTY_EXECUTIVE_CHANGE: ExecutiveChangeIntelligenceView = { executives: [], leadershipChanges: [] };
const EMPTY_TRACK_RECORD: ExecutiveTrackRecordIntelligenceView = { tenures: [] };
const EMPTY_GOVERNANCE: GovernanceIntelligenceView = {
  boardComposition: { chairDisclosed: false, leadIndependentDirectorDisclosed: false, directors: [] },
  committees: [],
  votingStructure: { dualClassDisclosed: false, controlledCompanyDisclosed: false, shareClassCount: 0 },
  changeCount: 0,
  observationCount: 0,
  filingsConsidered: [],
};
const EMPTY_OWNERSHIP: OwnershipIntelligenceView = { disclosures: [], changes: [], filingsConsidered: [] };
const EMPTY_COMPENSATION: ExecutiveCompensationIntelligenceView = { records: [], changes: [], filingsConsidered: [] };
const EMPTY_ALIGNMENT: InsiderAlignmentIntelligenceView = { profiles: [], filingsConsidered: [] };

function Harness(props: {
  regulatoryFilings?: RegulatoryFilingView[];
  executiveChange?: ExecutiveChangeIntelligenceView;
  trackRecord?: ExecutiveTrackRecordIntelligenceView;
  governance?: GovernanceIntelligenceView;
  ownership?: OwnershipIntelligenceView;
  executiveCompensation?: ExecutiveCompensationIntelligenceView;
  insiderAlignment?: InsiderAlignmentIntelligenceView;
}) {
  const { t } = useTranslation();
  return (
    <ManagementIntelligencePanel
      regulatoryFilings={props.regulatoryFilings ?? []}
      executiveChange={props.executiveChange ?? EMPTY_EXECUTIVE_CHANGE}
      trackRecord={props.trackRecord ?? EMPTY_TRACK_RECORD}
      governance={props.governance ?? EMPTY_GOVERNANCE}
      ownership={props.ownership ?? EMPTY_OWNERSHIP}
      executiveCompensation={props.executiveCompensation ?? EMPTY_COMPENSATION}
      insiderAlignment={props.insiderAlignment ?? EMPTY_ALIGNMENT}
      t={t}
    />
  );
}

function renderPanel(props: Parameters<typeof Harness>[0] = {}) {
  return render(
    <LanguageProvider>
      <Harness {...props} />
    </LanguageProvider>,
  );
}

const AAPL_DEF14A: RegulatoryFilingView = {
  formType: "DEF 14A", filedAt: "2026-01-08T00:00:00Z", accessionNumber: "0001308179-26-000008",
  filingUrl: "https://example.test/def14a", periodOfReport: null,
};

describe("ManagementIntelligencePanel (Product Utilization Sprint 1)", () => {
  it("lists a real executive with a translated role label, never a raw enum token", () => {
    renderPanel({
      executiveChange: {
        executives: [
          {
            name: "Tim Cook", roleCategory: "ceo", rawTitle: "Chief Executive Officer", company: "AAPL",
            isInterim: false, firstObservedDate: "2020-01-01", lastObservedDate: "2026-01-01",
            sourceTranscripts: ["Q1 2026"], statementCount: 3,
          },
        ],
        leadershipChanges: [],
      },
    });
    expect(screen.getByText("Tim Cook")).toBeInTheDocument();
    expect(screen.getByText("VD")).toBeInTheDocument();
    expect(screen.queryByText("ceo")).not.toBeInTheDocument();
  });

  it("marks an interim executive distinctly", () => {
    renderPanel({
      executiveChange: {
        executives: [
          {
            name: "Jane Smith", roleCategory: "cfo", rawTitle: "Interim CFO", company: "AAPL", isInterim: true,
            firstObservedDate: "2025-01-01", lastObservedDate: "2026-01-01", sourceTranscripts: ["Q4 2025"], statementCount: 1,
          },
        ],
        leadershipChanges: [],
      },
    });
    expect(screen.getByText("Tillförordnad")).toBeInTheDocument();
  });

  it("distinguishes 'content not yet acquired' from 'no relevant filing known', for every filing-content-gated sub-section", () => {
    const { unmount } = renderPanel({ regulatoryFilings: [AAPL_DEF14A] });
    // A DEF 14A is relevant to all four filing-content-gated
    // sub-sections (Alignment, Governance, Ownership, Compensation) --
    // all four render the same honest message, not a bug.
    expect(screen.getAllByText(/Atlas har identifierat en relevant rapport/).length).toBe(4);
    unmount();

    renderPanel({ regulatoryFilings: [] });
    expect(screen.getAllByText(/Atlas har ännu inte identifierat någon relevant rapport/).length).toBe(4);
  });

  it("shows a real ownership disclosure's own disclosed figures, behind a real expand control with the right count", () => {
    renderPanel({
      ownership: {
        disclosures: [
          {
            ownerName: "Tim Cook", categories: ["executive_officer"], disclosedPercentage: "*",
            disclosedShareCount: "3,280,295", accessionNumber: "0001308179-26-000008", filedAt: "2026-01-08T00:00:00Z",
          },
        ],
        changes: [],
        filingsConsidered: ["0001308179-26-000008"],
      },
    });
    const summary = screen.getByText(/1 ägaruppgift/);
    expect(summary.closest("details")).not.toBeNull();
    expect(summary.closest("details")).toContainElement(screen.getByText(/3,280,295/));
  });

  it("shows an insider alignment observation using its own translated label", () => {
    renderPanel({
      insiderAlignment: {
        profiles: [
          {
            executive: {
              name: "Tim Cook", roleCategory: "ceo", rawTitle: null, company: "AAPL", isInterim: false,
              firstObservedDate: "2020-01-01", lastObservedDate: "2026-01-01", sourceTranscripts: [], statementCount: 0,
            },
            ownership: { holdingCount: 1, trend: "insufficient_history" },
            equityCompensation: { hasEquityAwards: false, equityIncentiveKinds: [], hasCashCompensation: false, disclosedComponents: [] },
            observations: [{ kind: "executive_owns_stock", executiveName: "Tim Cook", accessionNumber: null, filedAt: null }],
          },
        ],
        filingsConsidered: ["0001308179-26-000008"],
      },
    });
    expect(screen.getByText("Äger aktier i bolaget")).toBeInTheDocument();
  });

  it("never renders a raw snake_case observation kind when a translation exists", () => {
    renderPanel({
      insiderAlignment: {
        profiles: [
          {
            executive: {
              name: "Jane Smith", roleCategory: "cfo", rawTitle: null, company: "AAPL", isInterim: false,
              firstObservedDate: "2020-01-01", lastObservedDate: "2026-01-01", sourceTranscripts: [], statementCount: 0,
            },
            ownership: { holdingCount: 0, trend: "insufficient_history" },
            equityCompensation: { hasEquityAwards: false, equityIncentiveKinds: [], hasCashCompensation: false, disclosedComponents: [] },
            observations: [{ kind: "executive_has_no_disclosed_ownership", executiveName: "Jane Smith", accessionNumber: null, filedAt: null }],
          },
        ],
        filingsConsidered: [],
      },
    });
    expect(screen.queryByText("executive_has_no_disclosed_ownership")).not.toBeInTheDocument();
    expect(screen.getByText("Inget redovisat ägande")).toBeInTheDocument();
  });

  it("falls back to a humanized label for an unmapped committee kind, never a raw token", () => {
    renderPanel({
      governance: {
        ...EMPTY_GOVERNANCE,
        committees: [{ kind: "some_future_committee_kind", disclosedName: "Some Future Committee", members: [], chair: null }],
      },
    });
    expect(screen.getByText(/Some Future Committee Kind/)).toBeInTheDocument();
  });
});
