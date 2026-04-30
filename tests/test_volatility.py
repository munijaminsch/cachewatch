"""Tests for cachewatch.volatility."""
from __future__ import annotations

import math
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.volatility import VolatilityResult, compute_volatility


def _snap(hits: int, misses: int, ts: float = 0.0) -> CacheStats:
    return CacheStats(hits=hits, misses=misses)


def _tracker(records: List[tuple]) -> StatsTracker:
    t = StatsTracker()
    for i, (hits, misses) in enumerate(records):
        t.record(CacheStats(hits=hits, misses=misses), timestamp=float(i))
    return t


class TestComputeVolatility:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert compute_volatility(t) is None

    def test_returns_result_with_single_snapshot(self):
        t = _tracker([(10, 0)])
        result = compute_volatility(t)
        assert result is not None
        assert result.std_dev is None
        assert result.mean is None

    def test_std_dev_zero_for_constant_ratios(self):
        t = _tracker([(10, 0), (20, 0), (30, 0)])
        result = compute_volatility(t)
        assert result is not None
        assert result.std_dev == pytest.approx(0.0)
        assert result.mean == pytest.approx(1.0)

    def test_std_dev_nonzero_for_varying_ratios(self):
        # hits=10,misses=0 -> ratio 1.0; hits=5,misses=5 -> ratio 0.5
        t = _tracker([(10, 0), (5, 5)])
        result = compute_volatility(t)
        assert result is not None
        assert result.std_dev is not None
        assert result.std_dev > 0

    def test_min_max_correct(self):
        t = _tracker([(10, 0), (5, 5), (1, 9)])
        result = compute_volatility(t)
        assert result is not None
        assert result.min_ratio == pytest.approx(0.1)
        assert result.max_ratio == pytest.approx(1.0)

    def test_window_reflects_last_n(self):
        t = _tracker([(10, 0), (5, 5), (8, 2), (6, 4)])
        result = compute_volatility(t, last_n=2)
        assert result is not None
        assert result.window == 2

    def test_last_n_larger_than_history_uses_all(self):
        t = _tracker([(10, 0), (5, 5)])
        result = compute_volatility(t, last_n=100)
        assert result is not None
        assert result.window == 2

    def test_mean_calculation(self):
        t = _tracker([(10, 0), (0, 10)])  # ratios: 1.0, 0.0
        result = compute_volatility(t)
        assert result is not None
        assert result.mean == pytest.approx(0.5)

    def test_volatility_result_window_matches_snapshot_count(self):
        t = _tracker([(10, 0)] * 5)
        result = compute_volatility(t)
        assert result is not None
        assert result.window == 5
