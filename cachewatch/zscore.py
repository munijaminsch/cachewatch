"""Z-score based normalization and anomaly scoring for hit ratio snapshots."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class ZScorePoint:
    timestamp: float
    hit_ratio: Optional[float]
    zscore: Optional[float]

    def __str__(self) -> str:
        ts = f"{self.timestamp:.0f}"
        ratio = f"{self.hit_ratio:.4f}" if self.hit_ratio is not None else "N/A"
        z = f"{self.zscore:+.4f}" if self.zscore is not None else "N/A"
        return f"ZScorePoint(ts={ts}, ratio={ratio}, z={z})"


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std_dev(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def compute_zscores(tracker: StatsTracker) -> List[ZScorePoint]:
    """Compute z-scores for each snapshot's hit ratio.

    Returns a list of ZScorePoint objects.  Points with a None hit_ratio
    receive a None z-score.  When the standard deviation is zero every
    valid point receives a z-score of 0.0.
    """
    snapshots = tracker.history()
    if not snapshots:
        return []

    ratios: List[Optional[float]] = [s.hit_ratio() for s in snapshots]
    valid: List[float] = [r for r in ratios if r is not None]

    if len(valid) < 2:
        return [
            ZScorePoint(
                timestamp=s.timestamp,
                hit_ratio=r,
                zscore=0.0 if r is not None else None,
            )
            for s, r in zip(snapshots, ratios)
        ]

    mu = _mean(valid)
    sigma = _std_dev(valid, mu)

    results: List[ZScorePoint] = []
    for snap, ratio in zip(snapshots, ratios):
        if ratio is None:
            z = None
        elif sigma == 0.0:
            z = 0.0
        else:
            z = (ratio - mu) / sigma
        results.append(ZScorePoint(timestamp=snap.timestamp, hit_ratio=ratio, zscore=z))

    return results
