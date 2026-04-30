"""Tests for cachewatch.divergence."""
from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.divergence import DivergenceResult, compute_divergence


def _snap(hits: int, misses: int, ts: float | None = None) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts or time.time())


def _tracker(records: List[CacheStats]) -> StatsTracker:
    t = StatsTracker()
    for r in records:
        t.record(r)
    return t


class TestComputeDivergence:
    def test_returns_none_when_both_empty(self):
        a = _tracker([])
        b = _tracker([])
        assert compute_divergence(a, b) is None

    def test_returns_none_when_one_empty(self):
        a = _tracker([_snap(10, 2)])
        b = _tracker([])
        assert compute_divergence(a, b) is None

    def test_returns_none_with_single_snapshot_each(self):
        a = _tracker([_snap(10, 2, ts=1.0)])
        b = _tracker([_snap(8, 4, ts=1.0)])
        assert compute_divergence(a, b) is None

    def test_returns_divergence_result(self):
        a = _tracker([_snap(10, 0, ts=1.0), _snap(8, 2, ts=2.0)])
        b = _tracker([_snap(6, 4, ts=1.0), _snap(5, 5, ts=2.0)])
        result = compute_divergence(a, b)
        assert isinstance(result, DivergenceResult)

    def test_sample_count_uses_shorter_tracker(self):
        a = _tracker([_snap(10, 0, ts=float(i)) for i in range(5)])
        b = _tracker([_snap(8, 2, ts=float(i)) for i in range(3)])
        result = compute_divergence(a, b)
        assert result is not None
        assert result.sample_count == 3

    def test_mean_a_and_mean_b_are_correct(self):
        # a always 1.0 hit ratio, b always 0.5
        a = _tracker([_snap(10, 0, ts=float(i)) for i in range(3)])
        b = _tracker([_snap(5, 5, ts=float(i)) for i in range(3)])
        result = compute_divergence(a, b)
        assert result is not None
        assert abs(result.mean_a - 1.0) < 1e-9
        assert abs(result.mean_b - 0.5) < 1e-9

    def test_mean_gap_is_b_minus_a(self):
        a = _tracker([_snap(10, 0, ts=float(i)) for i in range(3)])
        b = _tracker([_snap(5, 5, ts=float(i)) for i in range(3)])
        result = compute_divergence(a, b)
        assert result is not None
        assert abs(result.mean_gap - (-0.5)) < 1e-9

    def test_max_gap_by_absolute_value(self):
        ts = [1.0, 2.0, 3.0]
        a = _tracker([_snap(10, 0, ts=t) for t in ts])
        b_snaps = [
            _snap(5, 5, ts=1.0),   # gap = -0.5
            _snap(10, 0, ts=2.0),  # gap = 0.0
            _snap(0, 10, ts=3.0),  # gap = -1.0  <- largest absolute gap
        ]
        b = _tracker(b_snaps)
        result = compute_divergence(a, b)
        assert result is not None
        assert abs(result.max_gap - (-1.0)) < 1e-9

    def test_positive_mean_gap_when_b_better(self):
        a = _tracker([_snap(5, 5, ts=float(i)) for i in range(4)])
        b = _tracker([_snap(9, 1, ts=float(i)) for i in range(4)])
        result = compute_divergence(a, b)
        assert result is not None
        assert result.mean_gap > 0
