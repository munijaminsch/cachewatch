"""Unit tests for StatsTracker."""

import time
import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker


def make_snapshot(hits: int, misses: int, ts: float = None) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts or time.time())


class TestStatsTracker:
    def test_latest_none_when_empty(self):
        tracker = StatsTracker()
        assert tracker.latest is None

    def test_record_and_latest(self):
        tracker = StatsTracker()
        snap = make_snapshot(100, 20)
        tracker.record(snap)
        assert tracker.latest is snap

    def test_delta_none_with_single_snapshot(self):
        tracker = StatsTracker()
        tracker.record(make_snapshot(100, 20))
        assert tracker.delta() is None

    def test_delta_computes_correctly(self):
        tracker = StatsTracker()
        tracker.record(make_snapshot(hits=100, misses=20))
        tracker.record(make_snapshot(hits=130, misses=25))
        hits_delta, misses_delta = tracker.delta()
        assert hits_delta == 30
        assert misses_delta == 5

    def test_delta_clamps_negative_values_to_zero(self):
        """Handles Redis restart where counters reset."""
        tracker = StatsTracker()
        tracker.record(make_snapshot(hits=500, misses=100))
        tracker.record(make_snapshot(hits=10, misses=2))
        hits_delta, misses_delta = tracker.delta()
        assert hits_delta == 0
        assert misses_delta == 0

    def test_hit_ratio_series(self):
        tracker = StatsTracker()
        tracker.record(make_snapshot(hits=50, misses=50))
        tracker.record(make_snapshot(hits=150, misses=50))
        series = tracker.hit_ratio_series()
        assert len(series) == 2
        assert series[0] == pytest.approx(0.5)
        assert series[1] == pytest.approx(0.75)

    def test_requests_per_second(self):
        tracker = StatsTracker()
        tracker.record(make_snapshot(hits=0, misses=0, ts=0.0))
        tracker.record(make_snapshot(hits=100, misses=20, ts=1.0))
        rps = tracker.requests_per_second()
        assert rps == pytest.approx(120.0)

    def test_max_history_respected(self):
        tracker = StatsTracker(max_history=5)
        for i in range(10):
            tracker.record(make_snapshot(hits=i, misses=0))
        assert len(tracker.history) == 5
