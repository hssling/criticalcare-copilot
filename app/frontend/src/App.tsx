import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import NewCase from "./pages/NewCase";
import CaseSummary from "./pages/CaseSummary";
import MedicationSafety from "./pages/MedicationSafety";
import AlertConsole from "./pages/AlertConsole";
import AuditViewer from "./pages/AuditViewer";
import Settings from "./pages/Settings";
import DemoSamples from "./pages/DemoSamples";
import Disclaimer from "./components/Disclaimer";
import HealthBadge from "./components/HealthBadge";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold">criticalcare-copilot</h1>
            <p className="text-xs text-slate-500">Review-required clinical decision support</p>
          </div>
          <HealthBadge />
        </div>
        <nav className="max-w-6xl mx-auto px-4 pb-2 flex flex-wrap gap-3 text-sm">
          {[
            ["/", "Dashboard"],
            ["/new", "New case"],
            ["/summary", "Case summary"],
            ["/med-safety", "Medication safety"],
            ["/alerts", "Alert console"],
            ["/audit", "Audit"],
            ["/samples", "Samples"],
            ["/settings", "Settings"],
          ].map(([to, label]) => (
            <NavLink key={to} to={to}
              className={({ isActive }) =>
                `px-2 py-1 rounded ${isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"}`}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <Disclaimer />
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewCase />} />
          <Route path="/summary" element={<CaseSummary />} />
          <Route path="/med-safety" element={<MedicationSafety />} />
          <Route path="/alerts" element={<AlertConsole />} />
          <Route path="/audit" element={<AuditViewer />} />
          <Route path="/samples" element={<DemoSamples />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="text-xs text-slate-500 text-center py-4">
        Not a medical device. Every recommendation requires clinician review.
      </footer>
    </div>
  );
}
