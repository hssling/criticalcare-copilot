/** GET /.netlify/functions/health — basic liveness + endpoint reachability. */
import type { Handler } from "@netlify/functions";

export const handler: Handler = async () => {
  const url = process.env.HF_ENDPOINT_URL;
  let reachable = false;
  if (url) {
    try {
      const ctl = new AbortController();
      const to = setTimeout(() => ctl.abort(), 3_000);
      const r = await fetch(url, { method: "GET", signal: ctl.signal });
      clearTimeout(to);
      reachable = r.status < 500;
    } catch { reachable = false; }
  }
  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ok: true,
      model_endpoint: reachable ? "reachable" : "unreachable",
      has_token: Boolean(process.env.HF_API_TOKEN),
      model_revision: process.env.HF_MODEL_REVISION ?? "dev",
      enable_model_call: process.env.ENABLE_MODEL_CALL !== "false",
    }),
  };
};
