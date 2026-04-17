/** POST /.netlify/functions/audit_log — explicit client-side audit beacon. */
import type { Handler } from "@netlify/functions";
import { appendAudit } from "./_lib/audit.js";

export const handler: Handler = async (event) => {
  if (event.httpMethod !== "POST") return { statusCode: 405, body: "method not allowed" };
  let body: any = {};
  try { body = JSON.parse(event.body || "{}"); } catch { /* ignore */ }
  await appendAudit({ source: "client", ...body });
  return { statusCode: 204, body: "" };
};
