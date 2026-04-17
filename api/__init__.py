"""API layer: request/response models, orchestration, and hardening modules."""
from .request_models import InferRequest, SafetyCheckRequest, RetrieveRequest
from .response_models import CopilotResponse, Alert, Evidence
from .service import CopilotService
from .validation import (
    InputValidationError,
    sanitize_case,
    validate_infer_request,
    MAX_CASE_PAYLOAD_BYTES,
)
from .redaction import redact_dict, redact_case_for_logging
from .audit import AuditAction, AuditOutcome, AuditEvent, emit_audit_event
from .rate_limiter import RateLimiter, RateLimitExceeded
from .errors import safe_error_response
from .feature_flags import flags, Flag
from .logging_config import configure_logging, set_request_context

__all__ = [
    "InferRequest", "SafetyCheckRequest", "RetrieveRequest",
    "CopilotResponse", "Alert", "Evidence",
    "CopilotService",
    # Hardening
    "InputValidationError", "sanitize_case", "validate_infer_request",
    "MAX_CASE_PAYLOAD_BYTES",
    "redact_dict", "redact_case_for_logging",
    "AuditAction", "AuditOutcome", "AuditEvent", "emit_audit_event",
    "RateLimiter", "RateLimitExceeded",
    "safe_error_response",
    "flags", "Flag",
    "configure_logging", "set_request_context",
]
