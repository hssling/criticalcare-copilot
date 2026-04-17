export type Severity = "low" | "medium" | "high" | "critical";

export interface Alert {
  type: string;
  severity: Severity;
  source: "rule" | "model" | "retrieval";
  message: string;
  rationale?: string | null;
  rule_id?: string | null;
  evidence_ids?: string[];
}

export interface Evidence {
  title: string;
  snippet: string;
  source_id: string;
}

export interface CopilotResponse {
  summary: string;
  active_problems: string[];
  alerts: Alert[];
  recommendations: string[];
  missing_data: string[];
  uncertainty: "low" | "medium" | "high";
  escalation: string;
  review_required: true;
  evidence: Evidence[];
  model_version?: string | null;
  abstained?: boolean;
}

export interface ClinicalCase {
  case_id: string;
  demographics: { age_years: number; sex: string; weight_kg?: number | null; height_cm?: number | null };
  encounter: { encounter_id: string; admission_ts: string };
  icu_stay: { stay_id: string; icu_admit_ts: string; unit_type?: string | null };
  vitals?: any[]; labs?: any[]; medications?: any[]; allergies?: any[];
  diagnoses?: any[]; notes?: any[];
  provenance: { source: string; extracted_ts: string };
  review_required?: boolean;
}
