

"""Simple token-bucket rate limiter (stdlib-only).

Design goals:
- Global limiter for the CLI, thread-safe.
- Token bucket with steady refill using time.monotonic().
- Non-blocking probe (try_acquire) and a convenience acquire() that sleeps as needed.

Usage:
    from .rate_limit import configure_global, acquire
    configure_global(rps=2.0, burst=4)
    acquire()  # will sleep to respect RPS
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class _Bucket:
    capacity: float
    tokens: float
    last_refill: float


class RateLimiter:
    def __init__(self, rps: float = 5.0, burst: int = 5) -> None:
        if rps <= 0:
            raise ValueError("rps must be > 0")
        if burst <= 0:
            raise ValueError("burst must be > 0")
        self._rps = float(rps)
        self._lock = threading.Lock()
        now = time.monotonic()
        self._bucket = _Bucket(capacity=float(burst), tokens=float(burst), last_refill=now)

    # --- internal ---
    def _refill_locked(self, now: float) -> None:
        b = self._bucket
        elapsed = now - b.last_refill
        if elapsed <= 0:
            return
        b.tokens = min(b.capacity, b.tokens + elapsed * self._rps)
        b.last_refill = now

    # --- public ---
    @property
    def rps(self) -> float:
        return self._rps

    def try_acquire(self) -> float:
        """Attempt to take one token.

        Returns
        -------
        float
            0.0 if a token was acquired immediately; otherwise, the number of
            seconds the caller should wait before trying again.
        """
        now = time.monotonic()
        with self._lock:
            self._refill_locked(now)
            b = self._bucket
            if b.tokens >= 1.0:
                b.tokens -= 1.0
                return 0.0
            # compute time until next token
            missing = 1.0 - b.tokens
            wait = max(0.0, missing / self._rps)
            return wait

    def acquire(self) -> None:
        """Block (sleep) until one token is available, then consume it."""
        while True:
            wait = self.try_acquire()
            if wait <= 0:
                return
            # sleep a hair less than wait to reduce overshoot on wake
            time.sleep(wait)


# ---- Module-level global limiter ----
_GLOBAL: Optional[RateLimiter] = None


def configure_global(rps: float = 5.0, burst: int = 5) -> None:
    global _GLOBAL
    _GLOBAL = RateLimiter(rps=rps, burst=burst)


def acquire() -> None:
    """Acquire a token from the global limiter (sleeping if necessary).

    If the global limiter hasn't been configured, a default of 5 rps / burst 5 is used.
    """
    global _GLOBAL
    if _GLOBAL is None:
        _GLOBAL = RateLimiter()
    _GLOBAL.acquire()


__all__ = ["RateLimiter", "configure_global", "acquire"]