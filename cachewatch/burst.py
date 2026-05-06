"""Burst detection: identify rapid short-term spikes in hit ratio change."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class BurstResult:
    """Represents a detected burst event in the hit ratio time series."""

    timestamp: float
    hit_ratio: float
    delta: float          # change from previous snapshot
    direction: str        # 'up' or 'down'

    def __str__(self) -> str:
        sign = "+" if self.delta >= 0 else ""
        return (
            f"Burst({self.direction}) at ts={self.timestamp:.1f} "
            f"ratio={self.hit_ratio:.4f} delta={sign}{self.delta:.4f}"
        )


def detect_bursts(
    tracker: StatsTracker,
    threshold: float = 0.10,
) -> List[BurstResult]:
    """Return snapshots where the hit ratio changed by *threshold* or more
    compared to the immediately preceding snapshot.

    Parameters
    ----------
    tracker:
        Source of recorded snapshots.
    threshold:
        Minimum absolute change in hit ratio to qualify as a burst.
        Defaults to 0.10 (10 percentage points).

    Returns
    -------
    List of :class:`BurstResult` in chronological order.  Empty when fewer
    than two snapshots are available or no burst is detected.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return []

    bursts: List[BurstResult] = []
    for prev, curr in zip(snapshots, snapshots[1:]):
        prev_ratio: Optional[float] = prev.hit_ratio
        curr_ratio: Optional[float] = curr.hit_ratio
        if prev_ratio is None or curr_ratio is None:
            continue
        delta = curr_ratio - prev_ratio
        if abs(delta) >= threshold:
            bursts.append(
                BurstResult(
                    timestamp=curr.timestamp,
                    hit_ratio=curr_ratio,
                    delta=delta,
                    direction="up" if delta > 0 else "down",
                )
            )
    return bursts
