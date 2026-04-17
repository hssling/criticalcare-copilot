/**
 * POST /.netlify/functions/infer
 *
 * Body: { task: string, case: ClinicalCase, use_rag?: boolean }
 *
 * Responsibilities:
 *   1. Validate the incoming case against case_schema.json (Ajv).
 *   2. Call the HF Inference Endpoint with a strict system+safety prompt.
 *   3. Run deterministic safety checks (a light, TS-side subset of rules).
 *   4. Merge rule alerts + model output into the response contract.
 *   5. Enforce review_required=true and advisory phrasing before returning.
 *
 * Secrets (HF_API_TOKEN, HF_ENDPOINT_URL) come from Netlify env only.
 */
import type { Handler } from "@netlify/functions";
import Ajv from "ajv";
import addFormats from "ajv-formats";

import caseSchema from "../../data/schemas/case_schema.json" with { type: "json" };
import responseSchema from "../../data/schemas/response_schema.json" with { type: "json" };
import alertSchema from "../../data/schemas/alert_schema.json" with { type: "json" };
import { runLightRules } from "./_lib/rules.js";
import { enforceGuardrails } from "./_lib/guardrails.js";
import { buildPrompt, coerceJson } from "./_lib/prompt.js";
import { appendAudit } from "./_lib/audit.js";

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(alertSchema, "alert_schema.json");
const validateCase = ajv.compile(caseSchema as object);
const validateResponse = ajv.compile(responseSchema as object);

export const handler: Handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "method not allowed" };
  }
  let body: any;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "invalid JSON" }) };
  }
  const { task = "icu_summary", case: clinCase, use_rag = false } = body;

  if (!validateCase(clinCase)) {
    return json(400, abstain("case failed schema validation", validateCase.errors?.slice(0, 5) ?? []));
  }

  const ruleAlerts = runLightRules(clinCase);

  let modelOut: any = {};
  if (process.env.ENABLE_MODEL_CALL !== "false") {
    modelOut = await callHF(task, clinCase, use_rag);
  }

  const merged = mergeResponses(clinCase, ruleAlerts, modelOut);
  enforceGuardrails(merged);

  if (!validateResponse(merged)) {
    const fallback = abstain("response failed schema validation", validateResponse.errors?.slice(0, 5) ?? []);
    await appendAudit({ task, case_id: clinCase.case_id, schema_valid: false, degraded: true });
    return json(200, fallback);
  }

  merged.model_version = process.env.HF_MODEL_REVISION ?? "dev";
  await appendAudit({
    task, case_id: clinCase.case_id,
    model_version: merged.model_version,
    rules_fired: ruleAlerts.map((a) => a.rule_id ?? a.type),
    review_required: merged.review_required,
    schema_valid: true,
  });
  return json(200, merged);
};

// ---------------------------------------------------------------------------

async function callHF(task: string, clinCase: any, useRag: boolean): Promise<any> {
  const url = process.env.HF_ENDPOINT_URL;
  const token = process.env.HF_API_TOKEN;
  if (!url || !token) return {};

  const prompt = buildPrompt({ task, case: clinCase, evidence: useRag ? [] : [] });

  const controller = new AbortController();
  const to = setTimeout(() => controller.abort(), 45_000);
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: { max_new_tokens: 1024, temperature: 0.2, top_p: 0.9, return_full_text: false },
      }),
      signal: controller.signal,
    });
    if (!r.ok) return {};
    const data = await r.json();
    const text = Array.isArray(data) ? data[0]?.generated_text ?? "" : data.generated_text ?? "";
    return coerceJson(text);
  } catch {
    return {};
  } finally {
    clearTimeout(to);
  }
}

function mergeResponses(clinCase: any, ruleAlerts: any[], modelOut: any) {
  const alerts = [...ruleAlerts];
  for (const a of modelOut.alerts ?? []) {
    if (a?.type && a?.message) {
      alerts.push({ source: "model", severity: "medium", evidence_ids: [], ...a });
    }
  }
  const dxs = (clinCase.diagnoses ?? [])
    .filter((d: any) => d?.status === "active")
    .map((d: any) => d.label)
    .filter(Boolean);
  const summary =
    (modelOut.summary ?? "").trim() ||
    (dxs.length ? `Active diagnoses: ${dxs.slice(0, 5).join(", ")}.` :
                  "Insufficient narrative data; clinician review required.");

  return {
    summary,
    active_problems: modelOut.active_problems ?? [],
    alerts,
    recommendations: modelOut.recommendations ?? [],
    missing_data: modelOut.missing_data ?? [],
    uncertainty: modelOut.uncertainty ?? "high",
    escalation: modelOut.escalation ?? "",
    review_required: true,
    evidence: modelOut.evidence ?? [],
    abstained: Boolean(modelOut.abstained),
  };
}

function abstain(reason: string, details: any[]) {
  return {
    summary: "Unable to produce a safe response.",
    active_problems: [],
    alerts: [{
      type: "other", severity: "high", source: "rule",
      message: reason, rationale: "Abstention is preferred over unsafe output.",
      rule_id: "abstain.safety", evidence_ids: [],
    }],
    recommendations: [],
    missing_data: details.map((d) => (typeof d === "string" ? d : JSON.stringify(d))),
    uncertainty: "high",
    escalation: "Review input and escalate to the covering clinician.",
    review_required: true,
    evidence: [],
    abstained: true,
  };
}

function json(status: number, body: unknown) {
  return {
    statusCode: status,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}
