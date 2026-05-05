"""Decay analysis: measures how quickly hit ratio degrades over time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from cachewatch.stats_tracker import StatsTracker


@dataclass
class DecayResult:
    """Result of a decay analysis over a window of snapshots."""

    initial_ratio: float
    final_ratio: float
    decay_rate: float          # ratio points lost per second (negative = degrading)
    half_life_seconds: Optional[float]  # seconds to lose half of initial ratio
    snapshot_count: int

    def __str__(self) -> str:
        hl = (
            f"{self.half_life_seconds:.1f}s"
            if self.half_life_seconds is not None
            else "N/A"
        )
        sign = "+" if self.decay_rate >= 0 else ""
        return (
            f"DecayResult(initial={self.initial_ratio:.4f}, "
            f"final={self.final_ratio:.4f}, "
            f"rate={sign}{self.decay_rate:.6f}/s, "
            f"half_life={hl})"
        )


def _half_life(initial: float, decay_rate: float) -> Optional[float]:
    """Return seconds to reach half of *initial* given a linear decay_rate.

    Returns None when decay_rate is non-negative (no decay occurring).
    """
    if decay_rate >= 0 or initial <= 0:
        return None
    # linear model: ratio(t) = initial + decay_rate * t
    # solve for ratio(t) = initial / 2  =>  t = -initial / (2 * decay_rate)
    return -initial / (2.0 * decay_rate)


def compute_decay(tracker: StatsTracker) -> Optional[DecayResult]:
    """Compute decay statistics from *tracker* history.

    Returns None when fewer than two snapshots are available.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return None

    ratios: List[float] = [s.hit_ratio for s in snapshots]
    timestamps: List[float] = [s.timestamp for s in snapshots]

    initial_ratio = ratios[0]
    final_ratio = ratios[-1]
    elapsed = timestamps[-1] - timestamps[0]

    if elapsed == 0:
        decay_rate = 0.0
    else:
        decay_rate = (final_ratio - initial_ratio) / elapsed

    half_life = _half_life(initial_ratio, decay_rate)

    return DecayResult(
        initial_ratio=initial_ratio,
        final_ratio=final_ratio,
        decay_rate=decay_rate,
        half_life_seconds=half_life,
        snapshot_count=len(snapshots),
    )
