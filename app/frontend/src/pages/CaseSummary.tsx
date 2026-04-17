import { useEffect, useState } from "react";
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
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!clinCase) return;
    setLoading(true); setErr(null);
    infer("icu_summary", clinCase)
      .then((r) => { setResp(r); auditBeacon({ event: "view_summary", case_id: clinCase.case_id }); })
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [clinCase]);

  if (!clinCase) return <p>No active case. Start under "New case" or "Samples".</p>;
  if (loading) return <p className="text-sm text-slate-500">Running review-required analysis…</p>;
  if (err) return <p className="text-sm text-red-600">{err}</p>;
  if (!resp) return null;

  return (
    <div className="space-y-4">
      <section className="bg-white rounded border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Summary</h2>
          <div className="flex gap-2">
            <span className="badge badge-low">review required</span>
            <span className={`badge ${resp.uncertainty === "high" ? "badge-high" : resp.uncertainty === "medium" ? "badge-med" : "badge-low"}`}>
              uncertainty: {resp.uncertainty}
            </span>
            {resp.abstained && <span className="badge badge-high">abstained</span>}
          </div>
        </div>
        <p className="mt-2 text-sm whitespace-pre-wrap">{resp.summary}</p>
        {resp.escalation && (
          <p className="mt-2 text-sm text-red-700"><strong>Escalation:</strong> {resp.escalation}</p>
        )}
      </section>

      <section className="bg-white rounded border border-slate-200 p-4">
        <h3 className="font-semibold mb-2">Active problems</h3>
        {resp.active_problems.length ? (
          <ul className="list-disc pl-5 text-sm">
            {resp.active_problems.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        ) : <p className="text-sm text-slate-500">None listed.</p>}
      </section>

      <section>
        <h3 className="font-semibold mb-2">Alerts</h3>
        <AlertList alerts={resp.alerts} />
      </section>

      <section className="bg-white rounded border border-slate-200 p-4">
        <h3 className="font-semibold mb-2">Recommendations (advisory)</h3>
        {resp.recommendations.length ? (
          <ul className="list-disc pl-5 text-sm">
            {resp.recommendations.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        ) : <p className="text-sm text-slate-500">None.</p>}
      </section>

      <section className="bg-white rounded border border-slate-200 p-4">
        <h3 className="font-semibold mb-2">Missing data</h3>
        {resp.missing_data.length ? (
          <ul className="list-disc pl-5 text-sm">
            {resp.missing_data.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        ) : <p className="text-sm text-slate-500">None identified.</p>}
      </section>

      <RationaleDrawer title="Timeline">
        <Timeline clinCase={clinCase} />
      </RationaleDrawer>

      <RationaleDrawer title="Evidence">
        <EvidenceList items={resp.evidence} />
      </RationaleDrawer>
    </div>
  );
}
