import { Navigate, Route, Routes } from "react-router-dom";
import Shell from "./console/Shell";
import Overview from "./console/Overview";
import Events from "./console/Events";
import EventDetail from "./console/EventDetail";
import Forecast from "./console/Forecast";
import Households from "./console/Households";
import Reports from "./console/Reports";
import Fleet from "./console/Fleet";
import Settings from "./console/Settings";
import DesignPage from "./pages/DesignPage";
import ServiceBlueprint from "./pages/ServiceBlueprint";
import OperatorApp from "./operator/OperatorApp";
import Messages from "./household/Messages";
import StatusPage from "./household/StatusPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Overview />} />
        <Route path="events" element={<Events />} />
        <Route path="events/:id" element={<EventDetail />} />
        <Route path="forecast" element={<Forecast />} />
        <Route path="households" element={<Households />} />
        <Route path="reports" element={<Reports />} />
        <Route path="fleet" element={<Fleet />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="design" element={<DesignPage />} />
      <Route path="design/service-blueprint" element={<ServiceBlueprint />} />
      <Route path="operator/*" element={<OperatorApp />} />
      <Route path="household/messages" element={<Messages />} />
      <Route path="household/status" element={<StatusPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
