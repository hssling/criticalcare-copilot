import type { Alert } from "../types";

const severityClass = (s: Alert["severity"]) =>
  s === "critical" ? "badge-crit" : s === "high" ? "badge-high" : s === "medium" ? "badge-med" : "badge-low";

export default function AlertList({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) return <p className="text-sm text-slate-500">No alerts.</p>;
  const sorted = [...alerts].sort(
    (a, b) => ["low", "medium", "high", "critical"].indexOf(b.severity) -
              ["low", "medium", "high", "critical"].indexOf(a.severity)
  );
  return (
    <ul className="space-y-2">
      {sorted.map((a, i) => (
        <li key={i} className="border border-slate-200 rounded p-3 bg-white">
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium">{a.type.replace(/_/g, " ")}</span>
            <span className={`badge ${severityClass(a.severity)}`}>{a.severity}</span>
          </div>
          <p className="text-sm mt-1">{a.message}</p>
          {a.rationale && <p className="text-xs text-slate-500 mt-1">{a.rationale}</p>}
          <div className="text-xs text-slate-400 mt-1">
            source: {a.source}{a.rule_id ? ` · rule: ${a.rule_id}` : ""}
          </div>
        </li>
      ))}
    </ul>
  );
}
