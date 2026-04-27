"""Trend analysis for cache hit ratio over time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class TrendResult:
    """Result of a trend analysis over a series of snapshots."""
    direction: str          # 'improving', 'degrading', or 'stable'
    slope: float            # change in hit ratio per second
    start_ratio: float
    end_ratio: float
    sample_count: int

    def __str__(self) -> str:
        arrow = {"improving": "↑", "degrading": "↓", "stable": "→"}.get(
            self.direction, "?"
        )
        return (
            f"[{arrow} {self.direction.upper()}] "
            f"{self.start_ratio:.1%} → {self.end_ratio:.1%} "
            f"(slope={self.slope:+.4f}/s, n={self.sample_count})"
        )


def _linear_slope(xs: List[float], ys: List[float]) -> float:
    """Return the slope of the least-squares regression line."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    return num / den if den != 0.0 else 0.0


def analyze_trend(
    tracker: StatsTracker,
    stable_threshold: float = 0.001,
) -> Optional[TrendResult]:
    """Analyse the hit-ratio trend across all recorded snapshots.

    Returns ``None`` when fewer than two snapshots are available.
    ``stable_threshold`` (in hit-ratio units per second) controls the
    boundary between *stable* and *improving* / *degrading*.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return None

    t0 = snapshots[0].timestamp
    xs = [s.timestamp - t0 for s in snapshots]
    ys = [s.hit_ratio for s in snapshots]

    slope = _linear_slope(xs, ys)

    if slope > stable_threshold:
        direction = "improving"
    elif slope < -stable_threshold:
        direction = "degrading"
    else:
        direction = "stable"

    return TrendResult(
        direction=direction,
        slope=slope,
        start_ratio=ys[0],
        end_ratio=ys[-1],
        sample_count=len(snapshots),
    )
