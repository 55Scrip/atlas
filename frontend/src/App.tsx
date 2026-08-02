import { Route, Routes } from "react-router-dom";
import { DashboardPage } from "./routes/DashboardPage";
import { DecisionWorkspacePage } from "./routes/DecisionWorkspacePage";
import { InvestmentCasePage } from "./routes/InvestmentCasePage";
import { PlatformStatusPage } from "./routes/PlatformStatusPage";
import { AppShell } from "./shell/AppShell";
import { NotFoundPage } from "./shell/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<PlatformStatusPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="investment-case" element={<InvestmentCasePage />} />
        <Route path="investment-case/:caseId" element={<InvestmentCasePage />} />
        <Route path="decision-workspace" element={<DecisionWorkspacePage />} />
        <Route path="decision-workspace/:caseId" element={<DecisionWorkspacePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
