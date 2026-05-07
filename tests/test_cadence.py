"""Tests for cachewatch.cadence."""
from __future__ import annotations

import time
from typing import Optional

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.cadence import CadenceResult, compute_cadence


def _snap(ts: float, hits: int = 8, misses: int = 2) -> object:
    """Create a minimal snapshot-like object accepted by StatsTracker."""
    from cachewatch.stats_tracker import Snapshot  # type: ignore

    stats = CacheStats(hits=hits, misses=misses)
    return Snapshot(timestamp=ts, stats=stats)


def _tracker(*timestamps: float) -> StatsTracker:
    t = StatsTracker()
    for ts in timestamps:
        snap = _snap(ts)
        t._history.append(snap)  # type: ignore[attr-defined]
    return t


# ---------------------------------------------------------------------------
# CadenceResult.__str__
# ---------------------------------------------------------------------------

class TestCadenceResultStr:
    def test_str_insufficient_data(self):
        r = CadenceResult(
            count=1,
            min_interval=None,
            max_interval=None,
            mean_interval=None,
            std_dev=None,
            is_regular=False,
        )
        assert "insufficient" in str(r)

    def test_str_contains_mean_and_regularity(self):
        r = CadenceResult(
            count=5,
            min_interval=1.0,
            max_interval=3.0,
            mean_interval=2.0,
            std_dev=0.1,
            is_regular=True,
        )
        s = str(r)
        assert "mean=2.00s" in s
        assert "regular" in s

    def test_str_irregular_label(self):
        r = CadenceResult(
            count=4,
            min_interval=1.0,
            max_interval=10.0,
            mean_interval=5.0,
            std_dev=4.0,
            is_regular=False,
        )
        assert "irregular" in str(r)


# ---------------------------------------------------------------------------
# compute_cadence
# ---------------------------------------------------------------------------

class TestComputeCadence:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert compute_cadence(t) is None

    def test_returns_none_with_single_snapshot(self):
        t = _tracker(1000.0)
        assert compute_cadence(t) is None

    def test_returns_result_with_two_snapshots(self):
        t = _tracker(1000.0, 1005.0)
        result = compute_cadence(t)
        assert result is not None
        assert result.count == 2
        assert result.mean_interval == pytest.approx(5.0)
        assert result.min_interval == pytest.approx(5.0)
        assert result.max_interval == pytest.approx(5.0)

    def test_regular_when_uniform_intervals(self):
        # 10 snapshots, 1 s apart — perfectly regular
        t = _tracker(*[float(i) for i in range(10)])
        result = compute_cadence(t)
        assert result is not None
        assert result.is_regular is True
        assert result.std_dev == pytest.approx(0.0)

    def test_irregular_when_intervals_vary_widely(self):
        # intervals: 1, 1, 1, 100 — highly irregular
        t = _tracker(0.0, 1.0, 2.0, 3.0, 103.0)
        result = compute_cadence(t)
        assert result is not None
        assert result.is_regular is False

    def test_count_matches_snapshot_count(self):
        t = _tracker(0.0, 2.0, 4.0, 6.0)
        result = compute_cadence(t)
        assert result is not None
        assert result.count == 4

    def test_min_max_correct(self):
        t = _tracker(0.0, 1.0, 4.0, 6.0)  # intervals: 1, 3, 2
        result = compute_cadence(t)
        assert result is not None
        assert result.min_interval == pytest.approx(1.0)
        assert result.max_interval == pytest.approx(3.0)
