"""Utilities for filtering and querying snapshot history."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


def filter_by_time_range(
    tracker: StatsTracker,
    start: datetime,
    end: Optional[datetime] = None,
) -> List[CacheStats]:
    """Return snapshots whose timestamp falls within [start, end].

    Args:
        tracker: The StatsTracker instance holding history.
        start: Inclusive lower bound.
        end: Inclusive upper bound; defaults to now.

    Returns:
        A list of CacheStats snapshots within the range.
    """
    if end is None:
        end = datetime.utcnow()
    return [
        snap
        for snap in tracker.history()
        if start <= snap.timestamp <= end
    ]


def filter_last_n_seconds(tracker: StatsTracker, seconds: float) -> List[CacheStats]:
    """Return snapshots recorded within the last *seconds* seconds."""
    cutoff = datetime.utcnow() - timedelta(seconds=seconds)
    return filter_by_time_range(tracker, start=cutoff)


def average_hit_ratio(snapshots: List[CacheStats]) -> Optional[float]:
    """Compute the mean hit ratio across a list of snapshots.

    Returns None when the list is empty.
    """
    if not snapshots:
        return None
    return sum(s.hit_ratio for s in snapshots) / len(snapshots)


def peak_hit_ratio(snapshots: List[CacheStats]) -> Optional[float]:
    """Return the highest hit ratio observed in *snapshots*."""
    if not snapshots:
        return None
    return max(s.hit_ratio for s in snapshots)


def trough_hit_ratio(snapshots: List[CacheStats]) -> Optional[float]:
    """Return the lowest hit ratio observed in *snapshots*."""
    if not snapshots:
        return None
    return min(s.hit_ratio for s in snapshots)
