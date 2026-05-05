"""Tests for cachewatch.plateau."""

from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.plateau import PlateauResult, detect_plateaus


def _snap(ts: float, hits: int, misses: int) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts)


def _tracker(snapshots: list) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


class TestPlateauResult:
    def test_str_contains_avg_and_deviation(self):
        p = PlateauResult(
            start_ts=0.0,
            end_ts=10.0,
            average_hit_ratio=0.9,
            snapshot_count=5,
            max_deviation=0.005,
        )
        s = str(p)
        assert "90.00%" in s
        assert "0.0050" in s

    def test_duration(self):
        p = PlateauResult(
            start_ts=100.0,
            end_ts=150.0,
            average_hit_ratio=0.8,
            snapshot_count=4,
            max_deviation=0.01,
        )
        assert p.duration() == pytest.approx(50.0)


class TestDetectPlateaus:
    def test_empty_tracker_returns_empty(self):
        t = StatsTracker()
        assert detect_plateaus(t) == []

    def test_too_few_snapshots_returns_empty(self):
        snaps = [_snap(float(i), 9, 1) for i in range(2)]
        t = _tracker(snaps)
        result = detect_plateaus(t, min_snapshots=3)
        assert result == []

    def test_stable_window_detected(self):
        # All hits=90, misses=10 -> ratio=0.9 exactly
        snaps = [_snap(float(i), 90, 10) for i in range(5)]
        t = _tracker(snaps)
        result = detect_plateaus(t, min_snapshots=3, max_deviation=0.01)
        assert len(result) == 1
        assert result[0].snapshot_count == 5
        assert result[0].average_hit_ratio == pytest.approx(0.9)

    def test_unstable_window_not_detected(self):
        # Alternating high/low ratios
        snaps = [
            _snap(0.0, 90, 10),  # 0.9
            _snap(1.0, 10, 90),  # 0.1
            _snap(2.0, 90, 10),  # 0.9
            _snap(3.0, 10, 90),  # 0.1
            _snap(4.0, 90, 10),  # 0.9
        ]
        t = _tracker(snaps)
        result = detect_plateaus(t, min_snapshots=3, max_deviation=0.02)
        assert result == []

    def test_multiple_plateaus_detected(self):
        stable_a = [_snap(float(i), 80, 20) for i in range(4)]
        unstable = [_snap(float(i + 4), 50 + i * 10, 50 - i * 10) for i in range(3)]
        stable_b = [_snap(float(i + 7), 95, 5) for i in range(4)]
        t = _tracker(stable_a + unstable + stable_b)
        result = detect_plateaus(t, min_snapshots=3, max_deviation=0.02)
        assert len(result) >= 2

    def test_result_fields_populated(self):
        snaps = [_snap(float(i * 10), 70, 30) for i in range(4)]
        t = _tracker(snaps)
        result = detect_plateaus(t, min_snapshots=3, max_deviation=0.01)
        assert len(result) == 1
        p = result[0]
        assert p.start_ts == pytest.approx(0.0)
        assert p.end_ts == pytest.approx(30.0)
        assert p.snapshot_count == 4
        assert p.max_deviation == pytest.approx(0.0)
