"""Outlier detection for cache hit ratio snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class OutlierResult:
    timestamp: float
    hit_ratio: float
    mean: float
    std_dev: float
    z_score: float

    def __str__(self) -> str:
        direction = "high" if self.hit_ratio > self.mean else "low"
        return (
            f"Outlier at ts={self.timestamp:.1f}: "
            f"ratio={self.hit_ratio:.3f} ({direction}), "
            f"z={self.z_score:.2f}"
        )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std_dev(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def detect_outliers(
    tracker: StatsTracker,
    z_threshold: float = 2.0,
) -> List[OutlierResult]:
    """Return snapshots whose hit ratio deviates beyond *z_threshold* std devs."""
    snapshots = tracker.history()
    if len(snapshots) < 3:
        return []

    ratios = [s.hit_ratio for s in snapshots]
    mu = _mean(ratios)
    sigma = _std_dev(ratios, mu)

    if sigma == 0.0:
        return []

    results: List[OutlierResult] = []
    for snap in snapshots:
        z = (snap.hit_ratio - mu) / sigma
        if abs(z) >= z_threshold:
            results.append(
                OutlierResult(
                    timestamp=snap.timestamp,
                    hit_ratio=snap.hit_ratio,
                    mean=mu,
                    std_dev=sigma,
                    z_score=z,
                )
            )
    return results
