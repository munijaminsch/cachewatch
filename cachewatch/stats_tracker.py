"""Tracks rolling cache statistics and computes deltas between snapshots."""

from collections import deque
from typing import Deque, Optional, Tuple

from cachewatch.redis_collector import CacheStats


MAX_HISTORY = 120  # keep up to 120 data points (~2 min at 1s interval)


class StatsTracker:
    """Maintains a history of CacheStats snapshots and derives metrics."""

    def __init__(self, max_history: int = MAX_HISTORY):
        self._history: Deque[CacheStats] = deque(maxlen=max_history)

    def record(self, snapshot: CacheStats) -> None:
        """Append a new snapshot to the history."""
        self._history.append(snapshot)

    @property
    def latest(self) -> Optional[CacheStats]:
        return self._history[-1] if self._history else None

    @property
    def history(self) -> list:
        return list(self._history)

    def delta(self) -> Optional[Tuple[int, int]]:
        """Return (hits_delta, misses_delta) between the last two snapshots."""
        if len(self._history) < 2:
            return None
        prev, curr = self._history[-2], self._history[-1]
        hits_delta = max(curr.hits - prev.hits, 0)
        misses_delta = max(curr.misses - prev.misses, 0)
        return hits_delta, misses_delta

    def hit_ratio_series(self) -> list:
        """Return a list of cumulative hit ratios for sparkline rendering."""
        return [s.hit_ratio for s in self._history]

    def requests_per_second(self) -> float:
        """Estimate requests/second based on the last two snapshots."""
        if len(self._history) < 2:
            return 0.0
        prev, curr = self._history[-2], self._history[-1]
        elapsed = curr.timestamp - prev.timestamp
        if elapsed <= 0:
            return 0.0
        total_delta = (curr.hits + curr.misses) - (prev.hits + prev.misses)
        return max(total_delta, 0) / elapsed
