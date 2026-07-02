"""Simple performance profiler for measuring execution times."""

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, List

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Profile function/method execution times with nested support."""

    def __init__(self):
        self._marks: Dict[str, List[float]] = defaultdict(list)
        self._stack: list = []

    @contextmanager
    def measure(self, label: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            self._marks[label].append(elapsed)

    def start(self, label: str):
        self._stack.append((label, time.perf_counter()))

    def stop(self) -> float:
        if not self._stack:
            return 0
        label, start = self._stack.pop()
        elapsed = (time.perf_counter() - start) * 1000
        self._marks[label].append(elapsed)
        return elapsed

    def report(self) -> Dict[str, dict]:
        result = {}
        for label, times in self._marks.items():
            if times:
                result[label] = {
                    "count": len(times),
                    "total_ms": round(sum(times), 2),
                    "avg_ms": round(sum(times) / len(times), 2),
                    "min_ms": round(min(times), 2),
                    "max_ms": round(max(times), 2),
                }
        return result

    def clear(self):
        self._marks.clear()
        self._stack.clear()

    def print_report(self):
        for label, stats in self.report().items():
            logger.info(
                "PROFILE [%s]: count=%d, avg=%.2fms, total=%.2fms, min=%.2fms, max=%.2fms",
                label, stats["count"], stats["avg_ms"], stats["total_ms"],
                stats["min_ms"], stats["max_ms"],
            )
