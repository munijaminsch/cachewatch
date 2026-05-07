"""Tests for cachewatch.entropy."""
from __future__ import annotations

import math
from unittest.mock import MagicMock

import pytest

from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats
from cachewatch.entropy import compute_entropy, EntropyResult, _shannon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(hits: int, misses: int, ts: float = 0.0):
    snap = MagicMock()
    snap.hits = hits
    snap.misses = misses
    total = hits + misses
    snap.hit_ratio = hits / total if total else 0.0
    snap.timestamp = ts
    return snap


def _tracker(*snaps):
    t = MagicMock(spec=StatsTracker)
    t.history.return_value = list(snaps)
    return t


# ---------------------------------------------------------------------------
# _shannon
# ---------------------------------------------------------------------------

class TestShannon:
    def test_all_zero_counts_returns_zero(self):
        assert _shannon([0, 0, 0]) == 0.0

    def test_uniform_distribution(self):
        counts = [1, 1, 1, 1]  # 4 equal buckets
        expected = math.log(4)
        assert abs(_shannon(counts) - expected) < 1e-9

    def test_single_bucket_occupied(self):
        # All mass in one bucket => entropy = 0
        assert _shannon([0, 0, 10, 0]) == 0.0


# ---------------------------------------------------------------------------
# compute_entropy
# ---------------------------------------------------------------------------

class TestComputeEntropy:
    def test_returns_none_when_empty(self):
        t = _tracker()
        assert compute_entropy(t) is None

    def test_returns_entropy_result(self):
        t = _tracker(_snap(8, 2), _snap(6, 4), _snap(9, 1))
        result = compute_entropy(t)
        assert isinstance(result, EntropyResult)

    def test_sample_size_matches_snapshot_count(self):
        snaps = [_snap(5, 5, float(i)) for i in range(7)]
        t = _tracker(*snaps)
        result = compute_entropy(t)
        assert result.sample_size == 7

    def test_bucket_counts_sum_to_sample_size(self):
        snaps = [_snap(i, 10 - i, float(i)) for i in range(11)]
        t = _tracker(*snaps)
        result = compute_entropy(t)
        assert sum(result.bucket_counts) == result.sample_size

    def test_normalized_between_zero_and_one(self):
        snaps = [_snap(i % 10, 10 - (i % 10), float(i)) for i in range(30)]
        t = _tracker(*snaps)
        result = compute_entropy(t)
        assert 0.0 <= result.normalized <= 1.0

    def test_all_same_ratio_gives_low_entropy(self):
        # All hits=9, misses=1 => ratio=0.9 => single bucket => entropy=0
        snaps = [_snap(9, 1, float(i)) for i in range(10)]
        t = _tracker(*snaps)
        result = compute_entropy(t)
        assert result.entropy == pytest.approx(0.0, abs=1e-9)
        assert result.normalized == pytest.approx(0.0, abs=1e-9)

    def test_custom_bucket_count(self):
        snaps = [_snap(i, 20 - i, float(i)) for i in range(21)]
        t = _tracker(*snaps)
        result = compute_entropy(t, buckets=5)
        assert len(result.bucket_counts) == 5

    def test_str_contains_entropy_and_n(self):
        t = _tracker(_snap(7, 3), _snap(5, 5))
        result = compute_entropy(t)
        s = str(result)
        assert "entropy=" in s
        assert "n=2" in s
