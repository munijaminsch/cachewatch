"""Tests for cachewatch.smoothing."""

from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.smoothing import SmoothedPoint, moving_average, smooth_tracker
from cachewatch.stats_tracker import StatsTracker


def _snap(hit_ratio: float, ts: float | None = None) -> CacheStats:
    if ts is None:
        ts = time.time()
    hits = int(hit_ratio * 100)
    misses = 100 - hits
    return CacheStats(hits=hits, misses=misses, timestamp=ts)


def _tracker(ratios: List[float]) -> StatsTracker:
    tracker = StatsTracker()
    for i, r in enumerate(ratios):
        snap = _snap(r, ts=float(i))
        tracker.record(snap)
    return tracker


class TestMovingAverage:
    def test_empty_returns_empty(self):
        assert moving_average([]) == []

    def test_single_point_smoothed_equals_raw(self):
        snap = _snap(0.8, ts=0.0)
        result = moving_average([snap], window=3)
        assert len(result) == 1
        assert result[0].smoothed_ratio == pytest.approx(0.8)
        assert result[0].raw_ratio == pytest.approx(0.8)

    def test_window_of_one_equals_raw(self):
        snaps = [_snap(r, ts=float(i)) for i, r in enumerate([0.5, 0.7, 0.9])]
        result = moving_average(snaps, window=1)
        for pt, snap in zip(result, snaps):
            assert pt.smoothed_ratio == pytest.approx(snap.hit_ratio)

    def test_three_point_window(self):
        snaps = [_snap(r, ts=float(i)) for i, r in enumerate([0.6, 0.8, 1.0])]
        result = moving_average(snaps, window=3)
        assert result[0].smoothed_ratio == pytest.approx(0.6)
        assert result[1].smoothed_ratio == pytest.approx(0.7)
        assert result[2].smoothed_ratio == pytest.approx(0.8)

    def test_timestamps_preserved(self):
        snaps = [_snap(0.5, ts=float(i * 10)) for i in range(4)]
        result = moving_average(snaps, window=2)
        for pt, snap in zip(result, snaps):
            assert pt.timestamp == snap.timestamp

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window must be >= 1"):
            moving_average([], window=0)

    def test_returns_smoothed_point_instances(self):
        snaps = [_snap(0.9, ts=0.0)]
        result = moving_average(snaps, window=1)
        assert isinstance(result[0], SmoothedPoint)


class TestSmoothedPointStr:
    def test_str_contains_ts_and_ratios(self):
        pt = SmoothedPoint(timestamp=10.0, raw_ratio=0.75, smoothed_ratio=0.80)
        s = str(pt)
        assert "10.0" in s
        assert "0.7500" in s
        assert "0.8000" in s

    def test_str_none_values_show_na(self):
        pt = SmoothedPoint(timestamp=5.0, raw_ratio=None, smoothed_ratio=None)
        s = str(pt)
        assert "N/A" in s


class TestSmoothTracker:
    def test_empty_tracker_returns_empty(self):
        tracker = StatsTracker()
        result = smooth_tracker(tracker, window=3)
        assert result == []

    def test_smooth_tracker_uses_history(self):
        tracker = _tracker([0.6, 0.8, 1.0])
        result = smooth_tracker(tracker, window=3)
        assert len(result) == 3
        assert result[2].smoothed_ratio == pytest.approx(0.8)
