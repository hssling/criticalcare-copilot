import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  ShieldAlert, 
  Info, 
  CheckCircle2, 
  AlertTriangle, 
  FileText,
  Clock,
  ExternalLink,
  Search
} from "lucide-react";
import { useLocalCase } from "../hooks/useLocalCase";
import { infer, auditBeacon } from "../lib/api";
import type { CopilotResponse } from "../types";
import AlertList from "../components/AlertList";
import EvidenceList from "../components/EvidenceList";
import RationaleDrawer from "../components/RationaleDrawer";
import Timeline from "../components/Timeline";

export default function CaseSummary() {
  const [clinCase] = useLocalCase();
  const [resp, setResp] = useState<CopilotResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<any>(null);

  useEffect(() => {
    if (!clinCase) return;
    setLoading(true); setErr(null);
    infer("icu_summary", clinCase)
      .then((r) => { 
        setResp(r); 
        auditBeacon({ event: "view_summary", case_id: clinCase.case_id }); 
      })
      .catch((e) => setErr(e))
      .finally(() => setLoading(false));
  }, [clinCase]);

  if (!clinCase) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center text-slate-400">
          <FileText size={32} />
        </div>
        <div>
          <h2 className="text-xl font-bold">No active case</h2>
          <p className="text-slate-500 max-w-xs">Start a new analysis or select a sample cohort from the sidebar.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 animate-shimmer rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
             <div className="h-64 glass-card animate-shimmer" />
             <div className="h-48 glass-card animate-shimmer" />
          </div>
          <div className="h-96 glass-card animate-shimmer" />
        </div>
      </div>
    );
  }

  if (err) {
    return (
      <div className="glass-card p-12 text-center space-y-6 border-rose-100 bg-rose-50/10">
        <div className="mx-auto w-16 h-16 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center">
          <ShieldAlert size={32} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Analysis Halted</h2>
          <p className="text-slate-600 max-w-md mx-auto">{err.message || "An unexpected error occurred during inference."}</p>
        </div>
        {err.reference_id && (
          <div className="inline-block px-4 py-2 bg-slate-100 rounded-lg font-mono text-xs text-slate-500">
            Ref ID: {err.reference_id}
          </div>
        )}
      </div>
    );
  }

  if (!resp) return null;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-bold text-sky-600 uppercase tracking-widest">
            <ClipboardList size={14} />
            Clinical Intelligence Case Summary
          </div>
          <h1 className="text-3xl font-bold text-slate-900">Case ID: {clinCase.case_id}</h1>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <div className={`px-4 py-1.5 rounded-xl border flex items-center gap-2 text-sm font-medium ${
            resp.uncertainty === 'high' ? 'bg-rose-50 border-rose-100 text-rose-700' :
            resp.uncertainty === 'medium' ? 'bg-amber-50 border-amber-100 text-amber-700' :
            'bg-emerald-50 border-emerald-100 text-emerald-700'
          }`}>
            <Search size={16} />
            Uncertainty: {resp.uncertainty}
          </div>
          <div className="px-4 py-1.5 rounded-xl bg-slate-900 text-white flex items-center gap-2 text-sm font-medium">
            <CheckCircle2 size={16} />
            Review Required
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Executive Summary */}
          <section className="glass-card overflow-hidden">
            <div className="bg-slate-900 px-6 py-4 flex items-center justify-between">
              <h2 className="text-white flex items-center gap-2">
                <FileText size={18} />
                Neural Summary
              </h2>
              {resp.abstained && <span className="badge badge-high bg-rose-500 text-white border-none">Abstained</span>}
            </div>
            <div className="p-8 space-y-4">
              <div className="text-lg text-slate-700 leading-relaxed font-medium whitespace-pre-wrap">
                {resp.summary}
              </div>
              
              {resp.escalation && (
                <div className="mt-8 p-4 bg-rose-50 border-l-4 border-rose-500 rounded-r-xl flex gap-4">
                  <AlertTriangle className="text-rose-500 shrink-0" size={24} />
                  <div>
                    <h4 className="text-rose-900 font-bold text-sm uppercase tracking-wider">Critical Escalation Plan</h4>
                    <p className="text-rose-700 font-medium">{resp.escalation}</p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Diagnosis & Problems */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h3 className="text-slate-900 flex items-center gap-2 mb-4 border-b pb-3">
                <Activity size={18} className="text-sky-500" />
                Active Problems
              </h3>
              <ul className="space-y-3">
                {resp.active_problems.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-600 group">
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1.5 group-hover:scale-125 transition-transform" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="glass-card p-6">
              <h3 className="text-slate-900 flex items-center gap-2 mb-4 border-b pb-3">
                <ExternalLink size={18} className="text-indigo-500" />
                Recommendations
              </h3>
              <ul className="space-y-3">
                {resp.recommendations.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-600 italic">
                    <CheckCircle2 size={14} className="text-slate-300 mt-0.5" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Timeline View */}
          <section className="glass-card p-8">
            <h3 className="text-slate-900 flex items-center gap-2 mb-8 uppercase tracking-widest text-xs font-bold">
              <Clock size={16} className="text-slate-400" />
              Clinical Event Context
            </h3>
            <Timeline clinCase={clinCase} />
          </section>
        </div>

        {/* Sidebar Column */}
        <div className="space-y-8">
          {/* Alerts Panel */}
          <section className="space-y-4">
             <h3 className="text-slate-900 flex items-center gap-2 uppercase tracking-widest text-xs font-bold px-2">
              <ShieldAlert size={16} className="text-rose-500" />
              Safety Alerts
            </h3>
            <AlertList alerts={resp.alerts} />
          </section>

          {/* Missing Data */}
          {resp.missing_data.length > 0 && (
            <section className="glass-card p-6 border-amber-100 bg-amber-50/5">
              <h3 className="text-amber-800 flex items-center gap-2 text-sm font-bold mb-3 uppercase tracking-wider">
                <Info size={16} />
                Information Gaps
              </h3>
              <ul className="space-y-2">
                {resp.missing_data.map((m, i) => (
                  <li key={i} className="text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded-md border border-amber-100">
                    {m}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Evidence Registry */}
          <section className="space-y-4">
             <h3 className="text-slate-900 flex items-center gap-2 uppercase tracking-widest text-xs font-bold px-2">
              <Database size={16} className="text-slate-400" />
              Knowledge Evidence
            </h3>
            <EvidenceList items={resp.evidence} />
          </section>
        </div>
      </div>
    </div>
  );
}
