"""Tests for cachewatch.snapshot_filter."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.snapshot_filter import (
    average_hit_ratio,
    filter_by_time_range,
    filter_last_n_seconds,
    peak_hit_ratio,
    trough_hit_ratio,
)


def _snap(hits: int, misses: int, seconds_ago: float = 0.0) -> CacheStats:
    ts = datetime.utcnow() - timedelta(seconds=seconds_ago)
    snap = MagicMock(spec=CacheStats)
    snap.hits = hits
    snap.misses = misses
    snap.timestamp = ts
    total = hits + misses
    snap.hit_ratio = hits / total if total else 0.0
    return snap


def _tracker(*snaps):
    tracker = MagicMock()
    tracker.history.return_value = list(snaps)
    return tracker


class TestFilterByTimeRange:
    def test_returns_all_within_range(self):
        now = datetime.utcnow()
        s1 = _snap(10, 2, seconds_ago=5)
        s2 = _snap(8, 4, seconds_ago=2)
        s3 = _snap(6, 6, seconds_ago=0)
        tracker = _tracker(s1, s2, s3)
        result = filter_by_time_range(tracker, start=now - timedelta(seconds=10))
        assert len(result) == 3

    def test_excludes_outside_range(self):
        now = datetime.utcnow()
        old = _snap(10, 0, seconds_ago=60)
        recent = _snap(5, 5, seconds_ago=1)
        tracker = _tracker(old, recent)
        result = filter_by_time_range(tracker, start=now - timedelta(seconds=10))
        assert old not in result
        assert recent in result

    def test_empty_history(self):
        tracker = _tracker()
        result = filter_by_time_range(tracker, start=datetime.utcnow())
        assert result == []


class TestFilterLastNSeconds:
    def test_filters_correctly(self):
        s_old = _snap(10, 0, seconds_ago=30)
        s_new = _snap(5, 5, seconds_ago=2)
        tracker = _tracker(s_old, s_new)
        result = filter_last_n_seconds(tracker, seconds=10)
        assert s_new in result
        assert s_old not in result


class TestAggregates:
    def test_average_hit_ratio(self):
        snaps = [_snap(8, 2), _snap(6, 4)]
        assert average_hit_ratio(snaps) == pytest.approx(0.7)

    def test_average_empty(self):
        assert average_hit_ratio([]) is None

    def test_peak_hit_ratio(self):
        snaps = [_snap(8, 2), _snap(5, 5), _snap(9, 1)]
        assert peak_hit_ratio(snaps) == pytest.approx(0.9)

    def test_trough_hit_ratio(self):
        snaps = [_snap(8, 2), _snap(5, 5), _snap(9, 1)]
        assert trough_hit_ratio(snaps) == pytest.approx(0.5)

    def test_peak_empty(self):
        assert peak_hit_ratio([]) is None

    def test_trough_empty(self):
        assert trough_hit_ratio([]) is None
