"""Tests for cachewatch.baseline."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from cachewatch.baseline import BaselineResult, compare_to_baseline
from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


def _snap(hits: int, misses: int, ts: float | None = None) -> MagicMock:
    snap = MagicMock()
    snap.stats = CacheStats(hits=hits, misses=misses)
    snap.timestamp = ts or time.time()
    return snap


def _tracker(*snaps) -> StatsTracker:
    t = StatsTracker(max_history=100)
    for s in snaps:
        t._history.append(s)  # type: ignore[attr-defined]
    return t


class TestBaselineResult:
    def test_str_contains_baseline_and_current(self):
        r = BaselineResult(baseline_ratio=0.8, current_ratio=0.75, delta=-0.05, verdict="below")
        s = str(r)
        assert "0.800" in s
        assert "0.750" in s
        assert "below" in s

    def test_str_positive_delta_has_plus_sign(self):
        r = BaselineResult(baseline_ratio=0.7, current_ratio=0.8, delta=0.1, verdict="above")
        assert "+" in str(r)

    def test_str_unknown_when_none(self):
        r = BaselineResult(baseline_ratio=None, current_ratio=None, delta=None, verdict="unknown")
        assert "unknown" in str(r)


class TestCompareToBaseline:
    def test_returns_unknown_when_both_empty(self):
        result = compare_to_baseline(_tracker(), _tracker())
        assert result.verdict == "unknown"
        assert result.delta is None

    def test_returns_unknown_when_baseline_empty(self):
        current = _tracker(_snap(80, 20))
        result = compare_to_baseline(current, _tracker())
        assert result.verdict == "unknown"

    def test_returns_unknown_when_current_empty(self):
        baseline = _tracker(_snap(80, 20))
        result = compare_to_baseline(_tracker(), baseline)
        assert result.verdict == "unknown"

    def test_above_when_current_higher(self):
        baseline = _tracker(_snap(60, 40))  # ratio 0.6
        current = _tracker(_snap(90, 10))   # ratio 0.9
        result = compare_to_baseline(current, baseline, tolerance=0.02)
        assert result.verdict == "above"
        assert result.delta is not None
        assert result.delta > 0

    def test_below_when_current_lower(self):
        baseline = _tracker(_snap(90, 10))  # ratio 0.9
        current = _tracker(_snap(60, 40))   # ratio 0.6
        result = compare_to_baseline(current, baseline, tolerance=0.02)
        assert result.verdict == "below"
        assert result.delta is not None
        assert result.delta < 0

    def test_on_par_within_tolerance(self):
        baseline = _tracker(_snap(80, 20))  # ratio 0.8
        current = _tracker(_snap(81, 19))   # ratio ~0.81
        result = compare_to_baseline(current, baseline, tolerance=0.05)
        assert result.verdict == "on_par"

    def test_delta_is_current_minus_baseline(self):
        baseline = _tracker(_snap(70, 30))  # 0.7
        current = _tracker(_snap(80, 20))   # 0.8
        result = compare_to_baseline(current, baseline)
        assert result.delta == pytest.approx(0.1, abs=1e-6)
