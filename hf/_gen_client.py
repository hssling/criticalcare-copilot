"""One-shot script: regenerate hf/endpoint_client.py with proper template."""
from pathlib import Path

SYS = "<" + "|system|" + ">"
USR = "<" + "|user|" + ">"
AST = "<" + "|assistant|" + ">"

TPL_VAR = (
    f'SYSTEM_USER_TEMPLATE = (\n'
    f'    "{SYS}\\n{{system}}\\n\\n{{safety}}\\n"\n'
    f'    "{USR}\\n{{user}}\\n"\n'
    f'    "{AST}\\n"\n'
    f')\n'
)

BODY = '''"""HTTP client for the HF Inference Endpoint + an optional local client.

``HFEndpointClient`` is used by the Python local API and by tests.
Netlify Functions speak HTTPS to the same endpoint directly from TS
(see ``app/functions/infer.ts``).

Production hardening (v0.2):
  * Configurable timeout (``HF_TIMEOUT_S``, default 45 s).
  * Configurable max retries (``HF_MAX_RETRIES``, default 2).
  * Exponential back-off with jitter.
  * Structured logging on every attempt / failure.
  * Never surfaces raw exception to callers -- returns ``{{}}``.
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

log = logging.getLogger(__name__)


{tpl_var}

@dataclass
class HFEndpointClient:
    url: str | None = None
    token: str | None = None
    timeout: float = 45.0
    max_retries: int = 2

    def __post_init__(self):
        self.url = self.url or os.getenv("HF_ENDPOINT_URL")
        self.token = self.token or os.getenv("HF_API_TOKEN")
        self.timeout = float(os.getenv("HF_TIMEOUT_S", str(self.timeout)))
        self.max_retries = int(os.getenv("HF_MAX_RETRIES", str(self.max_retries)))

    def _headers(self) -> dict[str, str]:
        h = {{"Content-Type": "application/json"}}
        if self.token:
            h["Authorization"] = f"Bearer {{self.token}}"
        return h

    def generate(self, *, system_prompt: str, safety_prompt: str,
                 case: dict[str, Any], task: str, evidence: list[dict] | None = None) -> dict[str, Any]:
        if not self.url:
            log.warning("hf_endpoint_url_not_set -- skipping model call")
            return {{}}
        user = json.dumps({{"task": task, "case": case, "evidence": evidence or []}}, ensure_ascii=False)
        prompt = SYSTEM_USER_TEMPLATE.format(system=system_prompt, safety=safety_prompt, user=user)

        payload = {{
            "inputs": prompt,
            "parameters": {{
                "max_new_tokens": 1024,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_full_text": False,
            }},
        }}

        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                log.info(
                    "hf_request attempt=%d/%d timeout=%.1fs url=%s",
                    attempt + 1, self.max_retries + 1, self.timeout,
                    (self.url or "")[:60],
                    extra={{"data": {{"attempt": attempt + 1}}}},
                )
                with httpx.Client(timeout=self.timeout) as client:
                    r = client.post(self.url, headers=self._headers(), json=payload)
                r.raise_for_status()
                data = r.json()
                text = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", "")
                log.info("hf_request_ok status=%d", r.status_code)
                return _coerce_json(text)
            except httpx.TimeoutException as e:
                last_exc = e
                log.warning(
                    "hf_timeout attempt=%d/%d delay=%.1fs",
                    attempt + 1, self.max_retries + 1, delay,
                )
            except httpx.HTTPStatusError as e:
                last_exc = e
                log.warning(
                    "hf_http_error attempt=%d/%d status=%d",
                    attempt + 1, self.max_retries + 1, e.response.status_code,
                )
                # Don't retry 4xx (client errors)
                if 400 <= e.response.status_code < 500:
                    break
            except Exception as e:
                last_exc = e
                log.warning(
                    "hf_request_error attempt=%d/%d exc=%s",
                    attempt + 1, self.max_retries + 1, e,
                )
            # Exponential back-off with jitter
            jitter = delay * random.uniform(0.5, 1.5)
            time.sleep(jitter)
            delay = min(delay * 2, 30.0)

        log.error(
            "hf_all_retries_exhausted retries=%d last_exc=%s",
            self.max_retries, last_exc,
        )
        # Fail soft -- service layer degrades to rules-only.
        return {{}}


def _coerce_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of the last JSON object in a string."""
    if not text:
        return {{}}
    text = text.strip()
    # try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # find the last balanced {{...}} block
    start = text.rfind("{{")
    if start == -1:
        return {{}}
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{{":
            depth += 1
        elif c == "}}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return {{}}
    return {{}}


class LocalHFClient:
    """Loads a local base/adapter and runs transformers.generate.
    Intentionally minimal; used by evaluate_checkpoint --no-mock."""
    def __init__(self, *, adapter: str | None = None, base: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        base = base or "google/gemma-4-e4b-it"
        self._tok = AutoTokenizer.from_pretrained(base, use_fast=True)
        if self._tok.pad_token is None:
            self._tok.pad_token = self._tok.eos_token
        model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.bfloat16)
        if adapter:
            model = PeftModel.from_pretrained(model, adapter)
        self._model = model
        self._device = next(model.parameters()).device

    def generate(self, *, system_prompt, safety_prompt, case, task, evidence):
        import torch
        user = json.dumps({{"task": task, "case": case, "evidence": evidence or []}}, ensure_ascii=False)
        prompt = SYSTEM_USER_TEMPLATE.format(system=system_prompt, safety=safety_prompt, user=user)
        ids = self._tok(prompt, return_tensors="pt").to(self._device)
        with torch.no_grad():
            out = self._model.generate(**ids, max_new_tokens=1024, temperature=0.2, top_p=0.9,
                                       do_sample=False, pad_token_id=self._tok.pad_token_id)
        text = self._tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        return _coerce_json(text)
'''.format(tpl_var=TPL_VAR)

target = Path(__file__).parent / "endpoint_client.py"
target.write_text(BODY, encoding="utf-8")
print(f"Wrote {target} ({target.stat().st_size} bytes)")
