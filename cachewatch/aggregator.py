"""Aggregation utilities for grouping snapshots into time buckets."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone

from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


@dataclass
class BucketSummary:
    """Summary statistics for a time bucket."""
    bucket_start: datetime
    bucket_end: datetime
    avg_hit_ratio: float
    min_hit_ratio: float
    max_hit_ratio: float
    total_hits: int
    total_misses: int
    sample_count: int

    def __str__(self) -> str:
        ts = self.bucket_start.strftime("%H:%M:%S")
        return (
            f"[{ts}] avg={self.avg_hit_ratio:.2%} "
            f"min={self.min_hit_ratio:.2%} max={self.max_hit_ratio:.2%} "
            f"samples={self.sample_count}"
        )


def aggregate_by_seconds(
    tracker: StatsTracker,
    bucket_size: int = 60,
) -> List[BucketSummary]:
    """Group tracker snapshots into fixed-size second buckets.

    Args:
        tracker: StatsTracker containing snapshots.
        bucket_size: Width of each bucket in seconds.

    Returns:
        List of BucketSummary, one per non-empty bucket, ordered by time.
    """
    snapshots = tracker.history()
    if not snapshots:
        return []

    buckets: dict = {}
    for snap in snapshots:
        ts = snap.timestamp.timestamp()
        bucket_key = int(ts // bucket_size) * bucket_size
        buckets.setdefault(bucket_key, []).append(snap)

    summaries: List[BucketSummary] = []
    for bucket_key in sorted(buckets):
        snaps = buckets[bucket_key]
        ratios = [s.stats.hit_ratio for s in snaps]
        summaries.append(
            BucketSummary(
                bucket_start=datetime.fromtimestamp(bucket_key, tz=timezone.utc),
                bucket_end=datetime.fromtimestamp(
                    bucket_key + bucket_size, tz=timezone.utc
                ),
                avg_hit_ratio=sum(ratios) / len(ratios),
                min_hit_ratio=min(ratios),
                max_hit_ratio=max(ratios),
                total_hits=sum(s.stats.hits for s in snaps),
                total_misses=sum(s.stats.misses for s in snaps),
                sample_count=len(snaps),
            )
        )
    return summaries
