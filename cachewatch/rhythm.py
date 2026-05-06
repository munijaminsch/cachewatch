"""Detect periodic rhythms (cycles) in hit ratio time series."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class RhythmResult:
    """Result of a rhythm/periodicity analysis."""

    period_seconds: float
    strength: float          # 0.0 – 1.0, higher = more regular
    sample_count: int
    mean_ratio: Optional[float]

    def __str__(self) -> str:
        strength_pct = f"{self.strength * 100:.1f}%"
        mean = f"{self.mean_ratio:.4f}" if self.mean_ratio is not None else "N/A"
        return (
            f"RhythmResult(period={self.period_seconds:.1f}s, "
            f"strength={strength_pct}, mean={mean}, n={self.sample_count})"
        )


def _autocorrelate(values: List[float], lag: int) -> float:
    """Return the normalised autocorrelation coefficient at *lag*."""
    n = len(values)
    if n <= lag:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values)
    if variance == 0.0:
        return 0.0
    cov = sum((values[i] - mean) * (values[i - lag] - mean) for i in range(lag, n))
    return cov / variance


def detect_rhythm(
    tracker: StatsTracker,
    min_period: int = 2,
    max_period: Optional[int] = None,
) -> Optional[RhythmResult]:
    """Detect the dominant periodic rhythm in *tracker*'s hit ratios.

    Returns ``None`` when there are fewer than four snapshots or no
    meaningful periodicity is found.
    """
    snapshots = tracker.history()
    if len(snapshots) < 4:
        return None

    ratios = [s.stats.hit_ratio for s in snapshots]
    n = len(ratios)
    upper = max_period if max_period is not None else n // 2
    upper = max(upper, min_period)

    best_lag = min_period
    best_corr = -math.inf
    for lag in range(min_period, upper + 1):
        corr = _autocorrelate(ratios, lag)
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    # Estimate period in seconds using timestamp span
    ts_values = [s.timestamp for s in snapshots]
    span = ts_values[-1] - ts_values[0]
    avg_interval = span / (n - 1) if n > 1 else 1.0
    period_seconds = best_lag * avg_interval

    strength = max(0.0, min(1.0, best_corr))
    mean_ratio = sum(ratios) / len(ratios)

    return RhythmResult(
        period_seconds=period_seconds,
        strength=strength,
        sample_count=n,
        mean_ratio=mean_ratio,
    )
