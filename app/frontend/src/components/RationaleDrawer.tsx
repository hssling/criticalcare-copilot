import { useState } from "react";

export default function RationaleDrawer({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded bg-white">
      <button
        className="w-full text-left px-3 py-2 flex items-center justify-between"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="font-medium">{title}</span>
        <span className="text-slate-500 text-xs">{open ? "hide" : "show"}</span>
      </button>
      {open && <div className="px-3 pb-3 text-sm text-slate-700">{children}</div>}
    </div>
  );
}
