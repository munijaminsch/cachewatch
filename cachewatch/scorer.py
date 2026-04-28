"""Cache health scoring module for cachewatch."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker
from cachewatch.snapshot_filter import average_hit_ratio, trough_hit_ratio
from cachewatch.trend import analyze_trend


@dataclass
class HealthScore:
    """Composite health score for a cache session."""

    score: float          # 0.0 – 100.0
    grade: str            # A / B / C / D / F
    avg_hit_ratio: float
    trough: float
    trend_slope: Optional[float]

    def __str__(self) -> str:
        slope_str = f"{self.trend_slope:+.4f}" if self.trend_slope is not None else "n/a"
        return (
            f"HealthScore(grade={self.grade}, score={self.score:.1f}, "
            f"avg={self.avg_hit_ratio:.3f}, trough={self.trough:.3f}, "
            f"slope={slope_str})"
        )


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"


def compute_health_score(
    tracker: StatsTracker,
    trend_weight: float = 0.2,
) -> Optional[HealthScore]:
    """Compute a 0-100 health score from tracker history.

    Weights:
      - 60 % average hit ratio
      - 20 % trough (worst point) hit ratio
      - 20 % trend direction (slope normalised to [-1, 1])
    """
    snapshots = tracker.history()
    if not snapshots:
        return None

    avg = average_hit_ratio(snapshots)
    trough = trough_hit_ratio(snapshots)

    trend = analyze_trend(tracker)
    slope = trend.slope if trend is not None else None

    # Normalise slope contribution: clamp to [-0.01, 0.01] then scale
    if slope is not None:
        clamped = max(-0.01, min(0.01, slope))
        trend_component = (clamped / 0.01) * 0.5 + 0.5  # 0..1
    else:
        trend_component = 0.5  # neutral when unknown

    raw = (
        0.60 * avg
        + 0.20 * trough
        + trend_weight * trend_component
    )
    score = round(min(100.0, max(0.0, raw * 100)), 2)

    return HealthScore(
        score=score,
        grade=_grade(score),
        avg_hit_ratio=avg,
        trough=trough,
        trend_slope=slope,
    )
