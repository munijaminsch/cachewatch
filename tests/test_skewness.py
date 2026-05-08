"""Tests for cachewatch.skewness."""
from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.skewness import SkewnessResult, compute_skewness


def _snap(hits: int, misses: int, ts: float | None = None) -> CacheStats:
    return CacheStats(hits=hits, misses=misses, timestamp=ts or time.time())


def _tracker(records: List[CacheStats]) -> StatsTracker:
    t = StatsTracker()
    for r in records:
        t.record(r)
    return t


# ---------------------------------------------------------------------------
# SkewnessResult.__str__
# ---------------------------------------------------------------------------

class TestSkewnessResultStr:
    def test_str_insufficient_data(self):
        result = SkewnessResult(skewness=None, sample_count=2, mean=0.5, std_dev=None)
        s = str(result)
        assert "N/A" in s
        assert "n=2" in s

    def test_str_right_skew(self):
        result = SkewnessResult(skewness=1.2, sample_count=10, mean=0.6, std_dev=0.1)
        s = str(result)
        assert "right" in s
        assert "1.2000" in s

    def test_str_left_skew(self):
        result = SkewnessResult(skewness=-0.8, sample_count=10, mean=0.7, std_dev=0.05)
        s = str(result)
        assert "left" in s

    def test_str_symmetric(self):
        result = SkewnessResult(skewness=0.0, sample_count=10, mean=0.5, std_dev=0.1)
        s = str(result)
        assert "symmetric" in s


# ---------------------------------------------------------------------------
# compute_skewness
# ---------------------------------------------------------------------------

class TestComputeSkewness:
    def test_returns_none_when_empty(self):
        t = _tracker([])
        assert compute_skewness(t) is None

    def test_returns_result_with_single_snapshot(self):
        t = _tracker([_snap(80, 20)])
        result = compute_skewness(t)
        assert result is not None
        assert result.sample_count == 1
        assert result.skewness is None

    def test_returns_result_with_two_snapshots(self):
        t = _tracker([_snap(80, 20), _snap(60, 40)])
        result = compute_skewness(t)
        assert result is not None
        assert result.sample_count == 2
        assert result.skewness is None

    def test_zero_skewness_for_symmetric_distribution(self):
        # Symmetric values around 0.5: 0.3, 0.5, 0.7
        snaps = [
            _snap(30, 70),
            _snap(50, 50),
            _snap(70, 30),
        ]
        result = compute_skewness(_tracker(snaps))
        assert result is not None
        assert result.skewness is not None
        assert abs(result.skewness) < 1e-9

    def test_positive_skew_for_right_tailed_data(self):
        # Most values low, one high outlier -> right skew
        snaps = [
            _snap(10, 90),
            _snap(15, 85),
            _snap(12, 88),
            _snap(90, 10),
        ]
        result = compute_skewness(_tracker(snaps))
        assert result is not None
        assert result.skewness is not None
        assert result.skewness > 0

    def test_constant_ratios_give_zero_skewness(self):
        snaps = [_snap(50, 50) for _ in range(5)]
        result = compute_skewness(_tracker(snaps))
        assert result is not None
        assert result.skewness == 0.0
        assert result.std_dev == 0.0

    def test_sample_count_matches_history_length(self):
        snaps = [_snap(i * 10, 100 - i * 10) for i in range(1, 6)]
        result = compute_skewness(_tracker(snaps))
        assert result is not None
        assert result.sample_count == 5

    def test_mean_is_correct(self):
        snaps = [
            _snap(20, 80),  # ratio 0.2
            _snap(40, 60),  # ratio 0.4
            _snap(60, 40),  # ratio 0.6
        ]
        result = compute_skewness(_tracker(snaps))
        assert result is not None
        assert result.mean == pytest.approx(0.4, abs=1e-9)
