"""Tests for cachewatch.comparator."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.comparator import compare_windows, ComparisonResult


BASE = 1_700_000_000.0


def _snap(ts: float, hits: int, misses: int):
    snap = MagicMock()
    snap.timestamp = ts
    snap.stats = CacheStats(hits=hits, misses=misses)
    return snap


def _tracker(*snaps):
    t = StatsTracker()
    for s in snaps:
        t._history.append(s)  # bypass record() to control timestamps
    return t


class TestCompareWindows:
    def test_returns_comparison_result(self):
        t = _tracker(
            _snap(BASE + 1, 80, 20),
            _snap(BASE + 2, 70, 30),
            _snap(BASE + 11, 90, 10),
            _snap(BASE + 12, 95, 5),
        )
        result = compare_windows(t, BASE, BASE + 5, BASE + 10, BASE + 15)
        assert isinstance(result, ComparisonResult)

    def test_delta_positive_when_b_better(self):
        t = _tracker(
            _snap(BASE + 1, 60, 40),
            _snap(BASE + 11, 90, 10),
        )
        result = compare_windows(t, BASE, BASE + 5, BASE + 10, BASE + 15)
        assert result.delta > 0
        assert result.improved is True

    def test_delta_negative_when_b_worse(self):
        t = _tracker(
            _snap(BASE + 1, 90, 10),
            _snap(BASE + 11, 60, 40),
        )
        result = compare_windows(t, BASE, BASE + 5, BASE + 10, BASE + 15)
        assert result.delta < 0
        assert result.improved is False

    def test_none_delta_when_window_a_empty(self):
        t = _tracker(_snap(BASE + 11, 80, 20))
        result = compare_windows(t, BASE, BASE + 5, BASE + 10, BASE + 15)
        assert result.delta is None
        assert result.window_a_avg is None

    def test_none_delta_when_window_b_empty(self):
        t = _tracker(_snap(BASE + 1, 80, 20))
        result = compare_windows(t, BASE, BASE + 5, BASE + 10, BASE + 15)
        assert result.delta is None
        assert result.window_b_avg is None

    def test_str_insufficient_data(self):
        result = ComparisonResult(None, None, None, None)
        assert "insufficient" in str(result)

    def test_str_with_data(self):
        result = ComparisonResult(0.75, 0.85, 0.10, True)
        s = str(result)
        assert "improved" in s
        assert "A=" in s and "B=" in s

    def test_averages_are_correct(self):
        t = _tracker(
            _snap(BASE + 1, 80, 20),   # 0.80
            _snap(BASE + 2, 60, 40),   # 0.60  avg_a = 0.70
            _snap(BASE + 11, 90, 10),  # 0.90
            _snap(BASE + 12, 80, 20),  # 0.80  avg_b = 0.85
        )
        result = compare_windows(t, BASE, BASE + 5, BASE + 10, BASE + 15)
        assert abs(result.window_a_avg - 0.70) < 1e-9
        assert abs(result.window_b_avg - 0.85) < 1e-9
