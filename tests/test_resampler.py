"""Tests for cachewatch.resampler."""

from __future__ import annotations

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.resampler import ResampledPoint, resample_tracker


def _snap(ts: float, hits: int, misses: int) -> object:
    """Create a minimal snapshot-like object accepted by StatsTracker."""

    class _Snap:
        def __init__(self):
            self.timestamp = ts
            self.stats = CacheStats(hits=hits, misses=misses)

    return _Snap()


def _tracker(*snaps) -> StatsTracker:
    t = StatsTracker()
    for s in snaps:
        t.record(s)
    return t


# ---------------------------------------------------------------------------
# ResampledPoint.__str__
# ---------------------------------------------------------------------------

class TestResampledPointStr:
    def test_str_with_ratio(self):
        pt = ResampledPoint(bucket_ts=1000.0, interval_seconds=60, count=3, average_hit_ratio=0.85)
        s = str(pt)
        assert "1000" in s
        assert "60" in s
        assert "0.8500" in s

    def test_str_none_ratio(self):
        pt = ResampledPoint(bucket_ts=2000.0, interval_seconds=30, count=0, average_hit_ratio=None)
        assert "N/A" in str(pt)


# ---------------------------------------------------------------------------
# resample_tracker
# ---------------------------------------------------------------------------

class TestResampleTracker:
    def test_empty_tracker_returns_empty(self):
        t = _tracker()
        assert resample_tracker(t, interval_seconds=60) == []

    def test_single_snapshot_one_bucket(self):
        t = _tracker(_snap(100.0, hits=8, misses=2))
        result = resample_tracker(t, interval_seconds=60)
        assert len(result) == 1
        assert result[0].count == 1
        assert result[0].average_hit_ratio == pytest.approx(0.8)

    def test_two_snapshots_same_bucket(self):
        t = _tracker(
            _snap(0.0, hits=10, misses=0),
            _snap(30.0, hits=6, misses=4),
        )
        result = resample_tracker(t, interval_seconds=60)
        assert len(result) == 1
        assert result[0].count == 2
        assert result[0].average_hit_ratio == pytest.approx(0.9)

    def test_two_snapshots_different_buckets(self):
        t = _tracker(
            _snap(0.0, hits=10, misses=0),
            _snap(60.0, hits=4, misses=6),
        )
        result = resample_tracker(t, interval_seconds=60)
        assert len(result) == 2
        assert result[0].average_hit_ratio == pytest.approx(1.0)
        assert result[1].average_hit_ratio == pytest.approx(0.4)

    def test_bucket_ts_is_floored(self):
        t = _tracker(_snap(75.0, hits=5, misses=5))
        result = resample_tracker(t, interval_seconds=60)
        assert result[0].bucket_ts == pytest.approx(60.0)

    def test_results_sorted_by_bucket_ts(self):
        t = _tracker(
            _snap(120.0, hits=9, misses=1),
            _snap(0.0, hits=7, misses=3),
            _snap(60.0, hits=5, misses=5),
        )
        result = resample_tracker(t, interval_seconds=60)
        ts_list = [r.bucket_ts for r in result]
        assert ts_list == sorted(ts_list)

    def test_interval_seconds_below_one_raises(self):
        t = _tracker(_snap(0.0, hits=1, misses=1))
        with pytest.raises(ValueError, match="interval_seconds must be >= 1"):
            resample_tracker(t, interval_seconds=0)

    def test_interval_seconds_stored_on_point(self):
        t = _tracker(_snap(0.0, hits=3, misses=7))
        result = resample_tracker(t, interval_seconds=120)
        assert result[0].interval_seconds == 120
