"""Tests for cachewatch.ranker."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.ranker import RankEntry, rank_trackers


def _snap(hits: int, misses: int, ts: float = 0.0):
    cs = CacheStats(hits=hits, misses=misses)
    return type(
        "Snapshot",
        (),
        {"stats": cs, "timestamp": ts, "delta": None},
    )()


def _tracker(*ratios_hits_misses):
    """Build a tracker from (hits, misses) pairs."""
    t = StatsTracker()
    for i, (h, m) in enumerate(ratios_hits_misses):
        t.record(_snap(h, m, ts=float(i)))
    return t


class TestRankEntry:
    def test_str_with_ratio(self):
        entry = RankEntry(name="cache-a", tracker=StatsTracker(), avg_hit_ratio=0.85, rank=1)
        s = str(entry)
        assert "#1" in s
        assert "cache-a" in s
        assert "85.00%" in s

    def test_str_none_ratio(self):
        entry = RankEntry(name="cache-b", tracker=StatsTracker(), avg_hit_ratio=None, rank=2)
        s = str(entry)
        assert "N/A" in s
        assert "#2" in s


class TestRankTrackers:
    def test_empty_list_returns_empty(self):
        result = rank_trackers([])
        assert result == []

    def test_single_tracker_rank_one(self):
        t = _tracker((8, 2))
        result = rank_trackers([("only", t)])
        assert len(result) == 1
        assert result[0].rank == 1
        assert result[0].name == "only"

    def test_ranks_descending_by_default(self):
        t_high = _tracker((9, 1))   # 0.90
        t_low = _tracker((5, 5))    # 0.50
        result = rank_trackers([("low", t_low), ("high", t_high)])
        assert result[0].name == "high"
        assert result[1].name == "low"
        assert result[0].rank == 1
        assert result[1].rank == 2

    def test_ranks_ascending_when_flag_set(self):
        t_high = _tracker((9, 1))
        t_low = _tracker((5, 5))
        result = rank_trackers([("high", t_high), ("low", t_low)], ascending=True)
        assert result[0].name == "low"
        assert result[1].name == "high"

    def test_empty_tracker_placed_last(self):
        t_good = _tracker((8, 2))
        t_empty = StatsTracker()
        result = rank_trackers([("empty", t_empty), ("good", t_good)])
        assert result[0].name == "good"
        assert result[1].name == "empty"
        assert result[1].avg_hit_ratio is None

    def test_avg_hit_ratio_correct(self):
        # Two snapshots: 0.8 and 0.6 -> avg 0.7
        t = _tracker((8, 2), (6, 4))
        result = rank_trackers([("t", t)])
        assert result[0].avg_hit_ratio == pytest.approx(0.7, abs=1e-6)
