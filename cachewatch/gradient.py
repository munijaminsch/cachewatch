"""Compute the rate-of-change gradient across cache hit ratio snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class GradientPoint:
    """A single gradient measurement between two consecutive snapshots."""

    timestamp: float
    hit_ratio: Optional[float]
    gradient: Optional[float]  # change in hit_ratio per second

    def __str__(self) -> str:
        ts = f"{self.timestamp:.2f}"
        ratio = f"{self.hit_ratio:.4f}" if self.hit_ratio is not None else "N/A"
        grad = (
            f"{self.gradient:+.6f}" if self.gradient is not None else "N/A"
        )
        return f"GradientPoint(ts={ts}, ratio={ratio}, gradient={grad})"


def compute_gradient(tracker: StatsTracker) -> List[GradientPoint]:
    """Return per-snapshot gradient (Δratio / Δtime) for all snapshots.

    The first point always has ``gradient=None`` because there is no
    preceding snapshot to compare against.

    Args:
        tracker: A :class:`StatsTracker` whose history is used.

    Returns:
        A list of :class:`GradientPoint` objects, one per snapshot.
        Returns an empty list when the tracker has no history.
    """
    snapshots = tracker.history()
    if not snapshots:
        return []

    points: List[GradientPoint] = []

    first = snapshots[0]
    points.append(
        GradientPoint(
            timestamp=first.timestamp,
            hit_ratio=first.hit_ratio,
            gradient=None,
        )
    )

    for prev, curr in zip(snapshots, snapshots[1:]):
        dt = curr.timestamp - prev.timestamp
        if dt <= 0 or prev.hit_ratio is None or curr.hit_ratio is None:
            gradient: Optional[float] = None
        else:
            gradient = (curr.hit_ratio - prev.hit_ratio) / dt

        points.append(
            GradientPoint(
                timestamp=curr.timestamp,
                hit_ratio=curr.hit_ratio,
                gradient=gradient,
            )
        )

    return points
