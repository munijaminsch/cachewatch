"""Smoothing utilities for hit-ratio time series data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class SmoothedPoint:
    """A single smoothed data point."""

    timestamp: float
    raw_ratio: Optional[float]
    smoothed_ratio: Optional[float]

    def __str__(self) -> str:
        raw = f"{self.raw_ratio:.4f}" if self.raw_ratio is not None else "N/A"
        smoothed = (
            f"{self.smoothed_ratio:.4f}" if self.smoothed_ratio is not None else "N/A"
        )
        return f"ts={self.timestamp:.1f} raw={raw} smoothed={smoothed}"


def moving_average(
    snapshots: list, window: int = 3
) -> List[SmoothedPoint]:
    """Compute a simple moving average over hit ratios.

    Args:
        snapshots: List of CacheStats snapshots.
        window: Number of points to average over (must be >= 1).

    Returns:
        List of SmoothedPoint instances in chronological order.
    """
    if window < 1:
        raise ValueError("window must be >= 1")

    result: List[SmoothedPoint] = []
    for i, snap in enumerate(snapshots):
        raw = snap.hit_ratio
        start = max(0, i - window + 1)
        window_snaps = snapshots[start : i + 1]
        ratios = [s.hit_ratio for s in window_snaps if s.hit_ratio is not None]
        smoothed = sum(ratios) / len(ratios) if ratios else None
        result.append(
            SmoothedPoint(
                timestamp=snap.timestamp,
                raw_ratio=raw,
                smoothed_ratio=smoothed,
            )
        )
    return result


def smooth_tracker(
    tracker: StatsTracker, window: int = 3
) -> List[SmoothedPoint]:
    """Apply moving-average smoothing to all snapshots in a tracker."""
    snapshots = tracker.history()
    return moving_average(snapshots, window=window)
