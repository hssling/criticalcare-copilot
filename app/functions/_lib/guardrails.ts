/** TS mirror of safety/output_guardrails.py. */
const ORDER_RE =
  /\b(give|administer|order|bolus|start)\s+(\d+\s*(mg|g|mcg|units?|ml|cc|l)\b|(norepinephrine|epinephrine|heparin|insulin)\b[^.]*\bnow\b)/i;

const SEVERITY_ORDER = ["low", "medium", "high", "critical"] as const;

export function enforceGuardrails(resp: any): void {
  if (!resp || typeof resp !== "object") throw new Error("response is not an object");

  resp.summary ??= "";
  resp.active_problems ??= [];
  resp.alerts ??= [];
  resp.recommendations ??= [];
  resp.missing_data ??= [];
  resp.uncertainty ??= "high";
  resp.escalation ??= "";
  resp.evidence ??= [];
  resp.review_required = true;

  resp.summary = rewrite(resp.summary);
  resp.recommendations = resp.recommendations.map(rewrite);
  for (const a of resp.alerts) {
    if (a.message) a.message = rewrite(a.message);
    if (a.rationale) a.rationale = rewrite(a.rationale);
  }

  const topIdx = Math.max(
    -1,
    ...resp.alerts.map((a: any) => SEVERITY_ORDER.indexOf(a.severity))
  );
  if (topIdx >= SEVERITY_ORDER.indexOf("high") && !resp.escalation.trim()) {
    resp.escalation =
      "Critical-severity alert(s) present. Escalate to the covering intensivist and re-verify key data points before acting.";
  }

  if (!["low", "medium", "high"].includes(resp.uncertainty)) resp.uncertainty = "high";
}

function rewrite(text: string): string {
  if (!text) return text;
  return text.replace(ORDER_RE, (m) => `consider reviewing (${m})`);
}
