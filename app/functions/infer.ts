/**
 * POST /.netlify/functions/infer
 *
 * Body: { task: string, case: ClinicalCase, use_rag?: boolean }
 *
 * Hardened Production (v0.2 TS):
 *   1. UUID-based request tracking.
 *   2. PHI Redaction of all log events.
 *   3. Structured JSON logging (stdout).
 *   4. Safe error code mapping (no internal leaks).
 *   5. Hard payload size limits.
 *   6. Schema validation + Rule engine gating.
 */
import type { Handler } from "@netlify/functions";
import Ajv from "ajv";
import addFormats from "ajv-formats";
import { v4 as uuidv4 } from "uuid";

import caseSchema from "../../data/schemas/case_schema.json" with { type: "json" };
import responseSchema from "../../data/schemas/response_schema.json" with { type: "json" };
import alertSchema from "../../data/schemas/alert_schema.json" with { type: "json" };
import { runLightRules } from "./_lib/rules.js";
import { enforceGuardrails } from "./_lib/guardrails.js";
import { buildPrompt, coerceJson } from "./_lib/prompt.js";
import { appendAudit } from "./_lib/audit.js";
import { redact } from "./_lib/redaction.js";
import { getSafeError, jsonError } from "./_lib/errors.js";

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(alertSchema, "alert_schema.json");
const validateCase = ajv.compile(caseSchema as object);
const validateResponse = ajv.compile(responseSchema as object);

const MAX_PAYLOAD_BYTES = 256 * 1024; // 256 KiB

export const handler: Handler = async (event) => {
  const reqId = uuidv4().slice(0, 12);
  
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "method not allowed" };
  }

  // Size limit check
  if (event.body && event.body.length > MAX_PAYLOAD_BYTES) {
    return jsonError(getSafeError("PAYLOAD_TOO_LARGE", reqId));
  }

  let body: any;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return jsonError(getSafeError("INTERNAL_ERROR", reqId, "Invalid JSON body"));
  }

  const { task = "icu_summary", case: clinCase, use_rag = false } = body;

  // Log request (Redacted)
  console.log(JSON.stringify({
    level: "INFO",
    msg: "request_received",
    reqId,
    data: redact({ task, use_rag, case_id: clinCase?.case_id })
  }));

  if (!clinCase || !validateCase(clinCase)) {
    const problems = validateCase.errors?.slice(0, 3) ?? [];
    console.warn(JSON.stringify({ 
      level: "WARN", msg: "validation_failed", reqId, problems 
    }));
    return jsonError(getSafeError("INPUT_VALIDATION_FAILED", reqId, JSON.stringify(problems)));
  }

  try {
    const ruleAlerts = runLightRules(clinCase);

    let modelOut: any = {};
    if (process.env.ENABLE_MODEL_CALL !== "false") {
      modelOut = await callHF(task, clinCase, use_rag, reqId);
    }

    const merged = mergeResponses(clinCase, ruleAlerts, modelOut);
    enforceGuardrails(merged);

    if (!validateResponse(merged)) {
      console.error(JSON.stringify({ 
        level: "ERROR", msg: "response_schema_failed", reqId, errors: validateResponse.errors 
      }));
      // Failed response validation results in a safe abstention
      const fallback = getAbstention("Response internal validation failed", reqId);
      await appendAudit({ task, reqId, case_id: clinCase.case_id, schema_valid: false, degraded: true });
      return json(200, fallback);
    }

    merged.model_version = process.env.HF_MODEL_REVISION ?? "dev";
    
    await appendAudit({
      task, 
      reqId,
      case_id: clinCase.case_id,
      model_version: merged.model_version,
      rules_fired: ruleAlerts.map((a) => a.rule_id ?? a.type),
      review_required: merged.review_required,
      schema_valid: true,
    });

    return json(200, merged);

  } catch (err: any) {
    console.error(JSON.stringify({ level: "ERROR", msg: "unhandled_exception", reqId, error: err.message }));
    return jsonError(getSafeError("INTERNAL_ERROR", reqId));
  }
};

// ---------------------------------------------------------------------------

async function callHF(task: string, clinCase: any, useRag: boolean, reqId: string): Promise<any> {
    const url = process.env.HF_ENDPOINT_URL;
    const token = process.env.HF_API_TOKEN;
    if (!url || !token) {
        console.warn(JSON.stringify({ level: "WARN", msg: "hf_config_missing", reqId }));
        return {};
    }

    const prompt = buildPrompt({ task, case: clinCase, evidence: useRag ? [] : [] });
    const timeoutS = parseInt(process.env.HF_TIMEOUT_S || "45");

    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), timeoutS * 1000);
    
    try {
        console.log(JSON.stringify({ level: "INFO", msg: "hf_request_sent", reqId, timeout: timeoutS }));
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

        if (!r.ok) {
            console.error(JSON.stringify({ level: "ERROR", msg: "hf_api_error", reqId, status: r.status }));
            return {};
        }

        const data = await r.json();
        const text = Array.isArray(data) ? data[0]?.generated_text ?? "" : data.generated_text ?? "";
        return coerceJson(text);
    } catch (err: any) {
        console.error(JSON.stringify({ level: "ERROR", msg: "hf_fetch_exception", reqId, error: err.name }));
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

function getAbstention(reason: string, refId: string) {
  return {
    summary: "Unable to produce a safe response.",
    active_problems: [],
    alerts: [{
      type: "other", severity: "high", source: "rule",
      message: reason, rationale: "Response validation failed internally.",
      rule_id: "abstain.fallback", evidence_ids: [],
    }],
    recommendations: [],
    missing_data: [`Reference ID: ${refId}`],
    uncertainty: "high",
    escalation: "Manual review required.",
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
