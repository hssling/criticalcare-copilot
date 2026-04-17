/** POST /.netlify/functions/retrieve_context
 *  Body: { query: string, k?: number }
 *  Returns: { evidence: {title, snippet, source_id}[] }
 *
 *  Pluggable: the default implementation returns [] and relies on the Python
 *  service for RAG (which ships FAISS). Wire a remote retriever URL via
 *  RAG_SERVICE_URL if you want in-function retrieval.
 */
import type { Handler } from "@netlify/functions";

export const handler: Handler = async (event) => {
  if (event.httpMethod !== "POST") return { statusCode: 405, body: "method not allowed" };
  let body: any = {};
  try { body = JSON.parse(event.body || "{}"); }
  catch { return { statusCode: 400, body: JSON.stringify({ error: "invalid JSON" }) }; }
  const { query = "", k = 5 } = body;
  if (!query) return { statusCode: 400, body: JSON.stringify({ error: "missing query" }) };

  const url = process.env.RAG_SERVICE_URL;
  if (!url) {
    return json(200, { evidence: [] });
  }
  try {
    const r = await fetch(`${url.replace(/\/$/, "")}/retrieve?k=${k}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!r.ok) return json(200, { evidence: [] });
    const data = await r.json();
    return json(200, { evidence: Array.isArray(data.evidence) ? data.evidence : [] });
  } catch {
    return json(200, { evidence: [] });
  }
};

function json(status: number, body: unknown) {
  return { statusCode: status, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}
