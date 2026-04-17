"""Rate-limiting scaffolding.

Provides an in-process sliding-window rate limiter suitable for a single
FastAPI worker. For production behind multiple workers or pods, replace the
back-end with Redis (``_RedisBackend``) or a sidecar like Envoy.

Usage in the API layer::

    from api.rate_limiter import RateLimiter, RateLimitExceeded
    limiter = RateLimiter.from_env()

    @app.post("/api/infer")
    def infer(req):
        limiter.check("infer", key=client_ip(req))
        ...

Environment variables (all optional):
  ``RATE_LIMIT_RPM``  — requests per minute per key (default 30).
  ``RATE_LIMIT_BURST`` — short-burst cap (default 5 within 2 s).
"""
from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Protocol


class RateLimitExceeded(Exception):
    """Raised when a caller exceeds the configured rate limit."""

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded; retry after {retry_after:.1f}s")


# ---------------------------------------------------------------------------
# Backend protocol (swap for Redis in prod)
# ---------------------------------------------------------------------------

class _Backend(Protocol):
    def is_allowed(self, key: str, rpm: int, burst: int) -> tuple[bool, float]: ...


@dataclass
class _InMemoryBackend:
    """Thread-safe sliding-window counter. Suitable for single-process."""
    _windows: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    _lock: Lock = field(default_factory=Lock)

    def is_allowed(self, key: str, rpm: int, burst: int) -> tuple[bool, float]:
        now = time.monotonic()
        with self._lock:
            window = self._windows[key]
            # Purge entries older than 60 s
            cutoff = now - 60.0
            self._windows[key] = window = [t for t in window if t > cutoff]

            if len(window) >= rpm:
                retry_after = 60.0 - (now - window[0])
                return False, max(retry_after, 0.1)

            # Burst check (last 2 s)
            burst_cutoff = now - 2.0
            recent = sum(1 for t in window if t > burst_cutoff)
            if recent >= burst:
                return False, 2.0

            window.append(now)
            return True, 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class RateLimiter:
    rpm: int = 30
    burst: int = 5
    _backend: _Backend = field(default_factory=_InMemoryBackend)

    @classmethod
    def from_env(cls) -> "RateLimiter":
        return cls(
            rpm=int(os.getenv("RATE_LIMIT_RPM", "30")),
            burst=int(os.getenv("RATE_LIMIT_BURST", "5")),
        )

    def check(self, route: str, *, key: str = "global") -> None:
        """Raise ``RateLimitExceeded`` if *key* has exceeded the limit."""
        composite_key = f"{route}:{key}"
        allowed, retry_after = self._backend.is_allowed(composite_key, self.rpm, self.burst)
        if not allowed:
            raise RateLimitExceeded(retry_after)
