import { Route, Routes } from "react-router-dom";
import { DecisionWorkspacePage } from "./decisionWorkspace/DecisionWorkspacePage";
import { DraftCommitPage } from "./decisionWorkspace/DraftCommitPage";
import { CompanyWorkspacePage } from "./routes/CompanyWorkspacePage";
import { DailyBriefPage } from "./routes/DailyBriefPage";
import { DashboardPage } from "./routes/DashboardPage";
import { DiscoveryPage } from "./routes/DiscoveryPage";
import { CandidateDetailPage } from "./discovery/CandidateDetailPage";
import { CompareCandidatesPage } from "./discovery/CompareCandidatesPage";
import { HistoryPage } from "./routes/HistoryPage";
import { HoldingAttentionPage } from "./routes/HoldingAttentionPage";
import { IndexRoute } from "./routes/IndexRoute";
import { InvestmentCasePage } from "./routes/InvestmentCasePage";
import { PlatformStatusPage } from "./routes/PlatformStatusPage";
import { PortfolioImportPage } from "./routes/PortfolioImportPage";
import { PortfolioPage } from "./routes/PortfolioPage";
import { WatchlistPage } from "./routes/WatchlistPage";
import { WelcomePage } from "./routes/WelcomePage";
import { AppShell } from "./shell/AppShell";
import { NotFoundPage } from "./shell/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<IndexRoute />} />
        <Route path="welcome" element={<WelcomePage />} />
        <Route path="daily-brief" element={<DailyBriefPage />} />
        <Route path="discovery" element={<DiscoveryPage />} />
        <Route path="discovery/candidate/:ticker" element={<CandidateDetailPage />} />
        <Route path="discovery/compare" element={<CompareCandidatesPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="portfolio/import" element={<PortfolioImportPage />} />
        <Route path="portfolio/holding/:ticker" element={<HoldingAttentionPage />} />
        <Route path="watchlist" element={<WatchlistPage />} />
        <Route path="company/:ticker" element={<CompanyWorkspacePage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="investment-case" element={<InvestmentCasePage />} />
        <Route path="investment-case/:caseId" element={<InvestmentCasePage />} />
        <Route path="decisions/:decisionId/workspace" element={<DecisionWorkspacePage />} />
        <Route path="decision-drafts/:draftId/commit" element={<DraftCommitPage />} />
        <Route path="platform-status" element={<PlatformStatusPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
