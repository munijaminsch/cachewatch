"""Tests for cachewatch.percentile."""
from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.percentile import PercentileResult, compute_percentiles, _percentile


def _snap(hits: int, misses: int, ts: float | None = None) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts or time.time())


def _tracker(records: List[CacheStats]) -> StatsTracker:
    t = StatsTracker()
    for r in records:
        t.record(r)
    return t


# ---------------------------------------------------------------------------
# _percentile helper
# ---------------------------------------------------------------------------

class TestPercentileHelper:
    def test_empty_returns_none(self):
        assert _percentile([], 50) is None

    def test_single_value(self):
        assert _percentile([0.8], 99) == pytest.approx(0.8)

    def test_median_two_values(self):
        result = _percentile([0.0, 1.0], 50)
        assert result == pytest.approx(0.5)

    def test_p100_returns_max(self):
        values = [0.1, 0.5, 0.9]
        assert _percentile(values, 100) == pytest.approx(0.9)

    def test_p0_returns_min(self):
        values = [0.1, 0.5, 0.9]
        assert _percentile(values, 0) == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# compute_percentiles
# ---------------------------------------------------------------------------

class TestComputePercentiles:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert compute_percentiles(t) is None

    def test_returns_percentile_result(self):
        t = _tracker([_snap(90, 10), _snap(80, 20), _snap(70, 30)])
        result = compute_percentiles(t)
        assert isinstance(result, PercentileResult)

    def test_sample_count_matches(self):
        snaps = [_snap(80, 20)] * 5
        t = _tracker(snaps)
        result = compute_percentiles(t)
        assert result.sample_count == 5

    def test_p50_midpoint(self):
        # ratios: 0.1, 0.5, 0.9 -> median = 0.5
        t = _tracker([
            _snap(10, 90),
            _snap(50, 50),
            _snap(90, 10),
        ])
        result = compute_percentiles(t)
        assert result.p50 == pytest.approx(0.5)

    def test_p99_near_max(self):
        # With many equal-ratio snapshots p99 should equal that ratio
        t = _tracker([_snap(80, 20)] * 10)
        result = compute_percentiles(t)
        assert result.p99 == pytest.approx(0.8)

    def test_str_contains_percentile_labels(self):
        t = _tracker([_snap(75, 25), _snap(85, 15)])
        result = compute_percentiles(t)
        s = str(result)
        assert "p50" in s
        assert "p90" in s
        assert "p95" in s
        assert "p99" in s

    def test_all_zero_hits(self):
        t = _tracker([_snap(0, 100)] * 3)
        result = compute_percentiles(t)
        assert result.p50 == pytest.approx(0.0)
