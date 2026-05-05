"""Plateau detection: identify time windows where hit ratio is stable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class PlateauResult:
    """A detected plateau window in the hit-ratio time series."""

    start_ts: float
    end_ts: float
    average_hit_ratio: float
    snapshot_count: int
    max_deviation: float

    def duration(self) -> float:
        """Return duration of the plateau in seconds."""
        return self.end_ts - self.start_ts

    def __str__(self) -> str:
        ratio_pct = self.average_hit_ratio * 100
        return (
            f"Plateau({ratio_pct:.2f}% avg, "
            f"deviation={self.max_deviation:.4f}, "
            f"duration={self.duration():.1f}s, "
            f"n={self.snapshot_count})"
        )


def detect_plateaus(
    tracker: StatsTracker,
    min_snapshots: int = 3,
    max_deviation: float = 0.02,
) -> List[PlateauResult]:
    """Detect plateau windows in the tracker's hit-ratio history.

    A plateau is a consecutive run of at least *min_snapshots* snapshots
    where every hit-ratio value stays within *max_deviation* of the window
    mean.

    Args:
        tracker: The StatsTracker whose history is analysed.
        min_snapshots: Minimum number of consecutive snapshots to form a plateau.
        max_deviation: Maximum allowed absolute deviation from the window mean.

    Returns:
        A list of PlateauResult objects ordered by start timestamp.
    """
    snapshots = tracker.history()
    if not snapshots:
        return []

    ratios = [s.hit_ratio for s in snapshots]
    timestamps = [s.timestamp for s in snapshots]
    n = len(ratios)
    plateaus: List[PlateauResult] = []

    start = 0
    while start < n:
        end = start + 1
        while end < n:
            window = ratios[start : end + 1]
            mean = sum(window) / len(window)
            deviation = max(abs(r - mean) for r in window)
            if deviation <= max_deviation:
                end += 1
            else:
                break

        length = end - start
        if length >= min_snapshots:
            window = ratios[start:end]
            mean = sum(window) / len(window)
            deviation = max(abs(r - mean) for r in window)
            plateaus.append(
                PlateauResult(
                    start_ts=timestamps[start],
                    end_ts=timestamps[end - 1],
                    average_hit_ratio=mean,
                    snapshot_count=length,
                    max_deviation=deviation,
                )
            )
            start = end
        else:
            start += 1

    return plateaus
