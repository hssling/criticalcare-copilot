import { Link } from "react-router-dom";
import { useLocalCase } from "../hooks/useLocalCase";

export default function Dashboard() {
  const [clinCase] = useLocalCase();
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <section className="bg-white rounded border border-slate-200 p-4">
        <h2 className="font-semibold mb-2">Active case</h2>
        {clinCase ? (
          <div className="text-sm">
            <div><span className="text-slate-500">ID:</span> {clinCase.case_id}</div>
            <div><span className="text-slate-500">Age/Sex:</span> {clinCase.demographics.age_years} / {clinCase.demographics.sex}</div>
            <div className="mt-3 flex gap-3">
              <Link className="underline" to="/summary">Open summary</Link>
              <Link className="underline" to="/med-safety">Medication safety</Link>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-600">
            No active case. <Link className="underline" to="/new">Enter a new case</Link> or <Link className="underline" to="/samples">load a sample</Link>.
          </p>
        )}
      </section>
      <section className="bg-white rounded border border-slate-200 p-4">
        <h2 className="font-semibold mb-2">Quick links</h2>
        <ul className="list-disc pl-5 text-sm space-y-1">
          <li><Link className="underline" to="/alerts">Alert console</Link></li>
          <li><Link className="underline" to="/audit">Audit viewer</Link></li>
          <li><Link className="underline" to="/settings">Settings / model version</Link></li>
        </ul>
      </section>
    </div>
  );
}
