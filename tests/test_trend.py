"""Tests for cachewatch.trend."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.trend import TrendResult, analyze_trend


def _snap(timestamp: float, hit_ratio: float):
    snap = MagicMock()
    snap.timestamp = timestamp
    snap.hit_ratio = hit_ratio
    return snap


def _tracker(*snapshots):
    tracker = MagicMock(spec=StatsTracker)
    tracker.history.return_value = list(snapshots)
    return tracker


class TestAnalyzeTrend:
    def test_returns_none_when_empty(self):
        assert analyze_trend(_tracker()) is None

    def test_returns_none_with_single_snapshot(self):
        assert analyze_trend(_tracker(_snap(0.0, 0.5))) is None

    def test_improving_direction(self):
        t = _tracker(_snap(0.0, 0.50), _snap(1.0, 0.60), _snap(2.0, 0.70))
        result = analyze_trend(t)
        assert result is not None
        assert result.direction == "improving"
        assert result.slope > 0

    def test_degrading_direction(self):
        t = _tracker(_snap(0.0, 0.80), _snap(1.0, 0.65), _snap(2.0, 0.50))
        result = analyze_trend(t)
        assert result is not None
        assert result.direction == "degrading"
        assert result.slope < 0

    def test_stable_direction(self):
        t = _tracker(_snap(0.0, 0.70), _snap(1.0, 0.70), _snap(2.0, 0.70))
        result = analyze_trend(t)
        assert result is not None
        assert result.direction == "stable"
        assert result.slope == pytest.approx(0.0)

    def test_sample_count(self):
        snaps = [_snap(float(i), 0.5) for i in range(5)]
        result = analyze_trend(_tracker(*snaps))
        assert result.sample_count == 5

    def test_start_and_end_ratio(self):
        t = _tracker(_snap(0.0, 0.40), _snap(1.0, 0.55), _snap(2.0, 0.70))
        result = analyze_trend(t)
        assert result.start_ratio == pytest.approx(0.40)
        assert result.end_ratio == pytest.approx(0.70)

    def test_custom_stable_threshold(self):
        # slope ~0.05/s — stable with a high threshold
        t = _tracker(_snap(0.0, 0.50), _snap(1.0, 0.55))
        result = analyze_trend(t, stable_threshold=0.1)
        assert result.direction == "stable"


class TestTrendResult:
    def test_str_improving(self):
        r = TrendResult("improving", 0.05, 0.50, 0.70, 4)
        s = str(r)
        assert "IMPROVING" in s
        assert "↑" in s

    def test_str_degrading(self):
        r = TrendResult("degrading", -0.03, 0.80, 0.60, 3)
        s = str(r)
        assert "DEGRADING" in s
        assert "↓" in s

    def test_str_stable(self):
        r = TrendResult("stable", 0.0, 0.65, 0.65, 2)
        s = str(r)
        assert "STABLE" in s
        assert "→" in s
