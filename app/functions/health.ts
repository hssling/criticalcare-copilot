/**
 * GET /.netlify/functions/health
 * Checks if the configured HF Endpoint is reachable.
 */
import type { Handler } from "@netlify/functions";

export const handler: Handler = async () => {
  const url = process.env.HF_ENDPOINT_URL;
  const token = process.env.HF_API_TOKEN;

  let modelStatus = "not_configured";
  if (url && token) {
    try {
      const controller = new AbortController();
      const to = setTimeout(() => controller.abort(), 2000);
      const r = await fetch(url, {
        method: "HEAD",
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      clearTimeout(to);
      modelStatus = r.ok ? "reachable" : `failed_${r.status}`;
    } catch (e: any) {
      modelStatus = e.name === "AbortError" ? "timeout" : "unreachable";
    }
  }

  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ok: modelStatus === "reachable",
      ts: new Date().toISOString(),
      model_endpoint: modelStatus,
      version: process.env.HF_MODEL_REVISION ?? "dev",
    }),
  };
};
