import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  FileJson, 
  Sparkles, 
  ShieldCheck, 
  HelpCircle,
  ArrowRight
} from "lucide-react";
import { useLocalCase } from "../hooks/useLocalCase";

const PLACEHOLDER = JSON.stringify({
  case_id: "ICU-7729-A",
  demographics: { age_years: 68, sex: "M", weight_kg: 84 },
  encounter: { encounter_id: "E-401", admission_ts: "2026-04-17T08:00:00Z" },
  icu_stay: { stay_id: "S-102", icu_admit_ts: "2026-04-17T09:15:00Z", unit_type: "MICU" },
  medications: [
    { name: "Noradrenaline", start_ts: "2026-04-17T09:30:00Z", status: "active", class: "vasopressor" },
    { name: "Fentanyl", start_ts: "2026-04-17T09:45:00Z", status: "active", class: "analgesic" }
  ],
  labs: [
    { name: "Lactate", value: 4.2, unit: "mmol/L", ts: "2026-04-17T10:00:00Z" }
  ],
  provenance: { source: "manual_entry", extracted_ts: "2026-04-17T12:00:00Z" },
}, null, 2);

export default function NewCase() {
  const nav = useNavigate();
  const [, setCase] = useLocalCase();
  const [text, setText] = useState(PLACEHOLDER);
  const [err, setErr] = useState<string | null>(null);

  function submit() {
    try {
      const parsed = JSON.parse(text);
      setCase(parsed);
      setErr(null);
      nav("/summary");
    } catch (e: any) {
      setErr(`Syntax Error: ${e.message}`);
    }
  }

  return (
    <div className="space-y-8">
      <div className="max-w-2xl">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">Admissions Workbench</h2>
        <p className="text-slate-500">
          Initialize a neural clinical review by providing a structured case schema. 
          Use the workbench below to edit the JSON manifest before submission.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card overflow-hidden">
            <div className="bg-white px-6 py-3 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest">
                <FileJson size={14} />
                JSON manifest
              </div>
              <div className="flex items-center gap-4">
                 <button 
                  onClick={() => setText(PLACEHOLDER)}
                  className="text-[10px] font-bold text-sky-600 uppercase hover:underline"
                 >
                   Reset to Sample
                 </button>
              </div>
            </div>
            <textarea
              className="w-full h-[500px] font-mono text-[13px] p-6 bg-slate-50/30 focus:bg-white outline-none transition-colors border-none"
              value={text}
              onChange={(e) => setText(e.target.value)}
              spellCheck={false}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="text-emerald-500" size={18} />
              <span className="text-xs text-slate-500">Inputs are redacted before cloud processing</span>
            </div>
            <button 
              onClick={submit} 
              className="btn-primary flex items-center gap-2"
            >
              Analyze Case
              <ArrowRight size={18} />
            </button>
          </div>
          
          {err && (
            <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-rose-600 text-sm font-medium animate-in fade-in slide-in-from-top-1">
              {err}
            </div>
          )}
        </div>

        <div className="space-y-6">
           <div className="glass-card p-6 bg-indigo-50/10 border-indigo-100">
              <h3 className="text-indigo-900 flex items-center gap-2 mb-3">
                <Sparkles size={18} />
                Intelligent Validation
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Our engine automatically detects:
              </p>
              <ul className="mt-4 space-y-3">
                {[
                  "Medication contraindications",
                  "Missing critical labs (Lactate, Creatinine)",
                  "Allergy crossovers",
                  "Dosing out-of-bounds"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs text-slate-600">
                    <div className="w-1 h-1 rounded-full bg-indigo-300" />
                    {item}
                  </li>
                ))}
              </ul>
           </div>

           <div className="p-6 rounded-2xl bg-slate-900 text-white space-y-4">
              <h3 className="flex items-center gap-2 text-sm">
                <HelpCircle size={18} className="text-sky-400" />
                Schema Help
              </h3>
              <p className="text-[11px] text-slate-400">
                The manifest follows the HL7-aligned internal schema. Ensure all timestamps are in ISO-8601 format.
              </p>
              <a href="https://github.com/hssling/criticalcare-copilot/blob/master/data/schemas/case_schema.json" target="_blank" className="text-[10px] font-bold text-sky-400 uppercase tracking-wider hover:underline flex items-center gap-1">
                View Specification <ExternalLink size={10} />
              </a>
           </div>
        </div>
      </div>
    </div>
  );
}
