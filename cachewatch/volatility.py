"""Compute hit-ratio volatility (standard deviation over a window)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class VolatilityResult:
    """Result of a volatility computation."""

    window: int  # number of snapshots used
    std_dev: Optional[float]  # None when fewer than 2 data points
    mean: Optional[float]
    min_ratio: Optional[float]
    max_ratio: Optional[float]

    def __str__(self) -> str:  # pragma: no cover
        if self.std_dev is None:
            return "Volatility: n/a (insufficient data)"
        return (
            f"Volatility(window={self.window}, "
            f"std_dev={self.std_dev:.4f}, "
            f"mean={self.mean:.4f}, "
            f"min={self.min_ratio:.4f}, "
            f"max={self.max_ratio:.4f})"
        )


def _std_dev(values: List[float]) -> float:
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return variance ** 0.5


def compute_volatility(
    tracker: StatsTracker,
    last_n: Optional[int] = None,
) -> Optional[VolatilityResult]:
    """Compute volatility of hit ratios recorded in *tracker*.

    Args:
        tracker: The :class:`StatsTracker` to analyse.
        last_n: If given, only the most-recent *last_n* snapshots are used.

    Returns:
        A :class:`VolatilityResult`, or ``None`` when the tracker is empty.
    """
    snapshots = tracker.history()
    if not snapshots:
        return None

    if last_n is not None and last_n > 0:
        snapshots = snapshots[-last_n:]

    ratios: List[float] = [
        s.hit_ratio for s in snapshots if s.hit_ratio is not None
    ]

    if len(ratios) < 2:
        return VolatilityResult(
            window=len(snapshots),
            std_dev=None,
            mean=None,
            min_ratio=None,
            max_ratio=None,
        )

    return VolatilityResult(
        window=len(snapshots),
        std_dev=_std_dev(ratios),
        mean=sum(ratios) / len(ratios),
        min_ratio=min(ratios),
        max_ratio=max(ratios),
    )
