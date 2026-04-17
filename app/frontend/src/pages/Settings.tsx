import { useEffect, useState } from "react";
import { health } from "../lib/api";

export default function Settings() {
  const [h, setH] = useState<Record<string, unknown>>({});
  useEffect(() => { health().then(setH).catch(() => setH({})); }, []);
  return (
    <div className="space-y-3">
      <h2 className="font-semibold">Settings</h2>
      <pre className="bg-white border border-slate-200 rounded p-3 text-xs overflow-x-auto">
{JSON.stringify(h, null, 2)}
      </pre>
      <p className="text-xs text-slate-500">
        Environment variables are managed in the Netlify UI. Secrets never reach the browser.
      </p>
    </div>
  );
}
