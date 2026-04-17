/**
 * Lightweight TS subset of the Python rule engine — only the highest-impact
 * checks, sufficient to produce safety alerts when the Python service is not
 * reachable. The authoritative ruleset still lives in ../../rules/*.yaml and
 * is used by the Python evaluator; here we hand-code a few critical rules.
 */
export type Alert = {
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  source: "rule" | "model" | "retrieval";
  message: string;
  rationale?: string | null;
  rule_id?: string | null;
  evidence_ids: string[];
};

const LOWER = (s: any) => String(s ?? "").toLowerCase();

export function runLightRules(clinCase: any): Alert[] {
  const alerts: Alert[] = [];
  const meds = (clinCase.medications ?? []).filter((m: any) => (m.status ?? "active") === "active");
  const names = meds.map((m: any) => LOWER(m.name));
  const classes = meds.map((m: any) => LOWER(m.class)).filter(Boolean);
  const allergies = (clinCase.allergies ?? []).map((a: any) => LOWER(a.substance));
  const labs = clinCase.labs ?? [];

  // Penicillin + beta-lactam
  const betaLactams = ["amoxicillin", "ampicillin", "piperacillin-tazobactam", "cefepime", "ceftriaxone", "meropenem"];
  if (allergies.some((a: string) => ["penicillin", "amoxicillin"].includes(a)) &&
      names.some((n: string) => betaLactams.includes(n))) {
    alerts.push({
      type: "allergy_conflict", severity: "critical", source: "rule",
      message: "Penicillin allergy documented while a beta-lactam is active — escalate and review cross-reactivity.",
      rule_id: "allergy_penicillin_vs_betalactam", evidence_ids: [],
    });
  }

  // Duplicate anticoagulants
  if (classes.filter((c: string) => c === "anticoagulant").length >= 2) {
    alerts.push({
      type: "duplicate_therapy", severity: "critical", source: "rule",
      message: "Two anticoagulants appear concurrently active — escalate to verify bleeding risk and intent.",
      rule_id: "dup_anticoag", evidence_ids: [],
    });
  }

  // Hyperkalemia
  const k = lastNumeric(labs, ["potassium"]);
  if (k !== null && k >= 6.0) {
    alerts.push({
      type: "electrolyte_threshold", severity: "critical", source: "rule",
      message: `Serum potassium ${k} mEq/L — escalate urgently; obtain ECG and review.`,
      rule_id: "elyte_hyperkalemia", evidence_ids: [],
    });
  }

  // VTE prophylaxis omission (very rough)
  const anticoags = ["heparin", "enoxaparin", "dalteparin", "fondaparinux"];
  if (!names.some((n: string) => anticoags.includes(n))) {
    alerts.push({
      type: "vte_prophylaxis_omission", severity: "high", source: "rule",
      message: "No documented VTE prophylaxis — review indication.",
      rule_id: "prophy_vte_missing", evidence_ids: [],
    });
  }

  return alerts;
}

function lastNumeric(labs: any[], names: string[]): number | null {
  const match = labs
    .filter((l) => names.includes(LOWER(l.name)))
    .map((l) => ({ ts: l.ts ?? "", v: Number(l.value) }))
    .filter((l) => Number.isFinite(l.v))
    .sort((a, b) => (a.ts < b.ts ? -1 : 1));
  return match.length ? match[match.length - 1].v : null;
}
