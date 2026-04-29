"""Heatmap generation for cache hit ratios over time buckets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cachewatch.aggregator import BucketSummary, aggregate_by_seconds
from cachewatch.stats_tracker import StatsTracker


@dataclass
class HeatmapRow:
    """A single row in the heatmap, representing one time bucket."""

    timestamp: float
    hit_ratio: Optional[float]
    label: str

    def __str__(self) -> str:
        ratio_str = f"{self.hit_ratio:.2%}" if self.hit_ratio is not None else "N/A"
        return f"HeatmapRow(ts={self.timestamp:.0f}, ratio={ratio_str}, label={self.label!r})"


SHADES = [" ", "░", "▒", "▓", "█"]


def _ratio_to_shade(ratio: Optional[float]) -> str:
    """Map a hit ratio [0, 1] to a block shade character."""
    if ratio is None:
        return "?"
    idx = min(int(ratio * len(SHADES)), len(SHADES) - 1)
    return SHADES[idx]


def build_heatmap(tracker: StatsTracker, bucket_seconds: int = 60) -> List[HeatmapRow]:
    """Build a list of HeatmapRows from a StatsTracker.

    Args:
        tracker: The stats tracker containing snapshots.
        bucket_seconds: Width of each time bucket in seconds.

    Returns:
        Ordered list of HeatmapRow instances.
    """
    buckets: List[BucketSummary] = aggregate_by_seconds(tracker, bucket_seconds)
    rows: List[HeatmapRow] = []
    for bucket in buckets:
        shade = _ratio_to_shade(bucket.average_hit_ratio)
        rows.append(
            HeatmapRow(
                timestamp=bucket.bucket_start,
                hit_ratio=bucket.average_hit_ratio,
                label=shade,
            )
        )
    return rows
