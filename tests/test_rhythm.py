"""Tests for cachewatch.rhythm."""

import time
from unittest.mock import MagicMock

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.rhythm import RhythmResult, detect_rhythm, _autocorrelate


def _snap(hits: int, misses: int, ts: float):
    snap = MagicMock()
    snap.stats = CacheStats(hits=hits, misses=misses)
    snap.timestamp = ts
    return snap


def _tracker(records):
    tracker = MagicMock(spec=StatsTracker)
    tracker.history.return_value = records
    return tracker


# ---------------------------------------------------------------------------
# _autocorrelate
# ---------------------------------------------------------------------------

class TestAutocorrelate:
    def test_empty_returns_zero(self):
        assert _autocorrelate([], 1) == 0.0

    def test_constant_series_returns_zero(self):
        # variance is 0 → returns 0.0 to avoid division by zero
        assert _autocorrelate([0.5, 0.5, 0.5, 0.5], 1) == 0.0

    def test_lag_larger_than_series_returns_zero(self):
        assert _autocorrelate([0.1, 0.2], 5) == 0.0

    def test_periodic_series_has_positive_correlation(self):
        # Perfect sine-like alternation at lag 2
        values = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
        corr = _autocorrelate(values, 2)
        assert corr > 0.5


# ---------------------------------------------------------------------------
# detect_rhythm
# ---------------------------------------------------------------------------

class TestDetectRhythm:
    def test_returns_none_when_empty(self):
        assert detect_rhythm(_tracker([])) is None

    def test_returns_none_with_three_snapshots(self):
        snaps = [_snap(8, 2, float(i)) for i in range(3)]
        assert detect_rhythm(_tracker(snaps)) is None

    def test_returns_rhythm_result_with_four_snapshots(self):
        snaps = [_snap(8, 2, float(i)) for i in range(4)]
        result = detect_rhythm(_tracker(snaps))
        assert isinstance(result, RhythmResult)

    def test_sample_count_matches_snapshot_count(self):
        snaps = [_snap(7, 3, float(i)) for i in range(10)]
        result = detect_rhythm(_tracker(snaps))
        assert result.sample_count == 10

    def test_strength_between_zero_and_one(self):
        snaps = [_snap(9, 1, float(i)) for i in range(8)]
        result = detect_rhythm(_tracker(snaps))
        assert 0.0 <= result.strength <= 1.0

    def test_period_seconds_positive(self):
        snaps = [_snap(8, 2, float(i)) for i in range(8)]
        result = detect_rhythm(_tracker(snaps))
        assert result.period_seconds > 0.0

    def test_mean_ratio_computed_correctly(self):
        # All snapshots have ratio 0.8
        snaps = [_snap(8, 2, float(i)) for i in range(6)]
        result = detect_rhythm(_tracker(snaps))
        assert abs(result.mean_ratio - 0.8) < 1e-9

    def test_str_contains_period_and_strength(self):
        snaps = [_snap(6, 4, float(i)) for i in range(6)]
        result = detect_rhythm(_tracker(snaps))
        s = str(result)
        assert "period=" in s
        assert "strength=" in s
