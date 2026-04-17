import { useLocalCase } from "../hooks/useLocalCase";
import { useNavigate } from "react-router-dom";

const SAMPLES = [
  {
    case_id: "sample-hyperK",
    demographics: { age_years: 72, sex: "M", weight_kg: 80 },
    encounter: { encounter_id: "E-100", admission_ts: "2026-04-17T06:00:00Z" },
    icu_stay: { stay_id: "S-100", icu_admit_ts: "2026-04-17T07:00:00Z" },
    labs: [{ ts: "2026-04-17T08:00:00Z", name: "potassium", value: 6.3, unit: "mEq/L" }],
    medications: [],
    provenance: { source: "synthetic", extracted_ts: "2026-04-17T09:00:00Z" },
  },
  {
    case_id: "sample-pcn-allergy",
    demographics: { age_years: 54, sex: "F" },
    encounter: { encounter_id: "E-101", admission_ts: "2026-04-17T06:00:00Z" },
    icu_stay: { stay_id: "S-101", icu_admit_ts: "2026-04-17T07:00:00Z" },
    allergies: [{ substance: "penicillin", severity: "severe" }],
    medications: [{ name: "piperacillin-tazobactam", start_ts: "2026-04-17T08:00:00Z", status: "active" }],
    provenance: { source: "synthetic", extracted_ts: "2026-04-17T09:00:00Z" },
  },
];

export default function DemoSamples() {
  const [, setCase] = useLocalCase();
  const nav = useNavigate();
  return (
    <div className="space-y-3">
      <h2 className="font-semibold">Demo samples</h2>
      <p className="text-sm text-slate-600">Fully synthetic cases — safe to use for demos.</p>
      <ul className="space-y-2">
        {SAMPLES.map((s) => (
          <li key={s.case_id} className="bg-white border border-slate-200 rounded p-3 flex items-center justify-between">
            <div>
              <div className="font-medium">{s.case_id}</div>
              <div className="text-xs text-slate-500">{s.demographics.age_years}y {s.demographics.sex}</div>
            </div>
            <button className="px-3 py-1.5 rounded bg-slate-900 text-white text-sm"
              onClick={() => { setCase(s as any); nav("/summary"); }}>
              Load
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
