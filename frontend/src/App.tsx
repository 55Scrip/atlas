import { Route, Routes } from "react-router-dom";
import { DashboardPage } from "./routes/DashboardPage";
import { IndexRoute } from "./routes/IndexRoute";
import { InvestmentCasePage } from "./routes/InvestmentCasePage";
import { PlatformStatusPage } from "./routes/PlatformStatusPage";
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
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="investment-case" element={<InvestmentCasePage />} />
        <Route path="investment-case/:caseId" element={<InvestmentCasePage />} />
        <Route path="platform-status" element={<PlatformStatusPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
