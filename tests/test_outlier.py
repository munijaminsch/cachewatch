"""Tests for cachewatch.outlier."""
from __future__ import annotations

import pytest

from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats
from cachewatch.outlier import OutlierResult, detect_outliers


def _snap(ts: float, hits: int, misses: int) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts)


def _tracker(*snaps: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snaps:
        t.record(s)
    return t


def _uniform_tracker(count: int, hits: int, misses: int) -> StatsTracker:
    """Return a StatsTracker populated with ``count`` identical snapshots."""
    snaps = [_snap(float(i), hits, misses) for i in range(count)]
    return _tracker(*snaps)


class TestOutlierResult:
    def test_str_contains_ts_and_ratio(self):
        r = OutlierResult(timestamp=1.0, hit_ratio=0.9, mean=0.5, std_dev=0.1, z_score=4.0)
        s = str(r)
        assert "1.0" in s
        assert "0.900" in s
        assert "high" in s

    def test_str_low_direction(self):
        r = OutlierResult(timestamp=2.0, hit_ratio=0.1, mean=0.5, std_dev=0.1, z_score=-4.0)
        assert "low" in str(r)


class TestDetectOutliers:
    def test_returns_empty_when_tracker_empty(self):
        t = _tracker()
        assert detect_outliers(t) == []

    def test_returns_empty_with_two_snapshots(self):
        t = _tracker(_snap(1.0, 10, 10), _snap(2.0, 10, 10))
        assert detect_outliers(t) == []

    def test_returns_empty_when_all_identical(self):
        t = _uniform_tracker(10, hits=8, misses=2)
        assert detect_outliers(t) == []

    def test_detects_high_outlier(self):
        # 9 normal snapshots + 1 spike
        snaps = [_snap(float(i), 5, 5) for i in range(9)]  # ratio=0.5 each
        snaps.append(_snap(9.0, 99, 1))  # ratio=0.99 — spike
        t = _tracker(*snaps)
        results = detect_outliers(t, z_threshold=2.0)
        assert len(results) >= 1
        assert any(r.hit_ratio > 0.9 for r in results)

    def test_detects_low_outlier(self):
        snaps = [_snap(float(i), 9, 1) for i in range(9)]  # ratio=0.9
        snaps.append(_snap(9.0, 1, 99))  # ratio=0.01
        t = _tracker(*snaps)
        results = detect_outliers(t, z_threshold=2.0)
        assert any(r.hit_ratio < 0.1 for r in results)

    def test_outlier_result_fields(self):
        snaps = [_snap(float(i), 5, 5) for i in range(9)]
        snaps.append(_snap(9.0, 99, 1))
        t = _tracker(*snaps)
        results = detect_outliers(t, z_threshold=2.0)
        r = results[-1]
        assert isinstance(r.z_score, float)
        assert r.std_dev > 0
        assert 0.0 <= r.mean <= 1.0

    def test_custom_z_threshold_stricter(self):
        snaps = [_snap(float(i), 5, 5) for i in range(9)]
        snaps.append(_snap(9.0, 99, 1))
        t = _tracker(*snaps)
        loose = detect_outliers(t, z_threshold=1.0)
        strict = detect_outliers(t, z_threshold=3.5)
        assert len(loose) >= len(strict)

    def test_no_false_positives_with_gradual_increase(self):
        """Smoothly rising hit ratios should not trigger outlier detection."""
        # ratios: 0.50, 0.55, 0.60, ..., 0.95 — linear ramp, no sharp spike
        snaps = [_snap(float(i), 50 + i * 5, 50 - i * 5) for i in range(10)]
        t = _tracker(*snaps)
        results = detect_outliers(t, z_threshold=2.0)
        assert results == []
