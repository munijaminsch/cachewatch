"""Tests for cachewatch.cusum."""
from __future__ import annotations

from typing import Optional

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.cusum import CusumResult, detect_cusum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(hits: int, misses: int, ts: float) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts)


def _tracker(*snapshots: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


# ---------------------------------------------------------------------------
# CusumResult
# ---------------------------------------------------------------------------

class TestCusumResult:
    def test_str_no_change(self):
        r = CusumResult(
            change_point_ts=None,
            cusum_high=[0.0],
            cusum_low=[0.0],
            threshold=0.1,
            drift=0.005,
        )
        text = str(r)
        assert "no change" in text
        assert "0.1000" in text

    def test_str_with_change(self):
        r = CusumResult(
            change_point_ts=42.5,
            cusum_high=[0.15],
            cusum_low=[0.0],
            threshold=0.1,
            drift=0.005,
        )
        text = str(r)
        assert "42.50" in text
        assert "0.1000" in text


# ---------------------------------------------------------------------------
# detect_cusum
# ---------------------------------------------------------------------------

class TestDetectCusum:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert detect_cusum(t) is None

    def test_returns_none_with_single_snapshot(self):
        t = _tracker(_snap(80, 20, 1.0))
        assert detect_cusum(t) is None

    def test_returns_result_for_two_snapshots(self):
        t = _tracker(_snap(80, 20, 1.0), _snap(60, 40, 2.0))
        result = detect_cusum(t)
        assert isinstance(result, CusumResult)

    def test_series_lengths_match_snapshots(self):
        snaps = [_snap(80, 20, float(i)) for i in range(10)]
        t = _tracker(*snaps)
        result = detect_cusum(t)
        assert len(result.cusum_high) == 10
        assert len(result.cusum_low) == 10

    def test_no_change_on_stable_series(self):
        # Perfectly uniform hit ratio — no change point expected.
        snaps = [_snap(80, 20, float(i)) for i in range(20)]
        t = _tracker(*snaps)
        result = detect_cusum(t, threshold=0.10, drift=0.005)
        assert result.change_point_ts is None

    def test_detects_sudden_drop(self):
        # First 10 snaps: 90 % hit ratio; next 10: 10 % hit ratio.
        high = [_snap(90, 10, float(i)) for i in range(10)]
        low = [_snap(10, 90, float(i + 10)) for i in range(10)]
        t = _tracker(*(high + low))
        result = detect_cusum(t, threshold=0.05, drift=0.001)
        assert result.change_point_ts is not None
        # Change point must be in the second half.
        assert result.change_point_ts >= 10.0

    def test_threshold_stored_on_result(self):
        t = _tracker(_snap(70, 30, 1.0), _snap(70, 30, 2.0))
        result = detect_cusum(t, threshold=0.25, drift=0.01)
        assert result.threshold == pytest.approx(0.25)
        assert result.drift == pytest.approx(0.01)

    def test_cusum_values_non_negative(self):
        snaps = [_snap(50, 50, float(i)) for i in range(15)]
        t = _tracker(*snaps)
        result = detect_cusum(t)
        assert all(v >= 0.0 for v in result.cusum_high)
        assert all(v >= 0.0 for v in result.cusum_low)
