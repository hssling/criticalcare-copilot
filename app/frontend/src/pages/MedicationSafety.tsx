import { useEffect, useState } from "react";
import { useLocalCase } from "../hooks/useLocalCase";
import { safetyCheck } from "../lib/api";
import type { CopilotResponse } from "../types";
import AlertList from "../components/AlertList";

export default function MedicationSafety() {
  const [clinCase] = useLocalCase();
  const [resp, setResp] = useState<CopilotResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!clinCase) return;
    setErr(null);
    safetyCheck(clinCase).then(setResp).catch((e) => setErr(String(e)));
  }, [clinCase]);

  if (!clinCase) return <p>No active case.</p>;
  if (err) return <p className="text-red-600 text-sm">{err}</p>;
  if (!resp) return <p className="text-slate-500 text-sm">Running rules…</p>;

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Medication safety (rules-only)</h2>
      <p className="text-sm text-slate-500">Deterministic rule layer only; model not invoked on this page.</p>
      <AlertList alerts={resp.alerts} />
    </div>
  );
}
