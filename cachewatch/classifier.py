"""Classify cache performance snapshots into labeled performance tiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


# Performance tier labels
TIER_EXCELLENT = "excellent"
TIER_GOOD = "good"
TIER_FAIR = "fair"
TIER_POOR = "poor"
TIER_CRITICAL = "critical"


@dataclass
class ClassificationResult:
    tier: str
    hit_ratio: float
    snapshot_count: int
    description: str

    def __str__(self) -> str:
        return (
            f"Tier: {self.tier.upper()} | "
            f"Avg Hit Ratio: {self.hit_ratio:.1%} | "
            f"Snapshots: {self.snapshot_count} | "
            f"{self.description}"
        )


def _tier_for_ratio(ratio: float) -> tuple[str, str]:
    """Return (tier, description) for a given hit ratio."""
    if ratio >= 0.90:
        return TIER_EXCELLENT, "Cache is performing exceptionally well."
    elif ratio >= 0.75:
        return TIER_GOOD, "Cache performance is healthy."
    elif ratio >= 0.55:
        return TIER_FAIR, "Cache performance is acceptable but could improve."
    elif ratio >= 0.35:
        return TIER_POOR, "Cache performance is degraded; investigation recommended."
    else:
        return TIER_CRITICAL, "Cache performance is critically low; immediate action required."


def classify_tracker(tracker: StatsTracker) -> Optional[ClassificationResult]:
    """Classify overall cache performance based on average hit ratio across all snapshots."""
    snapshots = tracker.history()
    if not snapshots:
        return None

    ratios: List[float] = [
        s.hit_ratio for s in snapshots if s.hit_ratio is not None
    ]
    if not ratios:
        return None

    avg_ratio = sum(ratios) / len(ratios)
    tier, description = _tier_for_ratio(avg_ratio)

    return ClassificationResult(
        tier=tier,
        hit_ratio=avg_ratio,
        snapshot_count=len(snapshots),
        description=description,
    )
