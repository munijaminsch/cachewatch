"""Pulse detection: identify periodic high-activity intervals in cache traffic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class PulseResult:
    """Represents a detected pulse (burst of high request volume)."""

    timestamp: float
    total_requests: int
    hit_ratio: Optional[float]
    z_score: float

    def __str__(self) -> str:  # pragma: no cover
        ratio_str = f"{self.hit_ratio:.4f}" if self.hit_ratio is not None else "N/A"
        return (
            f"PulseResult(ts={self.timestamp:.1f}, "
            f"requests={self.total_requests}, "
            f"hit_ratio={ratio_str}, "
            f"z_score={self.z_score:.3f})"
        )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std_dev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def detect_pulses(
    tracker: StatsTracker,
    threshold_z: float = 2.0,
) -> List[PulseResult]:
    """Detect snapshots where request volume is significantly above average.

    Args:
        tracker: The StatsTracker holding snapshots.
        threshold_z: Z-score threshold above which a snapshot is a pulse.

    Returns:
        List of PulseResult for each snapshot exceeding the threshold.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return []

    totals = [float(s.total) for s in snapshots]
    mean = _mean(totals)
    std = _std_dev(totals, mean)

    if std == 0.0:
        return []

    results: List[PulseResult] = []
    for snap in snapshots:
        z = (snap.total - mean) / std
        if z >= threshold_z:
            results.append(
                PulseResult(
                    timestamp=snap.timestamp,
                    total_requests=snap.total,
                    hit_ratio=snap.hit_ratio,
                    z_score=z,
                )
            )
    return results
