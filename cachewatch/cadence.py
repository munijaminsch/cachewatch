"""Cadence detection: measure the average interval between snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class CadenceResult:
    """Result of cadence analysis over a sequence of snapshots."""

    count: int
    min_interval: Optional[float]   # seconds
    max_interval: Optional[float]   # seconds
    mean_interval: Optional[float]  # seconds
    std_dev: Optional[float]        # seconds
    is_regular: bool                # True when std_dev < 20 % of mean

    def __str__(self) -> str:
        if self.mean_interval is None:
            return "CadenceResult(insufficient data)"
        regularity = "regular" if self.is_regular else "irregular"
        return (
            f"CadenceResult(count={self.count}, "
            f"mean={self.mean_interval:.2f}s, "
            f"min={self.min_interval:.2f}s, "
            f"max={self.max_interval:.2f}s, "
            f"std={self.std_dev:.2f}s, "
            f"{regularity})"
        )


def _std_dev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def compute_cadence(tracker: StatsTracker) -> Optional[CadenceResult]:
    """Compute cadence statistics from the snapshot timestamps in *tracker*.

    Returns ``None`` when the tracker holds fewer than two snapshots.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return None

    timestamps = [s.timestamp for s in snapshots]
    intervals: List[float] = [
        timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)
    ]

    mean = sum(intervals) / len(intervals)
    std = _std_dev(intervals, mean)
    is_regular = (std / mean) < 0.20 if mean > 0 else True

    return CadenceResult(
        count=len(snapshots),
        min_interval=min(intervals),
        max_interval=max(intervals),
        mean_interval=mean,
        std_dev=std,
        is_regular=is_regular,
    )
