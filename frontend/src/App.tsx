import { Route, Routes } from "react-router-dom";
import { CompanyWorkspacePage } from "./routes/CompanyWorkspacePage";
import { DailyBriefPage } from "./routes/DailyBriefPage";
import { DashboardPage } from "./routes/DashboardPage";
import { DiscoveryPage } from "./routes/DiscoveryPage";
import { HistoryPage } from "./routes/HistoryPage";
import { HoldingAttentionPage } from "./routes/HoldingAttentionPage";
import { IndexRoute } from "./routes/IndexRoute";
import { InvestmentCasePage } from "./routes/InvestmentCasePage";
import { PlatformStatusPage } from "./routes/PlatformStatusPage";
import { PortfolioImportPage } from "./routes/PortfolioImportPage";
import { PortfolioPage } from "./routes/PortfolioPage";
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
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="portfolio/import" element={<PortfolioImportPage />} />
        <Route path="portfolio/holding/:ticker" element={<HoldingAttentionPage />} />
        <Route path="company/:ticker" element={<CompanyWorkspacePage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="investment-case" element={<InvestmentCasePage />} />
        <Route path="investment-case/:caseId" element={<InvestmentCasePage />} />
        <Route path="platform-status" element={<PlatformStatusPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
