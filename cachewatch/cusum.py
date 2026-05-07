"""CUSUM (Cumulative Sum) change-point detection for hit ratio streams."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class CusumResult:
    """Result of a CUSUM change-point detection pass."""

    change_point_ts: Optional[float]
    """Timestamp of the detected change point, or None."""
    cusum_high: List[float]
    """Upper CUSUM statistic series."""
    cusum_low: List[float]
    """Lower CUSUM statistic series."""
    threshold: float
    """Decision threshold used."""
    drift: float
    """Allowable drift parameter used."""

    def __str__(self) -> str:  # pragma: no cover
        if self.change_point_ts is None:
            return (
                f"CusumResult(no change detected, "
                f"threshold={self.threshold:.4f}, drift={self.drift:.4f})"
            )
        return (
            f"CusumResult(change_point_ts={self.change_point_ts:.2f}, "
            f"threshold={self.threshold:.4f}, drift={self.drift:.4f})"
        )


def detect_cusum(
    tracker: StatsTracker,
    threshold: float = 0.10,
    drift: float = 0.005,
) -> Optional[CusumResult]:
    """Run CUSUM change-point detection over *tracker*'s hit-ratio history.

    Parameters
    ----------
    tracker:
        Source of snapshot history.
    threshold:
        Alert threshold *h*.  When a CUSUM statistic exceeds this value a
        change point is declared.
    drift:
        Allowable slack *k* added/subtracted before accumulation.  Smaller
        values make the detector more sensitive.

    Returns
    -------
    CusumResult or None
        None when fewer than two snapshots are available.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return None

    ratios = [s.hit_ratio for s in snapshots]
    mean = sum(ratios) / len(ratios)

    cusum_high: List[float] = []
    cusum_low: List[float] = []
    change_point_ts: Optional[float] = None

    s_high = 0.0
    s_low = 0.0

    for idx, ratio in enumerate(ratios):
        s_high = max(0.0, s_high + (ratio - mean) - drift)
        s_low = max(0.0, s_low - (ratio - mean) - drift)
        cusum_high.append(s_high)
        cusum_low.append(s_low)

        if change_point_ts is None and (s_high > threshold or s_low > threshold):
            change_point_ts = snapshots[idx].timestamp

    return CusumResult(
        change_point_ts=change_point_ts,
        cusum_high=cusum_high,
        cusum_low=cusum_low,
        threshold=threshold,
        drift=drift,
    )
