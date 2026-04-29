"""Correlate hit ratio trends across two StatsTracker instances."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class CorrelationResult:
    """Result of correlating two snapshot series."""

    pearson_r: float
    n: int
    interpretation: str

    def __str__(self) -> str:
        return (
            f"CorrelationResult(r={self.pearson_r:.4f}, n={self.n}, "
            f"interpretation={self.interpretation!r})"
        )


def _interpret(r: float) -> str:
    abs_r = abs(r)
    if abs_r >= 0.9:
        direction = "positive" if r > 0 else "negative"
        return f"very strong {direction} correlation"
    if abs_r >= 0.7:
        direction = "positive" if r > 0 else "negative"
        return f"strong {direction} correlation"
    if abs_r >= 0.4:
        direction = "positive" if r > 0 else "negative"
        return f"moderate {direction} correlation"
    if abs_r >= 0.2:
        direction = "positive" if r > 0 else "negative"
        return f"weak {direction} correlation"
    return "little or no correlation"


def correlate_trackers(
    tracker_a: StatsTracker,
    tracker_b: StatsTracker,
) -> Optional[CorrelationResult]:
    """Compute the Pearson correlation coefficient between the hit ratios
    of two trackers.

    Snapshots are paired by position (oldest-first). Only the overlapping
    length is used. Returns ``None`` when fewer than two paired points exist.
    """
    snaps_a = tracker_a.history()
    snaps_b = tracker_b.history()

    n = min(len(snaps_a), len(snaps_b))
    if n < 2:
        return None

    xs = [s.stats.hit_ratio for s in snaps_a[:n]]
    ys = [s.stats.hit_ratio for s in snaps_b[:n]]

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    std_x = (sum((x - mean_x) ** 2 for x in xs)) ** 0.5
    std_y = (sum((y - mean_y) ** 2 for y in ys)) ** 0.5

    if std_x == 0.0 or std_y == 0.0:
        return None

    r = cov / (std_x * std_y)
    r = max(-1.0, min(1.0, r))

    return CorrelationResult(pearson_r=r, n=n, interpretation=_interpret(r))
