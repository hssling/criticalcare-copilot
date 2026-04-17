import { redact } from "./redaction.js";

/** Append-only audit sink. Default: stdout JSON (captured by Netlify logs).
 *  Pluggable: replace with DB/Blob/HTTP sink in production. */
export async function appendAudit(record: Record<string, unknown>): Promise<void> {
  const event = { ts: new Date().toISOString(), ...redact(record) };
  // Netlify captures stdout from functions as logs.
  console.log("AUDIT", JSON.stringify(event));
}
