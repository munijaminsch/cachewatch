"""Sliding window statistics over a StatsTracker."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from cachewatch.stats_tracker import StatsTracker
from cachewatch.snapshot_filter import filter_last_n_seconds, average_hit_ratio


@dataclass
class WindowResult:
    """Statistics computed over a sliding time window."""
    window_seconds: int
    count: int
    avg_hit_ratio: Optional[float]
    min_hit_ratio: Optional[float]
    max_hit_ratio: Optional[float]
    range_hit_ratio: Optional[float]

    def __str__(self) -> str:  # pragma: no cover
        avg = f"{self.avg_hit_ratio:.4f}" if self.avg_hit_ratio is not None else "N/A"
        lo = f"{self.min_hit_ratio:.4f}" if self.min_hit_ratio is not None else "N/A"
        hi = f"{self.max_hit_ratio:.4f}" if self.max_hit_ratio is not None else "N/A"
        return (
            f"Window({self.window_seconds}s) "
            f"count={self.count} avg={avg} min={lo} max={hi}"
        )


def compute_window(
    tracker: StatsTracker,
    window_seconds: int,
    reference_ts: Optional[float] = None,
) -> Optional[WindowResult]:
    """Compute sliding window statistics for the last *window_seconds* seconds.

    Parameters
    ----------
    tracker:
        The source of snapshot data.
    window_seconds:
        How many seconds back from *reference_ts* (or the latest snapshot) to
        include.
    reference_ts:
        Epoch timestamp to use as "now".  Defaults to the timestamp of the
        most recent snapshot.

    Returns
    -------
    WindowResult or None if the tracker is empty.
    """
    snapshots = tracker.history()
    if not snapshots:
        return None

    if reference_ts is None:
        reference_ts = snapshots[-1].timestamp

    window: List = filter_last_n_seconds(tracker, window_seconds, reference_ts)

    ratios = [
        s.hit_ratio for s in window if s.hit_ratio is not None
    ]

    avg = (sum(ratios) / len(ratios)) if ratios else None
    lo = min(ratios) if ratios else None
    hi = max(ratios) if ratios else None
    rng = (hi - lo) if (hi is not None and lo is not None) else None

    return WindowResult(
        window_seconds=window_seconds,
        count=len(window),
        avg_hit_ratio=avg,
        min_hit_ratio=lo,
        max_hit_ratio=hi,
        range_hit_ratio=rng,
    )
