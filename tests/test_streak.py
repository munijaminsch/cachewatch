"""Tests for cachewatch.streak."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.streak import StreakResult, detect_streak


def _snap(hits: int, misses: int) -> MagicMock:
    snap = MagicMock()
    total = hits + misses
    snap.hit_ratio = hits / total if total else 0.0
    snap.timestamp = time.time()
    return snap


def _tracker(*hit_miss_pairs) -> StatsTracker:
    tracker = StatsTracker()
    for hits, misses in hit_miss_pairs:
        snap = _snap(hits, misses)
        tracker._history.append(snap)  # type: ignore[attr-defined]
    return tracker


class TestDetectStreak:
    def test_returns_none_when_empty(self):
        tracker = StatsTracker()
        assert detect_streak(tracker) is None

    def test_returns_none_with_single_snapshot(self):
        tracker = _tracker((80, 20))
        assert detect_streak(tracker) is None

    def test_improving_streak(self):
        # ratios: 0.5, 0.6, 0.7, 0.8
        tracker = _tracker((50, 50), (60, 40), (70, 30), (80, 20))
        result = detect_streak(tracker)
        assert result is not None
        assert result.kind == "improving"
        assert result.length == 4

    def test_declining_streak(self):
        # ratios: 0.9, 0.8, 0.7
        tracker = _tracker((90, 10), (80, 20), (70, 30))
        result = detect_streak(tracker)
        assert result is not None
        assert result.kind == "declining"
        assert result.length == 3

    def test_neutral_streak_when_all_equal(self):
        # ratios: 0.7, 0.7, 0.7
        tracker = _tracker((70, 30), (70, 30), (70, 30))
        result = detect_streak(tracker)
        assert result is not None
        assert result.kind == "neutral"

    def test_streak_resets_on_direction_change(self):
        # ratios: 0.9, 0.8, 0.7 — declining 3 — then 0.75, 0.8 — improving 2
        tracker = _tracker((90, 10), (80, 20), (70, 30), (75, 25), (80, 20))
        result = detect_streak(tracker)
        assert result is not None
        assert result.kind == "improving"
        assert result.length == 2

    def test_start_and_end_ratio_set_correctly(self):
        tracker = _tracker((60, 40), (70, 30), (80, 20))
        result = detect_streak(tracker)
        assert result is not None
        assert pytest.approx(result.start_ratio, abs=1e-6) == 0.6
        assert pytest.approx(result.end_ratio, abs=1e-6) == 0.8

    def test_streak_result_str_contains_kind(self):
        r = StreakResult(kind="improving", length=3, start_ratio=0.6, end_ratio=0.9)
        s = str(r)
        assert "improving" in s
        assert "3" in s

    def test_streak_result_str_declining_negative_delta(self):
        r = StreakResult(kind="declining", length=2, start_ratio=0.8, end_ratio=0.6)
        s = str(r)
        assert "declining" in s
        assert "-" in s
