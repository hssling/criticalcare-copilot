import { useCallback, useEffect, useState } from "react";
import type { ClinicalCase } from "../types";

const KEY = "ccc.activeCase";

export function useLocalCase(): [ClinicalCase | null, (c: ClinicalCase | null) => void] {
  const [c, setC] = useState<ClinicalCase | null>(null);
  useEffect(() => {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      try { setC(JSON.parse(raw)); } catch { /* ignore */ }
    }
  }, []);
  const set = useCallback((next: ClinicalCase | null) => {
    setC(next);
    if (next) localStorage.setItem(KEY, JSON.stringify(next));
    else localStorage.removeItem(KEY);
  }, []);
  return [c, set];
}
