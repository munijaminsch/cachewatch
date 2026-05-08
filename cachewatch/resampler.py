"""Resample snapshot history to a fixed time interval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


@dataclass
class ResampledPoint:
    """A single resampled data point representing one interval bucket."""

    bucket_ts: float
    interval_seconds: int
    count: int
    average_hit_ratio: Optional[float]

    def __str__(self) -> str:
        ratio = f"{self.average_hit_ratio:.4f}" if self.average_hit_ratio is not None else "N/A"
        return (
            f"ResampledPoint(ts={self.bucket_ts:.0f}, "
            f"interval={self.interval_seconds}s, "
            f"count={self.count}, avg_ratio={ratio})"
        )


def resample_tracker(
    tracker: StatsTracker,
    interval_seconds: int = 60,
) -> List[ResampledPoint]:
    """Resample tracker snapshots into fixed-width time buckets.

    Snapshots are grouped by flooring their timestamp to the nearest
    ``interval_seconds`` boundary.  Each bucket reports the count of
    snapshots it contains and the average hit ratio across those snapshots.

    Args:
        tracker: Source of snapshot history.
        interval_seconds: Width of each bucket in seconds (must be >= 1).

    Returns:
        List of :class:`ResampledPoint` sorted by ascending bucket timestamp.
        Returns an empty list when the tracker has no history.
    """
    if interval_seconds < 1:
        raise ValueError("interval_seconds must be >= 1")

    snapshots = tracker.history()
    if not snapshots:
        return []

    buckets: dict[float, list[float]] = {}
    for snap in snapshots:
        bucket = float(int(snap.timestamp // interval_seconds) * interval_seconds)
        ratio = snap.stats.hit_ratio
        buckets.setdefault(bucket, []).append(ratio)

    result: List[ResampledPoint] = []
    for bucket_ts in sorted(buckets):
        ratios = buckets[bucket_ts]
        valid = [r for r in ratios if r is not None]
        avg = sum(valid) / len(valid) if valid else None
        result.append(
            ResampledPoint(
                bucket_ts=bucket_ts,
                interval_seconds=interval_seconds,
                count=len(ratios),
                average_hit_ratio=avg,
            )
        )
    return result
