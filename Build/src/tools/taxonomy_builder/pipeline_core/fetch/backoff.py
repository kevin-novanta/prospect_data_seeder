

"""Exponential backoff helpers (offline-first, stdlib-only).

Public API
----------
- should_retry(status: int) -> bool
    Return True for 429 and 5xx HTTP statuses.

- next_sleep(retry: int, base: float = 0.5, cap: float = 30.0, jitter: str = "full") -> float
    Compute the next backoff sleep in seconds using exponential growth
    with optional jitter. Jitter strategies:
        - "none": no jitter, pure exponential
        - "full": full jitter in [0, exp]  (AWS recommended)
        - "equal": equal jitter in [exp/2, exp]

Notes
-----
- `retry` is the zero-based attempt number (0 for first retry).
- The returned sleep is always clamped to [0, cap].
"""
from __future__ import annotations

import math
import random
from typing import Final

# Which statuses are considered retryable
RETRYABLE_STATUS_LOWER: Final[int] = 500
RETRYABLE_STATUS_UPPER: Final[int] = 600  # exclusive upper bound


def should_retry(status: int) -> bool:
    """Return True for 429 and 5xx statuses."""
    if status == 429:
        return True
    return RETRYABLE_STATUS_LOWER <= int(status) < RETRYABLE_STATUS_UPPER


def next_sleep(
    retry: int,
    base: float = 0.5,
    cap: float = 30.0,
    jitter: str = "full",
) -> float:
    """Compute exponential backoff sleep with jitter.

    Parameters
    ----------
    retry : int
        Zero-based retry count (0 for the first retry).
    base : float
        Base delay in seconds. Default 0.5.
    cap : float
        Maximum delay in seconds. Default 30.0.
    jitter : str
        One of {"none", "full", "equal"}. Default "full".

    Returns
    -------
    float
        Sleep duration in seconds (>= 0).
    """
    if retry < 0:
        retry = 0
    if base < 0:
        base = 0.0
    if cap <= 0:
        return 0.0

    # Exponential growth: base * 2^retry (clamped to cap)
    exp = min(cap, base * (2.0 ** retry))

    # Jitter strategies
    j = jitter.lower() if isinstance(jitter, str) else "full"
    if j == "none":
        delay = exp
    elif j == "equal":
        half = exp / 2.0
        delay = half + random.random() * half
    else:  # "full" and unknown -> full jitter
        delay = random.random() * exp

    # Guard against NaN or inf
    if not (delay >= 0.0 and math.isfinite(delay)):
        return 0.0
    return max(0.0, min(delay, cap))


__all__ = [
    "should_retry",
    "next_sleep",
    "RETRYABLE_STATUS_LOWER",
    "RETRYABLE_STATUS_UPPER",
]