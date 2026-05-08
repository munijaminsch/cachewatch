"""Tests for cachewatch.regression."""
from __future__ import annotations

import time
from typing import List
from unittest.mock import patch

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.regression import RegressionResult, compute_regression


def _snap(hits: int, misses: int, ts: float) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts)


def _tracker(records: List[CacheStats]) -> StatsTracker:
    t = StatsTracker()
    for r in records:
        t.record(r)
    return t


class TestComputeRegression:
    def test_returns_none_when_empty(self):
        t = _tracker([])
        assert compute_regression(t) is None

    def test_returns_none_with_single_snapshot_degree_1(self):
        t = _tracker([_snap(10, 5, 1000.0)])
        assert compute_regression(t, degree=1) is None

    def test_returns_none_when_insufficient_for_degree(self):
        # degree=2 requires at least 3 snapshots
        snaps = [_snap(10, 5, float(i)) for i in range(2)]
        t = _tracker(snaps)
        assert compute_regression(t, degree=2) is None

    def test_returns_regression_result_linear(self):
        snaps = [
            _snap(10, 10, 0.0),
            _snap(20, 5, 1.0),
            _snap(30, 0, 2.0),
        ]
        t = _tracker(snaps)
        result = compute_regression(t, degree=1)
        assert isinstance(result, RegressionResult)
        assert result.degree == 1
        assert result.sample_count == 3
        assert len(result.coefficients) == 2  # slope + intercept

    def test_r_squared_is_none_for_two_points_constant_y(self):
        # constant y -> ss_tot == 0 -> r2 is None
        snaps = [
            _snap(10, 0, 0.0),
            _snap(10, 0, 1.0),
        ]
        t = _tracker(snaps)
        result = compute_regression(t, degree=1)
        assert result is not None
        assert result.r_squared is None

    def test_r_squared_near_one_for_perfect_linear(self):
        # hit_ratio increases perfectly linearly
        snaps = [
            _snap(hits=i * 10, misses=100 - i * 10, ts=float(i))
            for i in range(1, 6)
        ]
        t = _tracker(snaps)
        result = compute_regression(t, degree=1)
        assert result is not None
        assert result.r_squared is not None
        assert result.r_squared == pytest.approx(1.0, abs=1e-6)

    def test_degree_2_returns_three_coefficients(self):
        snaps = [_snap(i * 5, 100 - i * 5, float(i)) for i in range(1, 6)]
        t = _tracker(snaps)
        result = compute_regression(t, degree=2)
        assert result is not None
        assert len(result.coefficients) == 3

    def test_returns_none_when_numpy_unavailable(self):
        snaps = [_snap(10, 5, float(i)) for i in range(3)]
        t = _tracker(snaps)
        with patch.dict("sys.modules", {"numpy": None}):
            result = compute_regression(t, degree=1)
        assert result is None
