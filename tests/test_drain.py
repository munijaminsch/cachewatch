"""Tests for cachewatch.drain."""

from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.drain import DrainResult, detect_drains


def _snap(ts: float, hits: int, misses: int) -> CacheStats:
    return CacheStats(timestamp=ts, hits=hits, misses=misses)


def _tracker(snaps) -> StatsTracker:
    t = StatsTracker()
    for s in snaps:
        t.record(s)
    return t


class TestDrainResult:
    def test_str_contains_drop_and_steps(self):
        d = DrainResult(start_ts=0.0, end_ts=5.0, start_ratio=0.9, end_ratio=0.7, steps=5)
        s = str(d)
        assert "drop=" in s
        assert "steps=5" in s

    def test_duration(self):
        d = DrainResult(start_ts=10.0, end_ts=25.0, start_ratio=0.8, end_ratio=0.5, steps=3)
        assert d.duration == pytest.approx(15.0)

    def test_total_drop(self):
        d = DrainResult(start_ts=0.0, end_ts=3.0, start_ratio=0.9, end_ratio=0.6, steps=3)
        assert d.total_drop == pytest.approx(0.3)


class TestDetectDrains:
    def test_empty_tracker_returns_empty(self):
        t = _tracker([])
        assert detect_drains(t) == []

    def test_single_snapshot_returns_empty(self):
        t = _tracker([_snap(0.0, 80, 20)])
        assert detect_drains(t) == []

    def test_no_drain_when_ratio_flat(self):
        snaps = [_snap(float(i), 80, 20) for i in range(6)]
        t = _tracker(snaps)
        assert detect_drains(t, min_steps=3, min_drop=0.05) == []

    def test_no_drain_when_ratio_rising(self):
        # hits increase each step
        snaps = [_snap(float(i), 70 + i * 5, 30) for i in range(6)]
        t = _tracker(snaps)
        assert detect_drains(t, min_steps=3, min_drop=0.05) == []

    def test_detects_drain_at_end(self):
        # First two stable, then 4 declining steps
        snaps = [
            _snap(0.0, 90, 10),
            _snap(1.0, 90, 10),
            _snap(2.0, 85, 15),
            _snap(3.0, 75, 25),
            _snap(4.0, 65, 35),
            _snap(5.0, 50, 50),
        ]
        t = _tracker(snaps)
        results = detect_drains(t, min_steps=3, min_drop=0.05)
        assert len(results) == 1
        r = results[0]
        assert r.steps == 4
        assert r.start_ratio == pytest.approx(0.85)
        assert r.end_ratio == pytest.approx(0.50)
        assert r.total_drop == pytest.approx(0.35)

    def test_drain_not_reported_below_min_steps(self):
        snaps = [
            _snap(0.0, 90, 10),
            _snap(1.0, 80, 20),
            _snap(2.0, 70, 30),
            _snap(3.0, 90, 10),
        ]
        t = _tracker(snaps)
        # only 2 declining steps, min_steps=3 → no drain
        results = detect_drains(t, min_steps=3, min_drop=0.05)
        assert results == []

    def test_drain_not_reported_below_min_drop(self):
        snaps = [
            _snap(0.0, 99, 1),
            _snap(1.0, 98, 2),
            _snap(2.0, 97, 3),
            _snap(3.0, 96, 4),
        ]
        t = _tracker(snaps)
        # drop is tiny, below default min_drop=0.05
        results = detect_drains(t, min_steps=3, min_drop=0.05)
        assert results == []

    def test_multiple_drains_detected(self):
        snaps = [
            _snap(0.0, 90, 10),
            _snap(1.0, 80, 20),
            _snap(2.0, 70, 30),
            _snap(3.0, 60, 40),  # end of first drain
            _snap(4.0, 95, 5),   # recovery
            _snap(5.0, 85, 15),
            _snap(6.0, 75, 25),
            _snap(7.0, 55, 45),  # end of second drain
        ]
        t = _tracker(snaps)
        results = detect_drains(t, min_steps=3, min_drop=0.05)
        assert len(results) == 2
