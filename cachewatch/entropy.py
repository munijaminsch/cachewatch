"""Compute hit-ratio entropy across a tracker's history.

Entropy here is the Shannon entropy of a discretised hit-ratio
distribution.  High entropy means the ratios are spread evenly across
buckets; low entropy means they cluster tightly in one region.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, List

from cachewatch.stats_tracker import StatsTracker

# Number of equal-width buckets spanning [0, 1]
_BUCKETS = 10


@dataclass
class EntropyResult:
    """Result returned by :func:`compute_entropy`."""

    entropy: float
    max_entropy: float
    normalized: float          # entropy / max_entropy  (0 = uniform, 1 = max spread)
    bucket_counts: List[int]   # raw counts per bucket
    sample_size: int

    def __str__(self) -> str:
        pct = f"{self.normalized * 100:.1f}%"
        return (
            f"EntropyResult(entropy={self.entropy:.4f}, "
            f"max={self.max_entropy:.4f}, "
            f"normalized={pct}, "
            f"n={self.sample_size})"
        )


def _shannon(counts: List[int]) -> float:
    """Return Shannon entropy (nats) for a list of bucket counts."""
    total = sum(counts)
    if total == 0:
        return 0.0
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log(p)
    return entropy


def compute_entropy(
    tracker: StatsTracker,
    buckets: int = _BUCKETS,
) -> Optional[EntropyResult]:
    """Compute hit-ratio entropy for all snapshots in *tracker*.

    Returns ``None`` when the tracker has no snapshots.
    """
    snapshots = tracker.history()
    if not snapshots:
        return None

    counts: List[int] = [0] * buckets
    for snap in snapshots:
        ratio = snap.hit_ratio
        # Clamp to [0, 1] and map to bucket index
        idx = min(int(ratio * buckets), buckets - 1)
        counts[idx] += 1

    entropy = _shannon(counts)
    max_entropy = math.log(buckets) if buckets > 1 else 0.0
    normalized = (entropy / max_entropy) if max_entropy > 0 else 0.0

    return EntropyResult(
        entropy=entropy,
        max_entropy=max_entropy,
        normalized=normalized,
        bucket_counts=counts,
        sample_size=len(snapshots),
    )
