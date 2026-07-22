import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ComponentsListPage } from "./routes/ComponentsListPage";
import { CostsPage } from "./routes/CostsPage";
import { ParametersPage } from "./routes/ParametersPage";
import { FFBPage } from "./routes/FFBPage";

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/components" replace />} />
        <Route path="/components" element={<ComponentsListPage />} />
        <Route path="/costs" element={<CostsPage />} />
        <Route path="/parameters" element={<ParametersPage />} />
        <Route path="/ffb" element={<FFBPage />} />
      </Route>
    </Routes>
  );
}

export default App;
