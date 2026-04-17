import type { ClinicalCase, CopilotResponse } from "../types";

const BASE = import.meta.env.VITE_FUNCTIONS_BASE || "/.netlify/functions";

export async function infer(task: string, clinCase: ClinicalCase): Promise<CopilotResponse> {
  const r = await fetch(`${BASE}/infer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task, case: clinCase }),
  });
  if (!r.ok) throw new Error(`infer failed: ${r.status}`);
  return r.json();
}

export async function safetyCheck(clinCase: ClinicalCase): Promise<CopilotResponse> {
  const r = await fetch(`${BASE}/safety_check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case: clinCase }),
  });
  if (!r.ok) throw new Error(`safety_check failed: ${r.status}`);
  return r.json();
}

export async function health() {
  const r = await fetch(`${BASE}/health`);
  return r.json();
}

export async function auditBeacon(record: Record<string, unknown>) {
  try {
    await fetch(`${BASE}/audit_log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(record),
    });
  } catch { /* fire-and-forget */ }
}
