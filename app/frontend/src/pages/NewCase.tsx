import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLocalCase } from "../hooks/useLocalCase";

const PLACEHOLDER = JSON.stringify({
  case_id: "demo-1",
  demographics: { age_years: 64, sex: "M" },
  encounter: { encounter_id: "E-1", admission_ts: "2026-04-17T10:00:00Z" },
  icu_stay: { stay_id: "S-1", icu_admit_ts: "2026-04-17T11:00:00Z" },
  medications: [{ name: "heparin", start_ts: "2026-04-17T11:30:00Z", status: "active", class: "anticoagulant" }],
  provenance: { source: "manual", extracted_ts: "2026-04-17T12:00:00Z" },
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
      setErr(`Invalid JSON: ${e.message}`);
    }
  }

  return (
    <div className="space-y-3">
      <h2 className="font-semibold">New case</h2>
      <p className="text-sm text-slate-600">
        Paste or edit a structured case JSON. Do not paste real PHI into shared environments.
      </p>
      <textarea
        className="w-full h-96 font-mono text-sm border rounded p-2"
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-label="Case JSON"
      />
      {err && <p className="text-sm text-red-600">{err}</p>}
      <button onClick={submit} className="px-3 py-2 rounded bg-slate-900 text-white">Use this case</button>
    </div>
  );
}
