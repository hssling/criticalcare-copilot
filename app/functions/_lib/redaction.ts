/**
 * PHI Redaction for TypeScript-side inference.
 * Recursively scrubs keys that might contain Patient Health Information (PHI).
 */

const REDACTED_KEYS = new Set([
  "name",
  "first_name",
  "last_name",
  "email",
  "phone",
  "phone_number",
  "address",
  "ssn",
  "mrn",
  "patient_name",
  "patient_id",
  "dob",
  "date_of_birth",
  "token",
  "api_key",
  "password",
]);

/**
 * Recursively redacts sensitive info from an object.
 */
export function redact(data: any): any {
  if (data === null || typeof data !== "object") {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map((item) => redact(item));
  }

  const redacted: Record<string, any> = {};
  for (const [key, value] of Object.entries(data)) {
    if (REDACTED_KEYS.has(key.toLowerCase())) {
      redacted[key] = "[REDACTED]";
    } else {
      redacted[key] = redact(value);
    }
  }
  return redacted;
}
