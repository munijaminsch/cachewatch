"""Compute hit-ratio percentiles across tracker snapshots."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class PercentileResult:
    p50: Optional[float]
    p90: Optional[float]
    p95: Optional[float]
    p99: Optional[float]
    sample_count: int

    def __str__(self) -> str:
        def _fmt(v: Optional[float]) -> str:
            return f"{v:.1%}" if v is not None else "n/a"

        return (
            f"PercentileResult(n={self.sample_count} "
            f"p50={_fmt(self.p50)} p90={_fmt(self.p90)} "
            f"p95={_fmt(self.p95)} p99={_fmt(self.p99)})"
        )


def _percentile(sorted_values: List[float], p: float) -> Optional[float]:
    """Return the p-th percentile (0-100) using linear interpolation."""
    n = len(sorted_values)
    if n == 0:
        return None
    if n == 1:
        return sorted_values[0]
    rank = (p / 100.0) * (n - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return sorted_values[lower]
    frac = rank - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def compute_percentiles(tracker: StatsTracker) -> Optional[PercentileResult]:
    """Compute p50/p90/p95/p99 hit ratios from all snapshots in *tracker*.

    Returns ``None`` when the tracker contains no snapshots.
    """
    snapshots = tracker.history()
    if not snapshots:
        return None

    ratios = sorted(
        s.hit_ratio for s in snapshots if s.hit_ratio is not None
    )

    if not ratios:
        return PercentileResult(
            p50=None, p90=None, p95=None, p99=None, sample_count=len(snapshots)
        )

    return PercentileResult(
        p50=_percentile(ratios, 50),
        p90=_percentile(ratios, 90),
        p95=_percentile(ratios, 95),
        p99=_percentile(ratios, 99),
        sample_count=len(snapshots),
    )
