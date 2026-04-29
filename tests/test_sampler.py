"""Tests for cachewatch.sampler."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker, Snapshot
from cachewatch.sampler import SampleResult, sample_snapshots, sample_tracker


def _snap(hits: int, misses: int, ts: float = 0.0) -> Snapshot:
    stats = CacheStats(hits=hits, misses=misses)
    return Snapshot(stats=stats, timestamp=datetime.fromtimestamp(ts, tz=timezone.utc))


def _tracker(n: int) -> StatsTracker:
    t = StatsTracker()
    for i in range(n):
        t.record(_snap(i * 10, i * 2, ts=float(i)))
    return t


class TestSampleSnapshots:
    def test_empty_list_returns_empty(self):
        result = sample_snapshots([], step=2)
        assert result.snapshots == []
        assert result.original_count == 0
        assert result.sampled_count == 0

    def test_step_one_returns_all(self):
        snaps = [_snap(i, 0) for i in range(5)]
        result = sample_snapshots(snaps, step=1)
        assert result.snapshots == snaps
        assert result.sampled_count == 5

    def test_step_two_halves_list(self):
        snaps = [_snap(i, 0) for i in range(6)]
        result = sample_snapshots(snaps, step=2)
        assert result.sampled_count == 3
        assert result.snapshots == snaps[::2]

    def test_step_larger_than_list(self):
        snaps = [_snap(i, 0) for i in range(3)]
        result = sample_snapshots(snaps, step=10)
        assert result.sampled_count == 1
        assert result.snapshots[0] == snaps[0]

    def test_step_stored_in_result(self):
        snaps = [_snap(i, 0) for i in range(4)]
        result = sample_snapshots(snaps, step=3)
        assert result.step == 3

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError, match="step must be >= 1"):
            sample_snapshots([], step=0)

    def test_original_count_preserved(self):
        snaps = [_snap(i, 0) for i in range(10)]
        result = sample_snapshots(snaps, step=3)
        assert result.original_count == 10


class TestSampleTracker:
    def test_empty_tracker(self):
        t = StatsTracker()
        result = sample_tracker(t, step=2)
        assert result.snapshots == []
        assert result.original_count == 0

    def test_respects_step(self):
        t = _tracker(10)
        result = sample_tracker(t, step=2)
        assert result.step == 2
        assert result.sampled_count == 5

    def test_max_points_limits_output(self):
        t = _tracker(100)
        result = sample_tracker(t, max_points=10)
        assert result.sampled_count <= 10

    def test_max_points_overrides_step(self):
        t = _tracker(50)
        result = sample_tracker(t, step=1, max_points=5)
        assert result.sampled_count <= 5

    def test_max_points_no_effect_when_small(self):
        """If tracker has fewer snapshots than max_points, return all."""
        t = _tracker(4)
        result = sample_tracker(t, step=1, max_points=20)
        assert result.sampled_count == 4
