"""Tests for cachewatch.pulse."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cachewatch.pulse import PulseResult, detect_pulses
from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker


def _snap(ts: float, hits: int, misses: int) -> CacheStats:
    snap = MagicMock(spec=CacheStats)
    snap.timestamp = ts
    snap.hits = hits
    snap.misses = misses
    snap.total = hits + misses
    snap.hit_ratio = hits / (hits + misses) if (hits + misses) > 0 else None
    return snap


def _tracker(*snaps) -> StatsTracker:
    tracker = MagicMock(spec=StatsTracker)
    tracker.history.return_value = list(snaps)
    return tracker


class TestDetectPulses:
    def test_empty_tracker_returns_empty(self):
        tracker = _tracker()
        assert detect_pulses(tracker) == []

    def test_single_snapshot_returns_empty(self):
        tracker = _tracker(_snap(1.0, 100, 10))
        assert detect_pulses(tracker) == []

    def test_uniform_traffic_returns_empty(self):
        snaps = [_snap(float(i), 100, 10) for i in range(10)]
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=2.0)
        assert result == []

    def test_detects_spike_above_threshold(self):
        # 9 normal snapshots + 1 spike
        snaps = [_snap(float(i), 100, 10) for i in range(9)]
        snaps.append(_snap(9.0, 10000, 1000))
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=2.0)
        assert len(result) == 1
        assert result[0].total_requests == 11000

    def test_pulse_result_has_correct_timestamp(self):
        snaps = [_snap(float(i), 100, 10) for i in range(9)]
        snaps.append(_snap(99.0, 10000, 1000))
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=2.0)
        assert result[0].timestamp == pytest.approx(99.0)

    def test_pulse_result_has_positive_z_score(self):
        snaps = [_snap(float(i), 100, 10) for i in range(9)]
        snaps.append(_snap(9.0, 10000, 1000))
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=2.0)
        assert result[0].z_score > 2.0

    def test_high_threshold_filters_out_pulses(self):
        snaps = [_snap(float(i), 100, 10) for i in range(9)]
        snaps.append(_snap(9.0, 10000, 1000))
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=100.0)
        assert result == []

    def test_multiple_pulses_detected(self):
        snaps = [_snap(float(i), 50, 5) for i in range(8)]
        snaps.append(_snap(8.0, 5000, 500))
        snaps.append(_snap(9.0, 6000, 600))
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=1.5)
        assert len(result) == 2

    def test_pulse_hit_ratio_matches_snapshot(self):
        snaps = [_snap(float(i), 100, 10) for i in range(9)]
        spike = _snap(9.0, 800, 200)
        snaps.append(spike)
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker, threshold_z=2.0)
        assert len(result) == 1
        assert result[0].hit_ratio == pytest.approx(0.8)

    def test_returns_list_of_pulse_result_instances(self):
        snaps = [_snap(float(i), 100, 10) for i in range(9)]
        snaps.append(_snap(9.0, 10000, 1000))
        tracker = _tracker(*snaps)
        result = detect_pulses(tracker)
        assert all(isinstance(r, PulseResult) for r in result)
