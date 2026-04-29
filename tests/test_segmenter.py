"""Tests for cachewatch.segmenter."""
import time
from typing import List

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.segmenter import Segment, segment_by_count, segment_by_duration


def _snap(hits: int, misses: int, ts: float | None = None) -> None:
    pass  # helper used via _tracker


def _tracker(entries: List[tuple]) -> StatsTracker:
    """Build a StatsTracker from (hits, misses, timestamp) tuples."""
    t = StatsTracker()
    base = 1_000_000.0
    for i, (hits, misses) in enumerate(entries):
        stats = CacheStats(hits=hits, misses=misses)
        t.record(stats, timestamp=base + i)
    return t


class TestSegment:
    def test_str_contains_label(self):
        seg = Segment(label="alpha")
        assert "alpha" in str(seg)

    def test_average_hit_ratio_none_when_empty(self):
        seg = Segment(label="x")
        assert seg.average_hit_ratio is None

    def test_count_reflects_snapshots(self):
        t = _tracker([(10, 5), (20, 10)])
        snaps = t.history()
        seg = Segment(label="test", snapshots=list(snaps))
        assert seg.count == 2

    def test_start_end_ts(self):
        t = _tracker([(10, 0), (20, 0), (30, 0)])
        snaps = t.history()
        seg = Segment(label="t", snapshots=list(snaps))
        assert seg.start_ts == snaps[0].timestamp
        assert seg.end_ts == snaps[-1].timestamp


class TestSegmentByCount:
    def test_empty_tracker_returns_empty(self):
        t = StatsTracker()
        result = segment_by_count(t, segment_size=3)
        assert result == []

    def test_single_segment_when_fewer_than_size(self):
        t = _tracker([(10, 2), (8, 1)])
        result = segment_by_count(t, segment_size=5)
        assert len(result) == 1
        assert result[0].count == 2

    def test_multiple_segments(self):
        t = _tracker([(i, 1) for i in range(7)])
        result = segment_by_count(t, segment_size=3)
        assert len(result) == 3  # 3, 3, 1
        assert result[0].count == 3
        assert result[2].count == 1

    def test_custom_labels_applied(self):
        t = _tracker([(10, 0), (20, 0)])
        result = segment_by_count(t, segment_size=1, labels=["first", "second"])
        assert result[0].label == "first"
        assert result[1].label == "second"

    def test_invalid_size_raises(self):
        t = StatsTracker()
        with pytest.raises(ValueError):
            segment_by_count(t, segment_size=0)


class TestSegmentByDuration:
    def test_empty_tracker_returns_empty(self):
        t = StatsTracker()
        result = segment_by_duration(t, window_seconds=10)
        assert result == []

    def test_all_in_one_window(self):
        t = _tracker([(5, 1), (6, 1), (7, 1)])  # timestamps 0,1,2 relative
        result = segment_by_duration(t, window_seconds=10)
        assert len(result) == 1
        assert result[0].count == 3

    def test_splits_into_two_windows(self):
        # Build tracker manually with wider gaps
        tracker = StatsTracker()
        base = 0.0
        for i in range(4):
            stats = CacheStats(hits=10, misses=2)
            tracker.record(stats, timestamp=base + i * 5)  # 0,5,10,15
        result = segment_by_duration(tracker, window_seconds=10)
        assert len(result) == 2

    def test_invalid_window_raises(self):
        t = StatsTracker()
        with pytest.raises(ValueError):
            segment_by_duration(t, window_seconds=0)
