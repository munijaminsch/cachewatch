"""Compute divergence between two trackers over a shared time window."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class DivergenceResult:
    """Result of a divergence analysis between two trackers."""

    mean_a: Optional[float]
    mean_b: Optional[float]
    max_gap: Optional[float]
    mean_gap: Optional[float]
    sample_count: int

    def __str__(self) -> str:  # pragma: no cover
        if self.mean_a is None or self.mean_b is None:
            return "DivergenceResult(insufficient data)"
        sign = "+" if (self.mean_gap or 0) >= 0 else ""
        return (
            f"DivergenceResult(mean_a={self.mean_a:.3f}, mean_b={self.mean_b:.3f}, "
            f"mean_gap={sign}{self.mean_gap:.3f}, max_gap={self.max_gap:.3f}, "
            f"n={self.sample_count})"
        )


def compute_divergence(
    tracker_a: StatsTracker,
    tracker_b: StatsTracker,
) -> Optional[DivergenceResult]:
    """Compare two trackers point-by-point (by index) and return divergence metrics.

    Snapshots are paired by position after sorting each tracker by timestamp.
    Only the overlapping count of snapshots is used.
    Returns None when either tracker has fewer than two snapshots.
    """
    snaps_a = sorted(tracker_a.history(), key=lambda s: s.timestamp)
    snaps_b = sorted(tracker_b.history(), key=lambda s: s.timestamp)

    n = min(len(snaps_a), len(snaps_b))
    if n < 2:
        return None

    ratios_a = [s.hit_ratio for s in snaps_a[:n]]
    ratios_b = [s.hit_ratio for s in snaps_b[:n]]

    gaps = [b - a for a, b in zip(ratios_a, ratios_b)]

    mean_a = sum(ratios_a) / n
    mean_b = sum(ratios_b) / n
    mean_gap = sum(gaps) / n
    max_gap = max(gaps, key=abs)

    return DivergenceResult(
        mean_a=mean_a,
        mean_b=mean_b,
        max_gap=max_gap,
        mean_gap=mean_gap,
        sample_count=n,
    )
