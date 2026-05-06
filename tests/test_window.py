"""Tests for cachewatch.window."""
from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.window import WindowResult, compute_window


def _snap(ts: float, hits: int, misses: int) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts)


def _tracker(*snapshots: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


# ---------------------------------------------------------------------------
# WindowResult
# ---------------------------------------------------------------------------

class TestWindowResult:
    def test_str_contains_window_seconds(self):
        r = WindowResult(
            window_seconds=60,
            count=5,
            avg_hit_ratio=0.9,
            min_hit_ratio=0.8,
            max_hit_ratio=1.0,
            range_hit_ratio=0.2,
        )
        assert "60" in str(r)

    def test_str_na_when_none(self):
        r = WindowResult(
            window_seconds=30,
            count=0,
            avg_hit_ratio=None,
            min_hit_ratio=None,
            max_hit_ratio=None,
            range_hit_ratio=None,
        )
        assert "N/A" in str(r)


# ---------------------------------------------------------------------------
# compute_window
# ---------------------------------------------------------------------------

class TestComputeWindow:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert compute_window(t, 60) is None

    def test_returns_window_result(self):
        now = 1_000.0
        t = _tracker(
            _snap(now - 50, 80, 20),
            _snap(now - 30, 90, 10),
            _snap(now - 10, 95, 5),
        )
        result = compute_window(t, 60, reference_ts=now)
        assert isinstance(result, WindowResult)

    def test_count_matches_window(self):
        now = 1_000.0
        t = _tracker(
            _snap(now - 120, 50, 50),  # outside 60 s window
            _snap(now - 50, 80, 20),
            _snap(now - 10, 90, 10),
        )
        result = compute_window(t, 60, reference_ts=now)
        assert result is not None
        assert result.count == 2

    def test_avg_hit_ratio_correct(self):
        now = 1_000.0
        t = _tracker(
            _snap(now - 20, 60, 40),  # ratio 0.6
            _snap(now - 10, 80, 20),  # ratio 0.8
        )
        result = compute_window(t, 60, reference_ts=now)
        assert result is not None
        assert result.avg_hit_ratio == pytest.approx(0.7, abs=1e-6)

    def test_min_max_range(self):
        now = 1_000.0
        t = _tracker(
            _snap(now - 30, 50, 50),  # 0.5
            _snap(now - 20, 70, 30),  # 0.7
            _snap(now - 10, 90, 10),  # 0.9
        )
        result = compute_window(t, 60, reference_ts=now)
        assert result is not None
        assert result.min_hit_ratio == pytest.approx(0.5, abs=1e-6)
        assert result.max_hit_ratio == pytest.approx(0.9, abs=1e-6)
        assert result.range_hit_ratio == pytest.approx(0.4, abs=1e-6)

    def test_uses_latest_snapshot_ts_as_default_reference(self):
        base = 2_000.0
        t = _tracker(
            _snap(base - 200, 40, 60),
            _snap(base - 10, 80, 20),
            _snap(base, 90, 10),
        )
        # Without explicit reference_ts, should use base (the latest)
        result = compute_window(t, 60)
        assert result is not None
        assert result.count == 2  # only the last two fall within 60 s

    def test_all_outside_window_gives_zero_count(self):
        now = 5_000.0
        t = _tracker(
            _snap(now - 200, 80, 20),
            _snap(now - 150, 70, 30),
        )
        result = compute_window(t, 60, reference_ts=now)
        assert result is not None
        assert result.count == 0
        assert result.avg_hit_ratio is None
