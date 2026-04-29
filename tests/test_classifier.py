"""Tests for cachewatch.classifier module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cachewatch.classifier import (
    ClassificationResult,
    TIER_CRITICAL,
    TIER_EXCELLENT,
    TIER_FAIR,
    TIER_GOOD,
    TIER_POOR,
    classify_tracker,
)
from cachewatch.stats_tracker import StatsTracker


def _snap(hit_ratio: float):
    snap = MagicMock()
    snap.hit_ratio = hit_ratio
    return snap


def _tracker(ratios):
    tracker = MagicMock(spec=StatsTracker)
    tracker.history.return_value = [_snap(r) for r in ratios]
    return tracker


class TestClassifyTracker:
    def test_returns_none_when_empty(self):
        t = _tracker([])
        assert classify_tracker(t) is None

    def test_returns_classification_result(self):
        t = _tracker([0.95, 0.92])
        result = classify_tracker(t)
        assert isinstance(result, ClassificationResult)

    def test_excellent_tier(self):
        t = _tracker([0.95, 0.91, 0.93])
        result = classify_tracker(t)
        assert result.tier == TIER_EXCELLENT

    def test_good_tier(self):
        t = _tracker([0.80, 0.78])
        result = classify_tracker(t)
        assert result.tier == TIER_GOOD

    def test_fair_tier(self):
        t = _tracker([0.60, 0.58])
        result = classify_tracker(t)
        assert result.tier == TIER_FAIR

    def test_poor_tier(self):
        t = _tracker([0.40, 0.38])
        result = classify_tracker(t)
        assert result.tier == TIER_POOR

    def test_critical_tier(self):
        t = _tracker([0.10, 0.20])
        result = classify_tracker(t)
        assert result.tier == TIER_CRITICAL

    def test_snapshot_count_matches(self):
        t = _tracker([0.85, 0.80, 0.82])
        result = classify_tracker(t)
        assert result.snapshot_count == 3

    def test_hit_ratio_is_average(self):
        t = _tracker([0.80, 0.90])
        result = classify_tracker(t)
        assert abs(result.hit_ratio - 0.85) < 1e-9

    def test_str_contains_tier(self):
        t = _tracker([0.95])
        result = classify_tracker(t)
        assert TIER_EXCELLENT.upper() in str(result)

    def test_str_contains_description(self):
        t = _tracker([0.10])
        result = classify_tracker(t)
        assert "immediate action" in str(result).lower()
