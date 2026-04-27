"""Compare two time-range snapshots and produce a diff summary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker
from cachewatch.snapshot_filter import filter_by_time_range, average_hit_ratio


@dataclass
class ComparisonResult:
    """Holds the comparison between two snapshot windows."""
    window_a_avg: Optional[float]
    window_b_avg: Optional[float]
    delta: Optional[float]
    improved: Optional[bool]

    def __str__(self) -> str:
        if self.window_a_avg is None or self.window_b_avg is None:
            return "ComparisonResult: insufficient data"
        direction = "improved" if self.improved else "degraded"
        return (
            f"ComparisonResult: A={self.window_a_avg:.2%} B={self.window_b_avg:.2%} "
            f"delta={self.delta:+.2%} ({direction})"
        )


def compare_windows(
    tracker: StatsTracker,
    start_a: float,
    end_a: float,
    start_b: float,
    end_b: float,
) -> ComparisonResult:
    """Compare average hit ratios between two time windows.

    Args:
        tracker: StatsTracker instance with recorded snapshots.
        start_a: Unix timestamp — start of window A.
        end_a:   Unix timestamp — end of window A.
        start_b: Unix timestamp — start of window B.
        end_b:   Unix timestamp — end of window B.

    Returns:
        ComparisonResult with averages and delta.
    """
    snaps_a = filter_by_time_range(tracker, start_a, end_a)
    snaps_b = filter_by_time_range(tracker, start_b, end_b)

    avg_a = average_hit_ratio(snaps_a) if snaps_a else None
    avg_b = average_hit_ratio(snaps_b) if snaps_b else None

    if avg_a is None or avg_b is None:
        return ComparisonResult(
            window_a_avg=avg_a,
            window_b_avg=avg_b,
            delta=None,
            improved=None,
        )

    delta = avg_b - avg_a
    return ComparisonResult(
        window_a_avg=avg_a,
        window_b_avg=avg_b,
        delta=delta,
        improved=delta >= 0,
    )
