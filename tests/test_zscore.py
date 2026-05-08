"""Tests for cachewatch.zscore."""
from __future__ import annotations

import time
from typing import Optional

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.zscore import ZScorePoint, compute_zscores


def _snap(hits: int, misses: int, ts: Optional[float] = None) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts or time.time())


def _tracker(*snapshots: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


class TestComputeZScores:
    def test_empty_tracker_returns_empty(self):
        t = _tracker()
        assert compute_zscores(t) == []

    def test_single_snapshot_zscore_is_zero(self):
        t = _tracker(_snap(80, 20, ts=1000.0))
        result = compute_zscores(t)
        assert len(result) == 1
        assert result[0].zscore == 0.0

    def test_two_equal_snapshots_both_zero(self):
        t = _tracker(_snap(80, 20, ts=1000.0), _snap(80, 20, ts=2000.0))
        result = compute_zscores(t)
        assert all(p.zscore == 0.0 for p in result)

    def test_returns_zscore_point_instances(self):
        t = _tracker(_snap(50, 50, ts=1.0), _snap(90, 10, ts=2.0))
        result = compute_zscores(t)
        assert all(isinstance(p, ZScorePoint) for p in result)

    def test_length_matches_history(self):
        snaps = [_snap(i * 10, 100 - i * 10, ts=float(i)) for i in range(1, 6)]
        t = _tracker(*snaps)
        result = compute_zscores(t)
        assert len(result) == 5

    def test_high_outlier_has_positive_zscore(self):
        # one snapshot with a much higher ratio
        snaps = [
            _snap(50, 50, ts=1.0),
            _snap(50, 50, ts=2.0),
            _snap(50, 50, ts=3.0),
            _snap(99, 1, ts=4.0),  # outlier
        ]
        t = _tracker(*snaps)
        result = compute_zscores(t)
        assert result[-1].zscore is not None
        assert result[-1].zscore > 1.0

    def test_low_outlier_has_negative_zscore(self):
        snaps = [
            _snap(90, 10, ts=1.0),
            _snap(90, 10, ts=2.0),
            _snap(90, 10, ts=3.0),
            _snap(1, 99, ts=4.0),  # outlier
        ]
        t = _tracker(*snaps)
        result = compute_zscores(t)
        assert result[-1].zscore is not None
        assert result[-1].zscore < -1.0

    def test_timestamps_preserved(self):
        snaps = [_snap(70, 30, ts=float(i * 100)) for i in range(1, 4)]
        t = _tracker(*snaps)
        result = compute_zscores(t)
        for point, snap in zip(result, snaps):
            assert point.timestamp == snap.timestamp

    def test_str_contains_z(self):
        t = _tracker(_snap(60, 40, ts=500.0), _snap(80, 20, ts=600.0))
        result = compute_zscores(t)
        for p in result:
            s = str(p)
            assert "ZScorePoint" in s
            assert "z=" in s
