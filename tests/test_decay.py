"""Tests for cachewatch.decay."""
from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.decay import DecayResult, compute_decay, _half_life


def _snap(ts: float, hits: int, misses: int) -> "StatsSnapshot":  # type: ignore[name-defined]
    from cachewatch.stats_tracker import StatsSnapshot  # local import
    stats = CacheStats(hits=hits, misses=misses)
    return StatsSnapshot(stats=stats, timestamp=ts)


def _tracker(snaps) -> StatsTracker:
    t = StatsTracker()
    for s in snaps:
        t._history.append(s)  # type: ignore[attr-defined]
    return t


# ---------------------------------------------------------------------------
# _half_life helper
# ---------------------------------------------------------------------------

class TestHalfLife:
    def test_returns_none_when_rate_zero(self):
        assert _half_life(0.8, 0.0) is None

    def test_returns_none_when_rate_positive(self):
        assert _half_life(0.8, 0.001) is None

    def test_returns_none_when_initial_zero(self):
        assert _half_life(0.0, -0.01) is None

    def test_correct_half_life(self):
        # initial=0.8, rate=-0.04/s => half-life = 0.8/(2*0.04) = 10s
        result = _half_life(0.8, -0.04)
        assert result == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# compute_decay
# ---------------------------------------------------------------------------

class TestComputeDecay:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert compute_decay(t) is None

    def test_returns_none_with_single_snapshot(self):
        t = _tracker([_snap(0.0, 80, 20)])
        assert compute_decay(t) is None

    def test_returns_decay_result(self):
        snaps = [_snap(0.0, 80, 20), _snap(10.0, 60, 40)]
        result = compute_decay(_tracker(snaps))
        assert isinstance(result, DecayResult)

    def test_initial_and_final_ratios(self):
        snaps = [_snap(0.0, 80, 20), _snap(10.0, 60, 40)]
        result = compute_decay(_tracker(snaps))
        assert result.initial_ratio == pytest.approx(0.8)
        assert result.final_ratio == pytest.approx(0.6)

    def test_decay_rate_negative_when_degrading(self):
        snaps = [_snap(0.0, 80, 20), _snap(10.0, 60, 40)]
        result = compute_decay(_tracker(snaps))
        # (0.6 - 0.8) / 10 = -0.02
        assert result.decay_rate == pytest.approx(-0.02)

    def test_decay_rate_positive_when_improving(self):
        snaps = [_snap(0.0, 60, 40), _snap(10.0, 80, 20)]
        result = compute_decay(_tracker(snaps))
        assert result.decay_rate == pytest.approx(0.02)

    def test_half_life_present_when_degrading(self):
        snaps = [_snap(0.0, 80, 20), _snap(10.0, 60, 40)]
        result = compute_decay(_tracker(snaps))
        assert result.half_life_seconds is not None
        assert result.half_life_seconds == pytest.approx(20.0)

    def test_half_life_none_when_stable(self):
        snaps = [_snap(0.0, 80, 20), _snap(10.0, 80, 20)]
        result = compute_decay(_tracker(snaps))
        assert result.half_life_seconds is None

    def test_snapshot_count(self):
        snaps = [_snap(float(i), 80, 20) for i in range(5)]
        result = compute_decay(_tracker(snaps))
        assert result.snapshot_count == 5

    def test_str_contains_rate(self):
        snaps = [_snap(0.0, 80, 20), _snap(10.0, 60, 40)]
        result = compute_decay(_tracker(snaps))
        assert "rate=" in str(result)
        assert "half_life=" in str(result)
