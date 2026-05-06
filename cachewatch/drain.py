"""Drain detection: identify periods of sustained cache hit ratio decline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class DrainResult:
    """Represents a detected drain period where hit ratio continuously declined."""

    start_ts: float
    end_ts: float
    start_ratio: float
    end_ratio: float
    steps: int

    @property
    def duration(self) -> float:
        """Duration of the drain period in seconds."""
        return self.end_ts - self.start_ts

    @property
    def total_drop(self) -> float:
        """Total drop in hit ratio over the drain period."""
        return self.start_ratio - self.end_ratio

    def __str__(self) -> str:
        return (
            f"DrainResult(start={self.start_ts:.1f}, end={self.end_ts:.1f}, "
            f"drop={self.total_drop:.4f}, steps={self.steps})"
        )


def detect_drains(
    tracker: StatsTracker,
    min_steps: int = 3,
    min_drop: float = 0.05,
) -> List[DrainResult]:
    """Detect sustained declining periods in the hit ratio history.

    A drain is a consecutive sequence of snapshots where the hit ratio
    decreases monotonically for at least *min_steps* steps and the total
    drop is at least *min_drop*.

    Args:
        tracker: The stats tracker containing snapshot history.
        min_steps: Minimum number of consecutive declining steps required.
        min_drop: Minimum total drop in hit ratio to qualify as a drain.

    Returns:
        A list of DrainResult objects, one per detected drain period.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return []

    results: List[DrainResult] = []
    drain_start: Optional[int] = None

    for i in range(1, len(snapshots)):
        prev_ratio = snapshots[i - 1].hit_ratio
        curr_ratio = snapshots[i].hit_ratio

        if curr_ratio < prev_ratio:
            if drain_start is None:
                drain_start = i - 1
        else:
            if drain_start is not None:
                steps = i - drain_start
                start_snap = snapshots[drain_start]
                end_snap = snapshots[i - 1]
                drop = start_snap.hit_ratio - end_snap.hit_ratio
                if steps >= min_steps and drop >= min_drop:
                    results.append(
                        DrainResult(
                            start_ts=start_snap.timestamp,
                            end_ts=end_snap.timestamp,
                            start_ratio=start_snap.hit_ratio,
                            end_ratio=end_snap.hit_ratio,
                            steps=steps,
                        )
                    )
                drain_start = None

    # Handle drain that extends to the last snapshot
    if drain_start is not None:
        steps = len(snapshots) - 1 - drain_start
        start_snap = snapshots[drain_start]
        end_snap = snapshots[-1]
        drop = start_snap.hit_ratio - end_snap.hit_ratio
        if steps >= min_steps and drop >= min_drop:
            results.append(
                DrainResult(
                    start_ts=start_snap.timestamp,
                    end_ts=end_snap.timestamp,
                    start_ratio=start_snap.hit_ratio,
                    end_ratio=end_snap.hit_ratio,
                    steps=steps,
                )
            )

    return results
