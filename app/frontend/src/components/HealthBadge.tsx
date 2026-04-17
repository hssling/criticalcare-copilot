import { useEffect, useState } from "react";
import { health } from "../lib/api";

export default function HealthBadge() {
  const [s, setS] = useState<{ ok?: boolean; model_endpoint?: string }>({});
  useEffect(() => {
    let alive = true;
    health().then((x) => alive && setS(x)).catch(() => alive && setS({ ok: false }));
    return () => { alive = false; };
  }, []);
  const endpoint = s.model_endpoint ?? "unknown";
  const ok = s.ok && endpoint === "reachable";
  return (
    <span className={`badge ${ok ? "badge-low" : "badge-high"}`}>
      {ok ? "Endpoint: reachable" : `Endpoint: ${endpoint}`}
    </span>
  );
}
