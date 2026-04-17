import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  LayoutDashboard, 
  PlusCircle, 
  ClipboardList, 
  ShieldAlert, 
  ShieldCheck, 
  History, 
  Database, 
  Settings as SettingsIcon,
  Activity,
  Menu,
  X
} from "lucide-react";
import { useState } from "react";

import Dashboard from "./pages/Dashboard";
import NewCase from "./pages/NewCase";
import CaseSummary from "./pages/CaseSummary";
import MedicationSafety from "./pages/MedicationSafety";
import AlertConsole from "./pages/AlertConsole";
import AuditViewer from "./pages/AuditViewer";
import Settings from "./pages/Settings";
import DemoSamples from "./pages/DemoSamples";

import HealthBadge from "./components/HealthBadge";

export default function App() {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  const navLinks = [
    { to: "/", label: "Overview", icon: LayoutDashboard },
    { to: "/new", label: "Analyze New Case", icon: PlusCircle },
    { to: "/summary", label: "Clinical Summary", icon: ClipboardList },
    { to: "/med-safety", label: "Medication Safety", icon: ShieldCheck },
    { to: "/alerts", label: "Alert Console", icon: ShieldAlert },
    { to: "/audit", label: "Audit Registry", icon: History },
    { to: "/samples", label: "Example Cohorts", icon: Database },
  ];

  return (
    <div className="flex h-screen bg-[#f8fafc]">
      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {isSidebarOpen && (
          <motion.aside
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            className="w-72 bg-slate-50 border-r border-slate-200 p-6 flex flex-col gap-8 z-50 fixed lg:relative h-full"
          >
            <div className="flex items-center gap-3 px-2">
              <div className="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center text-white shadow-lg shadow-slate-200">
                <Activity size={24} />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight text-slate-900">Copilot</h1>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-none">Critical Care</p>
              </div>
            </div>

            <nav className="flex flex-col gap-1 flex-1">
              {navLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
                >
                  <link.icon size={20} />
                  <span className="font-medium">{link.label}</span>
                </NavLink>
              ))}
            </nav>

            <div className="mt-auto pt-6 border-t border-slate-200">
              <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
                <SettingsIcon size={20} />
                <span className="font-medium">System config</span>
              </NavLink>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-40">
           <button 
            onClick={() => setSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
           >
             {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
           </button>

           <div className="flex items-center gap-6">
             <div className="hidden sm:flex flex-col items-end">
               <span className="text-xs font-bold text-rose-500 uppercase tracking-widest">Advisory Mode Only</span>
               <span className="text-[10px] text-slate-400">Review all outputs before clinical action</span>
             </div>
             <HealthBadge />
           </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8 relative">
          {/* Background Decorative Blobs */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-sky-100/30 rounded-full blur-3xl pointer-events-none -mr-48 -mt-48" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-100/20 rounded-full blur-3xl pointer-events-none -ml-48 -mb-48" />

          <div className="max-w-5xl mx-auto relative z-10">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
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
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}
