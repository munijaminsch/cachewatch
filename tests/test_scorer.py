"""Tests for cachewatch.scorer."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.scorer import HealthScore, _grade, compute_health_score


def _snap(hits: int, misses: int, ts: float) -> CacheStats:
    return CacheStats(
        hits=hits,
        misses=misses,
        timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
    )


def _tracker(*snapshots: CacheStats) -> StatsTracker:
    t = StatsTracker()
    for s in snapshots:
        t.record(s)
    return t


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

class TestGrade:
    def test_a(self):
        assert _grade(95) == "A"

    def test_b(self):
        assert _grade(80) == "B"

    def test_c(self):
        assert _grade(65) == "C"

    def test_d(self):
        assert _grade(50) == "D"

    def test_f(self):
        assert _grade(30) == "F"

    def test_boundary_a(self):
        assert _grade(90) == "A"

    def test_boundary_b(self):
        assert _grade(75) == "B"


# ---------------------------------------------------------------------------
# compute_health_score
# ---------------------------------------------------------------------------

class TestComputeHealthScore:
    def test_returns_none_when_empty(self):
        t = StatsTracker()
        assert compute_health_score(t) is None

    def test_returns_health_score_instance(self):
        t = _tracker(
            _snap(80, 20, 0.0),
            _snap(85, 15, 1.0),
            _snap(90, 10, 2.0),
        )
        result = compute_health_score(t)
        assert isinstance(result, HealthScore)

    def test_score_between_0_and_100(self):
        t = _tracker(
            _snap(50, 50, 0.0),
            _snap(60, 40, 1.0),
            _snap(70, 30, 2.0),
        )
        result = compute_health_score(t)
        assert 0.0 <= result.score <= 100.0

    def test_high_hit_ratio_gives_high_score(self):
        t = _tracker(
            _snap(950, 50, 0.0),
            _snap(960, 40, 1.0),
            _snap(970, 30, 2.0),
        )
        result = compute_health_score(t)
        assert result.score >= 80.0

    def test_low_hit_ratio_gives_low_score(self):
        t = _tracker(
            _snap(10, 90, 0.0),
            _snap(15, 85, 1.0),
            _snap(20, 80, 2.0),
        )
        result = compute_health_score(t)
        assert result.score < 40.0

    def test_grade_consistent_with_score(self):
        t = _tracker(
            _snap(900, 100, 0.0),
            _snap(910, 90, 1.0),
        )
        result = compute_health_score(t)
        assert result.grade == _grade(result.score)

    def test_str_contains_grade(self):
        t = _tracker(
            _snap(80, 20, 0.0),
            _snap(85, 15, 1.0),
        )
        result = compute_health_score(t)
        assert result.grade in str(result)

    def test_avg_hit_ratio_stored(self):
        t = _tracker(
            _snap(80, 20, 0.0),
            _snap(80, 20, 1.0),
        )
        result = compute_health_score(t)
        assert abs(result.avg_hit_ratio - 0.8) < 1e-6
