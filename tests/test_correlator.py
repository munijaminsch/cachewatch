"""Tests for cachewatch.correlator."""

from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker, Snapshot
from cachewatch.correlator import CorrelationResult, correlate_trackers


def _snap(hits: int, misses: int, ts: float | None = None) -> Snapshot:
    stats = CacheStats(hits=hits, misses=misses)
    return Snapshot(stats=stats, timestamp=ts or time.time())


def _tracker(pairs: List[tuple]) -> StatsTracker:
    t = StatsTracker()
    base = 1_000_000.0
    for i, (h, m) in enumerate(pairs):
        t.record(_snap(h, m, ts=base + i))
    return t


class TestCorrelateTrackers:
    def test_returns_none_when_both_empty(self):
        a = StatsTracker()
        b = StatsTracker()
        assert correlate_trackers(a, b) is None

    def test_returns_none_when_one_empty(self):
        a = _tracker([(10, 0), (20, 0)])
        b = StatsTracker()
        assert correlate_trackers(a, b) is None

    def test_returns_none_with_single_pair(self):
        a = _tracker([(10, 0)])
        b = _tracker([(5, 5)])
        assert correlate_trackers(a, b) is None

    def test_returns_none_when_constant_series(self):
        # std dev is zero — correlation undefined
        a = _tracker([(10, 0), (10, 0), (10, 0)])
        b = _tracker([(5, 5), (6, 4), (7, 3)])
        assert correlate_trackers(a, b) is None

    def test_perfect_positive_correlation(self):
        # both series move identically
        pairs = [(i, 10 - i) for i in range(1, 6)]
        a = _tracker(pairs)
        b = _tracker(pairs)
        result = correlate_trackers(a, b)
        assert result is not None
        assert abs(result.pearson_r - 1.0) < 1e-9
        assert result.n == 5

    def test_perfect_negative_correlation(self):
        a = _tracker([(i, 10 - i) for i in range(1, 6)])
        b = _tracker([(10 - i, i) for i in range(1, 6)])
        result = correlate_trackers(a, b)
        assert result is not None
        assert abs(result.pearson_r + 1.0) < 1e-9

    def test_uses_overlapping_length(self):
        a = _tracker([(i, 10 - i) for i in range(1, 8)])  # 7 snapshots
        b = _tracker([(i, 10 - i) for i in range(1, 5)])  # 4 snapshots
        result = correlate_trackers(a, b)
        assert result is not None
        assert result.n == 4

    def test_returns_correlation_result_type(self):
        a = _tracker([(3, 7), (5, 5), (7, 3)])
        b = _tracker([(2, 8), (4, 6), (6, 4)])
        result = correlate_trackers(a, b)
        assert isinstance(result, CorrelationResult)

    def test_str_contains_r_and_n(self):
        a = _tracker([(3, 7), (5, 5), (7, 3)])
        b = _tracker([(2, 8), (4, 6), (6, 4)])
        result = correlate_trackers(a, b)
        assert result is not None
        s = str(result)
        assert "pearson_r" in s or "r=" in s
        assert str(result.n) in s

    def test_interpretation_very_strong(self):
        pairs = [(i, 10 - i) for i in range(1, 6)]
        a = _tracker(pairs)
        b = _tracker(pairs)
        result = correlate_trackers(a, b)
        assert result is not None
        assert "very strong" in result.interpretation
        assert "positive" in result.interpretation
