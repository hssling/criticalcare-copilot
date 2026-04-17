"""Feature flags for model versions and runtime capabilities.

Flags are read from environment variables at startup and can be hot-swapped
via ``set_flag`` (useful for A/B testing or gradual rollouts).

Usage::

    from api.feature_flags import flags, Flag
    if flags.is_enabled(Flag.MODEL_V2):
        ...

Environment variables (all optional, default ``false`` unless noted):
  ``FF_MODEL_V2``          — route to v2 model endpoint.
  ``FF_RAG_ENABLED``       — enable RAG retrieval (default ``true``).
  ``FF_STRICT_GUARDRAILS`` — enable strict-mode guardrails (default ``true``).
  ``FF_AUDIT_VERBOSE``     — include full case in audit events.
  ``FF_RATE_LIMIT``        — enforce API rate limiting.
"""
from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)


class Flag(str, Enum):
    MODEL_V2 = "FF_MODEL_V2"
    RAG_ENABLED = "FF_RAG_ENABLED"
    STRICT_GUARDRAILS = "FF_STRICT_GUARDRAILS"
    AUDIT_VERBOSE = "FF_AUDIT_VERBOSE"
    RATE_LIMIT = "FF_RATE_LIMIT"


# Defaults: flags that should be ON unless explicitly disabled
_DEFAULTS: dict[Flag, bool] = {
    Flag.MODEL_V2: False,
    Flag.RAG_ENABLED: True,
    Flag.STRICT_GUARDRAILS: True,
    Flag.AUDIT_VERBOSE: False,
    Flag.RATE_LIMIT: False,
}


class FeatureFlags:
    """Thin wrapper around a flag store."""

    def __init__(self) -> None:
        self._overrides: dict[Flag, bool] = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        for flag in Flag:
            raw = os.getenv(flag.value)
            if raw is not None:
                self._overrides[flag] = raw.lower() in ("1", "true", "yes", "on")

    def is_enabled(self, flag: Flag) -> bool:
        if flag in self._overrides:
            return self._overrides[flag]
        return _DEFAULTS.get(flag, False)

    def set_flag(self, flag: Flag, enabled: bool) -> None:
        """Runtime override — useful for A/B experiments or blue/green."""
        prev = self.is_enabled(flag)
        self._overrides[flag] = enabled
        log.info(
            "feature_flag_changed flag=%s prev=%s new=%s",
            flag.value, prev, enabled,
            extra={"data": {"flag": flag.value, "prev": prev, "new": enabled}},
        )

    def snapshot(self) -> dict[str, bool]:
        """Return a dict of all flag states (for health endpoint / audit)."""
        return {f.value: self.is_enabled(f) for f in Flag}


# Singleton — import and use directly
flags = FeatureFlags()
