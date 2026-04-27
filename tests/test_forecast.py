"""Tests for cachewatch.forecast."""

from __future__ import annotations

import time

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.forecast import ForecastResult, forecast_hit_ratio


def _snap(timestamp: float, hits: int, misses: int) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=timestamp)


def _tracker(*snapshots: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


class TestForecastHitRatio:
    def test_returns_none_when_empty(self):
        t = _tracker()
        assert forecast_hit_ratio(t) is None

    def test_returns_none_with_single_snapshot(self):
        t = _tracker(_snap(0.0, 10, 5))
        assert forecast_hit_ratio(t) is None

    def test_returns_forecast_result(self):
        t = _tracker(
            _snap(0.0, 50, 50),
            _snap(10.0, 60, 40),
        )
        result = forecast_hit_ratio(t, seconds_ahead=10.0)
        assert isinstance(result, ForecastResult)

    def test_predicted_ratio_clamped_to_zero_minimum(self):
        # Steeply falling ratio — should not go below 0
        t = _tracker(
            _snap(0.0, 100, 0),
            _snap(1.0, 0, 100),
        )
        result = forecast_hit_ratio(t, seconds_ahead=1000.0)
        assert result is not None
        assert result.predicted_ratio >= 0.0

    def test_predicted_ratio_clamped_to_one_maximum(self):
        # Steeply rising ratio — should not exceed 1
        t = _tracker(
            _snap(0.0, 0, 100),
            _snap(1.0, 100, 0),
        )
        result = forecast_hit_ratio(t, seconds_ahead=1000.0)
        assert result is not None
        assert result.predicted_ratio <= 1.0

    def test_stable_trend_predicts_same_ratio(self):
        t = _tracker(
            _snap(0.0, 75, 25),
            _snap(10.0, 75, 25),
            _snap(20.0, 75, 25),
        )
        result = forecast_hit_ratio(t, seconds_ahead=30.0)
        assert result is not None
        assert abs(result.predicted_ratio - 0.75) < 0.01

    def test_str_contains_forecast_info(self):
        t = _tracker(
            _snap(0.0, 50, 50),
            _snap(10.0, 60, 40),
        )
        result = forecast_hit_ratio(t, seconds_ahead=30.0)
        assert result is not None
        text = str(result)
        assert "Forecast" in text
        assert "30s" in text

    def test_slope_positive_when_ratio_rising(self):
        t = _tracker(
            _snap(0.0, 40, 60),
            _snap(10.0, 60, 40),
        )
        result = forecast_hit_ratio(t, seconds_ahead=10.0)
        assert result is not None
        assert result.slope > 0
