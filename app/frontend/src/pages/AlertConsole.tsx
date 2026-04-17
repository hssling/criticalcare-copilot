import { useEffect, useState } from "react";
import { useLocalCase } from "../hooks/useLocalCase";
import { infer } from "../lib/api";
import AlertList from "../components/AlertList";
import type { CopilotResponse } from "../types";

export default function AlertConsole() {
  const [clinCase] = useLocalCase();
  const [resp, setResp] = useState<CopilotResponse | null>(null);
  useEffect(() => {
    if (clinCase) infer("icu_summary", clinCase).then(setResp).catch(() => setResp(null));
  }, [clinCase]);
  return (
    <div className="space-y-3">
      <h2 className="font-semibold">Alert console</h2>
      {!clinCase ? <p>No active case.</p>
        : !resp ? <p className="text-sm text-slate-500">Loading…</p>
        : <AlertList alerts={resp.alerts} />}
    </div>
  );
}
