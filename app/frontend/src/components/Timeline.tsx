import type { ClinicalCase } from "../types";

export default function Timeline({ clinCase }: { clinCase: ClinicalCase }) {
  const events: { ts: string; kind: string; detail: string }[] = [];
  for (const v of clinCase.vitals ?? [])
    events.push({ ts: v.ts, kind: "vital", detail: `${v.name}=${v.value}${v.unit ? " " + v.unit : ""}` });
  for (const l of clinCase.labs ?? [])
    events.push({ ts: l.ts, kind: "lab", detail: `${l.name}=${l.value}${l.unit ? " " + l.unit : ""}` });
  for (const m of clinCase.medications ?? [])
    events.push({ ts: m.start_ts, kind: "med", detail: `${m.name}${m.dose ? " " + m.dose + (m.dose_unit ?? "") : ""}` });
  events.sort((a, b) => (a.ts < b.ts ? -1 : 1));
  if (!events.length) return <p className="text-sm text-slate-500">No timeline events.</p>;
  return (
    <ol className="space-y-1 text-sm">
      {events.slice(0, 100).map((e, i) => (
        <li key={i} className="flex gap-3">
          <span className="text-slate-500 w-40 shrink-0">{e.ts}</span>
          <span className="badge badge-low w-16 justify-center">{e.kind}</span>
          <span>{e.detail}</span>
        </li>
      ))}
    </ol>
  );
}
