"""Tests for cachewatch.gradient."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cachewatch.gradient import GradientPoint, compute_gradient
from cachewatch.stats_tracker import StatsTracker


def _snap(timestamp: float, hit_ratio: float):
    snap = MagicMock()
    snap.timestamp = timestamp
    snap.hit_ratio = hit_ratio
    return snap


def _tracker(*snaps) -> StatsTracker:
    tracker = MagicMock(spec=StatsTracker)
    tracker.history.return_value = list(snaps)
    return tracker


class TestComputeGradient:
    def test_empty_tracker_returns_empty(self):
        result = compute_gradient(_tracker())
        assert result == []

    def test_single_snapshot_gradient_is_none(self):
        result = compute_gradient(_tracker(_snap(0.0, 0.8)))
        assert len(result) == 1
        assert result[0].gradient is None
        assert result[0].hit_ratio == pytest.approx(0.8)

    def test_two_snapshots_gradient_calculated(self):
        result = compute_gradient(
            _tracker(_snap(0.0, 0.5), _snap(2.0, 0.7))
        )
        assert len(result) == 2
        assert result[0].gradient is None
        # (0.7 - 0.5) / 2.0 == 0.1
        assert result[1].gradient == pytest.approx(0.1)

    def test_gradient_negative_when_ratio_drops(self):
        result = compute_gradient(
            _tracker(_snap(0.0, 0.9), _snap(1.0, 0.6))
        )
        assert result[1].gradient == pytest.approx(-0.3)

    def test_gradient_zero_when_ratio_unchanged(self):
        result = compute_gradient(
            _tracker(_snap(0.0, 0.75), _snap(5.0, 0.75))
        )
        assert result[1].gradient == pytest.approx(0.0)

    def test_gradient_none_when_dt_is_zero(self):
        result = compute_gradient(
            _tracker(_snap(1.0, 0.5), _snap(1.0, 0.8))
        )
        assert result[1].gradient is None

    def test_multiple_snapshots_length_matches(self):
        snaps = [_snap(float(i), 0.5 + i * 0.05) for i in range(6)]
        result = compute_gradient(_tracker(*snaps))
        assert len(result) == 6

    def test_timestamps_preserved(self):
        result = compute_gradient(
            _tracker(_snap(10.0, 0.4), _snap(20.0, 0.6))
        )
        assert result[0].timestamp == pytest.approx(10.0)
        assert result[1].timestamp == pytest.approx(20.0)

    def test_str_contains_gradient(self):
        pt = GradientPoint(timestamp=5.0, hit_ratio=0.75, gradient=0.01)
        s = str(pt)
        assert "gradient" in s.lower() or "+0.010000" in s

    def test_str_na_when_gradient_none(self):
        pt = GradientPoint(timestamp=0.0, hit_ratio=0.5, gradient=None)
        assert "N/A" in str(pt)
