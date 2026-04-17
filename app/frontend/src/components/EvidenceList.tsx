import type { Evidence } from "../types";

export default function EvidenceList({ items }: { items: Evidence[] }) {
  if (!items.length) return <p className="text-sm text-slate-500">No evidence retrieved.</p>;
  return (
    <ul className="space-y-2">
      {items.map((e, i) => (
        <li key={i} className="border border-slate-200 rounded p-3 bg-white">
          <div className="font-medium">{e.title}</div>
          <div className="text-xs text-slate-500">source: {e.source_id}</div>
          <p className="text-sm mt-1 whitespace-pre-wrap">{e.snippet}</p>
        </li>
      ))}
    </ul>
  );
}
