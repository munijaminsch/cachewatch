"""Tests for cachewatch.burst."""

from __future__ import annotations

import time
from typing import Optional

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.burst import BurstResult, detect_bursts


def _snap(hits: int, misses: int, ts: Optional[float] = None) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts or time.time())


def _tracker(*snapshots: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


# ---------------------------------------------------------------------------
# BurstResult
# ---------------------------------------------------------------------------

class TestBurstResult:
    def test_str_contains_direction_and_ratio(self):
        b = BurstResult(timestamp=1000.0, hit_ratio=0.85, delta=0.15, direction="up")
        s = str(b)
        assert "up" in s
        assert "0.8500" in s

    def test_str_down_direction(self):
        b = BurstResult(timestamp=2000.0, hit_ratio=0.40, delta=-0.20, direction="down")
        assert "down" in str(b)

    def test_str_positive_delta_has_plus_sign(self):
        b = BurstResult(timestamp=1.0, hit_ratio=0.9, delta=0.12, direction="up")
        assert "+" in str(b)

    def test_str_negative_delta_no_plus_sign(self):
        b = BurstResult(timestamp=1.0, hit_ratio=0.5, delta=-0.11, direction="down")
        s = str(b)
        assert "+" not in s
        assert "-" in s


# ---------------------------------------------------------------------------
# detect_bursts
# ---------------------------------------------------------------------------

class TestDetectBursts:
    def test_empty_tracker_returns_empty(self):
        t = StatsTracker()
        assert detect_bursts(t) == []

    def test_single_snapshot_returns_empty(self):
        t = _tracker(_snap(100, 10, ts=1.0))
        assert detect_bursts(t) == []

    def test_no_burst_below_threshold(self):
        # delta = 0.05, below default threshold of 0.10
        t = _tracker(
            _snap(50, 50, ts=1.0),   # ratio 0.50
            _snap(55, 45, ts=2.0),   # ratio 0.55  -> delta +0.05
        )
        assert detect_bursts(t, threshold=0.10) == []

    def test_detects_upward_burst(self):
        t = _tracker(
            _snap(50, 50, ts=1.0),   # ratio 0.50
            _snap(90, 10, ts=2.0),   # ratio 0.90  -> delta +0.40
        )
        results = detect_bursts(t, threshold=0.10)
        assert len(results) == 1
        assert results[0].direction == "up"
        assert results[0].delta == pytest.approx(0.40, abs=1e-6)

    def test_detects_downward_burst(self):
        t = _tracker(
            _snap(90, 10, ts=1.0),   # ratio 0.90
            _snap(40, 60, ts=2.0),   # ratio 0.40  -> delta -0.50
        )
        results = detect_bursts(t, threshold=0.10)
        assert len(results) == 1
        assert results[0].direction == "down"

    def test_multiple_bursts_detected(self):
        t = _tracker(
            _snap(50, 50, ts=1.0),   # 0.50
            _snap(90, 10, ts=2.0),   # 0.90  burst up
            _snap(91, 9,  ts=3.0),   # ~0.91 no burst
            _snap(20, 80, ts=4.0),   # 0.20  burst down
        )
        results = detect_bursts(t, threshold=0.10)
        assert len(results) == 2
        assert results[0].direction == "up"
        assert results[1].direction == "down"

    def test_custom_threshold_respected(self):
        t = _tracker(
            _snap(50, 50, ts=1.0),
            _snap(56, 44, ts=2.0),   # delta ~0.06
        )
        assert detect_bursts(t, threshold=0.05) != []
        assert detect_bursts(t, threshold=0.10) == []

    def test_result_timestamp_matches_current_snapshot(self):
        t = _tracker(
            _snap(50, 50, ts=100.0),
            _snap(90, 10, ts=200.0),
        )
        results = detect_bursts(t)
        assert results[0].timestamp == pytest.approx(200.0)
