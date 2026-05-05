"""Detect consecutive hit-ratio improvement or decline streaks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class StreakResult:
    """Result of a streak analysis."""

    kind: str          # 'improving' | 'declining' | 'neutral'
    length: int        # number of consecutive snapshots in the streak
    start_ratio: Optional[float]
    end_ratio: Optional[float]

    def __str__(self) -> str:  # pragma: no cover
        if self.start_ratio is None or self.end_ratio is None:
            return f"Streak({self.kind}, length={self.length})"
        delta = self.end_ratio - self.start_ratio
        sign = "+" if delta >= 0 else ""
        return (
            f"Streak({self.kind}, length={self.length}, "
            f"delta={sign}{delta:.4f})"
        )


def detect_streak(tracker: StatsTracker) -> Optional[StreakResult]:
    """Return the current trailing streak from the most recent snapshots.

    A streak is a run of consecutive snapshots where each hit_ratio is
    strictly greater than (improving) or strictly less than (declining)
    the previous one.  A single snapshot or an empty tracker returns None.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return None

    ratios = [s.hit_ratio for s in snapshots]

    # Walk backwards from the last element to find the trailing streak.
    direction: Optional[str] = None
    streak_end = len(ratios) - 1
    streak_start = streak_end

    for i in range(len(ratios) - 1, 0, -1):
        prev, curr = ratios[i - 1], ratios[i]
        if curr > prev:
            step_dir = "improving"
        elif curr < prev:
            step_dir = "declining"
        else:
            break

        if direction is None:
            direction = step_dir

        if step_dir == direction:
            streak_start = i - 1
        else:
            break

    if direction is None:
        return StreakResult(
            kind="neutral",
            length=1,
            start_ratio=ratios[-1],
            end_ratio=ratios[-1],
        )

    return StreakResult(
        kind=direction,
        length=streak_end - streak_start + 1,
        start_ratio=ratios[streak_start],
        end_ratio=ratios[streak_end],
    )
