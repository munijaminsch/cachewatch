"""Compute skewness of hit-ratio distribution across snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class SkewnessResult:
    """Result of a skewness computation over a tracker's hit-ratio history."""

    skewness: Optional[float]
    sample_count: int
    mean: Optional[float]
    std_dev: Optional[float]

    def __str__(self) -> str:
        if self.skewness is None:
            return f"SkewnessResult(n={self.sample_count}, skewness=N/A)"
        direction = "right" if self.skewness > 0 else ("left" if self.skewness < 0 else "symmetric")
        return (
            f"SkewnessResult(n={self.sample_count}, "
            f"skewness={self.skewness:.4f}, "
            f"direction={direction})"
        )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std_dev(values: list[float], mu: float) -> float:
    variance = sum((v - mu) ** 2 for v in values) / len(values)
    return variance ** 0.5


def compute_skewness(tracker: StatsTracker) -> Optional[SkewnessResult]:
    """Compute the Pearson moment skewness of hit ratios in *tracker*.

    Returns ``None`` when the tracker is empty.  When fewer than three
    snapshots are available the skewness value itself will be ``None``
    (insufficient data), but a :class:`SkewnessResult` is still returned
    so callers can inspect ``sample_count``.
    """
    snapshots = tracker.history()
    n = len(snapshots)

    if n == 0:
        return None

    ratios = [s.hit_ratio for s in snapshots]

    if n < 3:
        mu = _mean(ratios) if n > 0 else None
        return SkewnessResult(
            skewness=None,
            sample_count=n,
            mean=mu,
            std_dev=None,
        )

    mu = _mean(ratios)
    sigma = _std_dev(ratios, mu)

    if sigma == 0.0:
        return SkewnessResult(
            skewness=0.0,
            sample_count=n,
            mean=mu,
            std_dev=0.0,
        )

    skew = (sum((v - mu) ** 3 for v in ratios) / n) / (sigma ** 3)

    return SkewnessResult(
        skewness=skew,
        sample_count=n,
        mean=mu,
        std_dev=sigma,
    )
