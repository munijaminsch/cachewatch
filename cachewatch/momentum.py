"""Compute rate-of-change (momentum) of hit ratios over time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class MomentumPoint:
    """A single momentum measurement."""

    timestamp: float
    hit_ratio: Optional[float]
    momentum: Optional[float]  # change per second vs previous point

    def __str__(self) -> str:
        ratio_str = f"{self.hit_ratio:.4f}" if self.hit_ratio is not None else "N/A"
        mom_str = (
            f"{self.momentum:+.4f}" if self.momentum is not None else "N/A"
        )
        return f"ts={self.timestamp:.1f} ratio={ratio_str} momentum={mom_str}"


def compute_momentum(tracker: StatsTracker) -> List[MomentumPoint]:
    """Return momentum points for every snapshot in *tracker*.

    Momentum for the first snapshot is always ``None``.  For subsequent
    snapshots it is ``(ratio_n - ratio_{n-1}) / (ts_n - ts_{n-1})``.
    If the time delta between two consecutive snapshots is zero the
    momentum for that point is set to ``None``.
    """
    snapshots = tracker.history()
    if not snapshots:
        return []

    points: List[MomentumPoint] = []
    prev = snapshots[0]
    points.append(
        MomentumPoint(
            timestamp=prev.timestamp,
            hit_ratio=prev.hit_ratio,
            momentum=None,
        )
    )

    for snap in snapshots[1:]:
        dt = snap.timestamp - prev.timestamp
        if dt == 0 or prev.hit_ratio is None or snap.hit_ratio is None:
            mom: Optional[float] = None
        else:
            mom = (snap.hit_ratio - prev.hit_ratio) / dt
        points.append(
            MomentumPoint(
                timestamp=snap.timestamp,
                hit_ratio=snap.hit_ratio,
                momentum=mom,
            )
        )
        prev = snap

    return points
