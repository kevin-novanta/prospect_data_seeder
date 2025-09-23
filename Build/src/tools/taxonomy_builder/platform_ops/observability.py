

"""platform_ops.observability

Tiny stdlib-only observability helpers suitable for CLI tools and CI logs.

API:
    inc(name: str, **labels) -> None
    time_block(name: str, **labels) -> ContextManager[None]
    flush_metrics(reset: bool = True) -> dict

Implementation notes:
- Thread-safe via a single module-level lock.
- Counters and timer stats are kept in memory until `flush_metrics()`.
- Output is a JSON-serializable dict; printing is left to caller.
"""
from __future__ import annotations

import json
import time
import threading
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Any

# ---------- Internals ----------
_lock = threading.Lock()

# Use stable keys (metric name + sorted labels) to aggregate
LabelKey = Tuple[Tuple[str, str], ...]


def _label_key(labels: Dict[str, Any] | None) -> LabelKey:
    if not labels:
        return tuple()
    # string-ify values to avoid JSON encoding surprises
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


@dataclass
class CounterStat:
    name: str
    labels: LabelKey
    count: int = 0


@dataclass
class TimerStat:
    name: str
    labels: LabelKey
    count: int = 0
    total_seconds: float = 0.0

    @property
    def avg_seconds(self) -> float:
        return (self.total_seconds / self.count) if self.count else 0.0


# Metric stores
_COUNTERS: Dict[Tuple[str, LabelKey], CounterStat] = {}
_TIMERS: Dict[Tuple[str, LabelKey], TimerStat] = {}


# ---------- Public API ----------

def inc(name: str, **labels: Any) -> None:
    """Increment a counter (by 1) for name+labels."""
    lk = _label_key(labels)
    key = (name, lk)
    with _lock:
        stat = _COUNTERS.get(key)
        if stat is None:
            stat = CounterStat(name=name, labels=lk, count=0)
            _COUNTERS[key] = stat
        stat.count += 1


@contextmanager
def time_block(name: str, **labels: Any):
    """Context manager to time a code block.

    Example:
        with time_block("parse", file="clutch_directory.html"):
            parse()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        lk = _label_key(labels)
        key = (name, lk)
        with _lock:
            stat = _TIMERS.get(key)
            if stat is None:
                stat = TimerStat(name=name, labels=lk)
                _TIMERS[key] = stat
            stat.count += 1
            stat.total_seconds += elapsed


def _serialize_labels(lk: LabelKey) -> Dict[str, str]:
    return {k: v for k, v in lk}


def _dump() -> dict:
    counters = [
        {
            "name": name,
            "labels": _serialize_labels(lk),
            "count": stat.count,
        }
        for (name, lk), stat in sorted(_COUNTERS.items(), key=lambda x: x[0][0])
    ]
    timers = [
        {
            "name": name,
            "labels": _serialize_labels(lk),
            "count": stat.count,
            "total_seconds": round(stat.total_seconds, 6),
            "avg_seconds": round(stat.avg_seconds, 6),
        }
        for (name, lk), stat in sorted(_TIMERS.items(), key=lambda x: x[0][0])
    ]
    return {"counters": counters, "timers": timers}


def flush_metrics(reset: bool = True) -> dict:
    """Return a JSON-serializable metrics snapshot. Optionally reset accumulators."""
    with _lock:
        snapshot = _dump()
        if reset:
            _COUNTERS.clear()
            _TIMERS.clear()
    # Caller may print to stdout if desired:
    # print(json.dumps({"metrics": snapshot}, indent=2))
    return snapshot


__all__ = ["inc", "time_block", "flush_metrics"]