"""Local FastAPI mirror of the Netlify Functions surface.

Useful for testing the frontend locally without Netlify:

    python scripts/run_local_api.py
    # http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import (
    CopilotService, InferRequest, SafetyCheckRequest, RetrieveRequest,
    InputValidationError, RateLimiter, RateLimitExceeded,
    configure_logging, set_request_context, safe_error_response,
    flags, Flag, validate_infer_request, MAX_CASE_PAYLOAD_BYTES
)
from hf.endpoint_client import HFEndpointClient
from rag.retriever import Retriever
from safety import RuleEngine

# 1. Bootstrap logging
configure_logging()
log = logging.getLogger("api")

app = FastAPI(title="criticalcare-copilot local API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("API_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"], allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    set_request_context(request_id=req_id)

    # Hard payload size limit
    if "content-length" in request.headers:
        if int(request.headers["content-length"]) > MAX_CASE_PAYLOAD_BYTES:
            err = safe_error_response("PAYLOAD_TOO_LARGE", reference_id=req_id)
            return JSONResponse(status_code=err["status"], content=err["body"])

    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        err = safe_error_response("INTERNAL_ERROR", reference_id=req_id, internal_exc=exc)
        return JSONResponse(status_code=err["status"], content=err["body"])


def _service() -> CopilotService:
    client = HFEndpointClient() if os.getenv("HF_ENDPOINT_URL") else None
    retriever: Retriever | None = None
    try:
        retriever = Retriever.from_default()
    except Exception:
        log.warning("Retriever unavailable; RAG will be disabled.")
    return CopilotService(
        rule_engine=RuleEngine(),
        retriever=retriever,
        model_client=client,
    )


SERVICE = _service()
RATE_LIMITER = RateLimiter.from_env()


def check_rate_limit(request: Request, route: str) -> None:
    if flags.is_enabled(Flag.RATE_LIMIT):
        client_ip = request.client.host if request.client else "unknown"
        try:
            RATE_LIMITER.check(route, key=client_ip)
        except RateLimitExceeded as exc:
            raise HTTPException(status_code=429, detail=str(exc))


@app.exception_handler(InputValidationError)
async def validation_exception_handler(request: Request, exc: InputValidationError):
    req_id = uuid.uuid4().hex[:12]
    log.warning("validation_error problems=%s", exc.problems, extra={"data": {"problems": exc.problems}})
    err = safe_error_response("INPUT_VALIDATION_FAILED", reference_id=req_id, extra_detail=str(exc.problems))
    return JSONResponse(status_code=err["status"], content=err["body"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 429:
        err = safe_error_response("RATE_LIMIT_EXCEEDED")
        return JSONResponse(status_code=err["status"], content=err["body"])
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/api/health")
def health(request: Request) -> dict[str, Any]:
    check_rate_limit(request, "health")
    return {
        "ok": True,
        "model_endpoint": "reachable" if os.getenv("HF_ENDPOINT_URL") else "unreachable",
        "has_token": bool(os.getenv("HF_API_TOKEN")),
        "model_revision": os.getenv("HF_MODEL_REVISION", "dev"),
        "flags": flags.snapshot(),
    }


@app.post("/api/infer")
def infer(req: dict[str, Any], request: Request) -> dict[str, Any]:
    check_rate_limit(request, "infer")
    # Strict validation
    valid_req = validate_infer_request(req)
    
    # Feature flag for model calling
    use_model = valid_req.use_model
    if os.getenv("ENABLE_MODEL_CALL") == "false":
        use_model = False

    return SERVICE.run(
        valid_req.case, 
        task=valid_req.task, 
        use_rag=valid_req.use_rag, 
        use_model=use_model
    )


@app.post("/api/safety_check")
def safety(req: SafetyCheckRequest, request: Request) -> dict[str, Any]:
    check_rate_limit(request, "safety_check")
    return SERVICE.safety_only(req.case)


@app.post("/api/retrieve_context")
def retrieve(req: RetrieveRequest, request: Request) -> dict[str, Any]:
    check_rate_limit(request, "retrieve_context")
    if SERVICE.retriever is None or not flags.is_enabled(Flag.RAG_ENABLED):
        return {"evidence": []}
    return {"evidence": SERVICE.retriever.retrieve_evidence(req.query)}


@app.post("/api/audit_log")
def audit(record: dict[str, Any], request: Request) -> dict[str, Any]:
    check_rate_limit(request, "audit_log")
    # Simple file-backed sink; swap for your org's sink in prod.
    path = os.getenv("AUDIT_LOG_PATH", "data/processed/audit.log")
    if path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(record) + "\n")
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "scripts.run_local_api:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
