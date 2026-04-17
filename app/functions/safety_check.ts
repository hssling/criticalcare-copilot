/** POST /.netlify/functions/safety_check — rules-only response. */
import type { Handler } from "@netlify/functions";
import Ajv from "ajv";
import addFormats from "ajv-formats";

import caseSchema from "../../data/schemas/case_schema.json" with { type: "json" };
import { runLightRules } from "./_lib/rules.js";
import { enforceGuardrails } from "./_lib/guardrails.js";
import { appendAudit } from "./_lib/audit.js";

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const validateCase = ajv.compile(caseSchema as object);

export const handler: Handler = async (event) => {
  if (event.httpMethod !== "POST") return { statusCode: 405, body: "method not allowed" };
  let body: any;
  try { body = JSON.parse(event.body || "{}"); }
  catch { return { statusCode: 400, body: JSON.stringify({ error: "invalid JSON" }) }; }
  const clinCase = body.case;
  if (!validateCase(clinCase)) {
    return { statusCode: 400, body: JSON.stringify({ error: "case failed schema validation", details: validateCase.errors }) };
  }
  const alerts = runLightRules(clinCase);
  const resp = {
    summary: "Rules-only safety check.", active_problems: [], alerts,
    recommendations: [], missing_data: [], uncertainty: "high",
    escalation: "", review_required: true, evidence: [], abstained: false,
  };
  enforceGuardrails(resp);
  await appendAudit({ mode: "safety_check", case_id: clinCase.case_id, rules_fired: alerts.map(a => a.rule_id ?? a.type) });
  return { statusCode: 200, headers: { "Content-Type": "application/json" }, body: JSON.stringify(resp) };
};
