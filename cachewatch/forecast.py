"""Simple linear forecast for hit ratio based on recent trend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cachewatch.stats_tracker import StatsTracker
from cachewatch.trend import _linear_slope


@dataclass
class ForecastResult:
    """Projected hit ratio at a future point in time."""

    seconds_ahead: float
    current_ratio: float
    predicted_ratio: float
    slope: float

    def __str__(self) -> str:
        direction = "rising" if self.slope > 0 else "falling" if self.slope < 0 else "stable"
        return (
            f"Forecast +{self.seconds_ahead:.0f}s: "
            f"{self.predicted_ratio:.1%} (currently {self.current_ratio:.1%}, {direction})"
        )


def forecast_hit_ratio(
    tracker: StatsTracker,
    seconds_ahead: float = 60.0,
    window: int = 10,
) -> Optional[ForecastResult]:
    """Predict the hit ratio *seconds_ahead* seconds into the future.

    Uses the slope from the most recent *window* snapshots.  Returns
    ``None`` when there are fewer than two snapshots available.
    """
    snapshots = tracker.history()
    if len(snapshots) < 2:
        return None

    recent = snapshots[-window:] if len(snapshots) >= window else snapshots

    times = [s.timestamp for s in recent]
    ratios = [s.hit_ratio for s in recent]

    slope = _linear_slope(times, ratios)
    current_ratio = ratios[-1]
    predicted = current_ratio + slope * seconds_ahead
    predicted = max(0.0, min(1.0, predicted))

    return ForecastResult(
        seconds_ahead=seconds_ahead,
        current_ratio=current_ratio,
        predicted_ratio=predicted,
        slope=slope,
    )
