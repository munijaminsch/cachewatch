"""Tests for cachewatch.momentum."""

from __future__ import annotations

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.momentum import MomentumPoint, compute_momentum


def _snap(hits: int, misses: int, ts: float):
    stats = CacheStats(hits=hits, misses=misses)
    tracker = StatsTracker()
    tracker.record(stats, timestamp=ts)
    return tracker.latest()


def _tracker(*args) -> StatsTracker:
    """Build a tracker from (hits, misses, ts) tuples."""
    t = StatsTracker()
    for hits, misses, ts in args:
        t.record(CacheStats(hits=hits, misses=misses), timestamp=ts)
    return t


class TestComputeMomentum:
    def test_empty_tracker_returns_empty(self):
        t = StatsTracker()
        assert compute_momentum(t) == []

    def test_single_snapshot_momentum_is_none(self):
        t = _tracker((8, 2, 1000.0))
        points = compute_momentum(t)
        assert len(points) == 1
        assert points[0].momentum is None

    def test_two_snapshots_momentum_calculated(self):
        # ratio goes from 0.8 to 0.9 over 10 seconds => momentum = 0.01/s
        t = _tracker((8, 2, 1000.0), (9, 1, 1010.0))
        points = compute_momentum(t)
        assert len(points) == 2
        assert points[0].momentum is None
        assert points[1].momentum == pytest.approx(0.01, abs=1e-6)

    def test_decreasing_ratio_gives_negative_momentum(self):
        t = _tracker((9, 1, 0.0), (7, 3, 10.0))
        points = compute_momentum(t)
        assert points[1].momentum == pytest.approx(-0.02, abs=1e-6)

    def test_zero_time_delta_gives_none_momentum(self):
        t = _tracker((8, 2, 5.0), (9, 1, 5.0))
        points = compute_momentum(t)
        assert points[1].momentum is None

    def test_returns_correct_timestamps(self):
        t = _tracker((5, 5, 100.0), (6, 4, 110.0), (7, 3, 120.0))
        points = compute_momentum(t)
        assert [p.timestamp for p in points] == [100.0, 110.0, 120.0]

    def test_hit_ratios_preserved(self):
        t = _tracker((8, 2, 0.0), (6, 4, 10.0))
        points = compute_momentum(t)
        assert points[0].hit_ratio == pytest.approx(0.8)
        assert points[1].hit_ratio == pytest.approx(0.6)

    def test_str_first_point_no_momentum(self):
        t = _tracker((8, 2, 1000.0))
        pt = compute_momentum(t)[0]
        assert "N/A" in str(pt)
        assert "0.8000" in str(pt)

    def test_str_positive_momentum_has_plus_sign(self):
        t = _tracker((8, 2, 0.0), (9, 1, 10.0))
        pt = compute_momentum(t)[1]
        assert "+" in str(pt)

    def test_multiple_snapshots_length_matches(self):
        t = _tracker((1, 9, 0.0), (2, 8, 1.0), (3, 7, 2.0), (4, 6, 3.0))
        points = compute_momentum(t)
        assert len(points) == 4
