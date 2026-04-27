"""Tests for cachewatch.aggregator module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cachewatch.aggregator import aggregate_by_seconds, BucketSummary
from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker


def _snap(ts_epoch: float, hits: int, misses: int):
    snap = MagicMock()
    snap.timestamp = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
    snap.stats = CacheStats(hits=hits, misses=misses)
    return snap


def _tracker(snaps):
    t = MagicMock(spec=StatsTracker)
    t.history.return_value = snaps
    return t


class TestAggregatBySeconds:
    def test_empty_tracker_returns_empty(self):
        result = aggregate_by_seconds(_tracker([]))
        assert result == []

    def test_single_snapshot_one_bucket(self):
        snaps = [_snap(0.0, hits=80, misses=20)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert len(result) == 1
        assert result[0].sample_count == 1

    def test_bucket_hit_ratio_correct(self):
        snaps = [_snap(0.0, hits=80, misses=20)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert result[0].avg_hit_ratio == pytest.approx(0.8)
        assert result[0].min_hit_ratio == pytest.approx(0.8)
        assert result[0].max_hit_ratio == pytest.approx(0.8)

    def test_two_snapshots_same_bucket(self):
        snaps = [_snap(0.0, hits=60, misses=40), _snap(30.0, hits=80, misses=20)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert len(result) == 1
        assert result[0].sample_count == 2
        assert result[0].avg_hit_ratio == pytest.approx(0.7)

    def test_two_snapshots_different_buckets(self):
        snaps = [_snap(0.0, hits=60, misses=40), _snap(120.0, hits=90, misses=10)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert len(result) == 2

    def test_buckets_ordered_by_time(self):
        snaps = [_snap(120.0, hits=90, misses=10), _snap(0.0, hits=60, misses=40)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert result[0].bucket_start < result[1].bucket_start

    def test_total_hits_and_misses_summed(self):
        snaps = [_snap(0.0, hits=60, misses=40), _snap(30.0, hits=80, misses=20)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert result[0].total_hits == 140
        assert result[0].total_misses == 60

    def test_str_contains_avg(self):
        snaps = [_snap(0.0, hits=75, misses=25)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        s = str(result[0])
        assert "75.00%" in s
        assert "samples=1" in s

    def test_zero_hits_zero_ratio(self):
        snaps = [_snap(0.0, hits=0, misses=100)]
        result = aggregate_by_seconds(_tracker(snaps), bucket_size=60)
        assert result[0].avg_hit_ratio == pytest.approx(0.0)
