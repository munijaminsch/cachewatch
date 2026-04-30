"""Baseline comparison: compare current stats against a stored baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker
from cachewatch.snapshot_filter import average_hit_ratio


@dataclass
class BaselineResult:
    baseline_ratio: Optional[float]
    current_ratio: Optional[float]
    delta: Optional[float]
    verdict: str  # "above", "below", "on_par", "unknown"

    def __str__(self) -> str:
        if self.baseline_ratio is None or self.current_ratio is None:
            return "BaselineResult(unknown)"
        sign = "+" if (self.delta or 0) >= 0 else ""
        return (
            f"BaselineResult(baseline={self.baseline_ratio:.3f}, "
            f"current={self.current_ratio:.3f}, "
            f"delta={sign}{self.delta:.3f}, verdict={self.verdict})"
        )


def compare_to_baseline(
    tracker: StatsTracker,
    baseline_tracker: StatsTracker,
    tolerance: float = 0.02,
) -> BaselineResult:
    """Compare the average hit ratio of *tracker* against *baseline_tracker*.

    Args:
        tracker: The current (live) tracker to evaluate.
        baseline_tracker: A tracker whose snapshots represent the baseline.
        tolerance: Ratios within this band are considered "on_par".

    Returns:
        A :class:`BaselineResult` describing the comparison.
    """
    baseline_snapshots = baseline_tracker.history()
    current_snapshots = tracker.history()

    baseline_ratio = average_hit_ratio(baseline_snapshots) if baseline_snapshots else None
    current_ratio = average_hit_ratio(current_snapshots) if current_snapshots else None

    if baseline_ratio is None or current_ratio is None:
        return BaselineResult(
            baseline_ratio=baseline_ratio,
            current_ratio=current_ratio,
            delta=None,
            verdict="unknown",
        )

    delta = current_ratio - baseline_ratio

    if abs(delta) <= tolerance:
        verdict = "on_par"
    elif delta > 0:
        verdict = "above"
    else:
        verdict = "below"

    return BaselineResult(
        baseline_ratio=baseline_ratio,
        current_ratio=current_ratio,
        delta=delta,
        verdict=verdict,
    )
