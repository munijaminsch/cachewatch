"""Tests for cachewatch.heatmap."""

from __future__ import annotations

import time
from typing import List

import pytest

from cachewatch.heatmap import (
    HeatmapRow,
    SHADES,
    _ratio_to_shade,
    build_heatmap,
)
from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker, Snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(hits: int, misses: int, ts: float) -> Snapshot:
    return Snapshot(stats=CacheStats(hits=hits, misses=misses), timestamp=ts)


def _tracker(snaps: List[Snapshot]) -> StatsTracker:
    t = StatsTracker()
    for s in snaps:
        t._history.append(s)  # noqa: SLF001
    return t


# ---------------------------------------------------------------------------
# _ratio_to_shade
# ---------------------------------------------------------------------------

class TestRatioToShade:
    def test_none_returns_question_mark(self):
        assert _ratio_to_shade(None) == "?"

    def test_zero_returns_first_shade(self):
        assert _ratio_to_shade(0.0) == SHADES[0]

    def test_one_returns_last_shade(self):
        assert _ratio_to_shade(1.0) == SHADES[-1]

    def test_mid_value(self):
        shade = _ratio_to_shade(0.5)
        assert shade in SHADES


# ---------------------------------------------------------------------------
# HeatmapRow
# ---------------------------------------------------------------------------

class TestHeatmapRow:
    def test_str_contains_label(self):
        row = HeatmapRow(timestamp=1000.0, hit_ratio=0.75, label="▓")
        assert "▓" in str(row)

    def test_str_none_ratio(self):
        row = HeatmapRow(timestamp=1000.0, hit_ratio=None, label="?")
        assert "N/A" in str(row)


# ---------------------------------------------------------------------------
# build_heatmap
# ---------------------------------------------------------------------------

class TestBuildHeatmap:
    def test_empty_tracker_returns_empty(self):
        t = StatsTracker()
        assert build_heatmap(t, bucket_seconds=60) == []

    def test_single_bucket(self):
        base = 1_000_000.0
        snaps = [_snap(80, 20, base + i) for i in range(5)]
        t = _tracker(snaps)
        rows = build_heatmap(t, bucket_seconds=60)
        assert len(rows) == 1
        assert rows[0].hit_ratio == pytest.approx(0.8)

    def test_multiple_buckets(self):
        base = 1_000_000.0
        snaps = (
            [_snap(90, 10, base + i) for i in range(3)]
            + [_snap(40, 60, base + 120 + i) for i in range(3)]
        )
        t = _tracker(snaps)
        rows = build_heatmap(t, bucket_seconds=60)
        assert len(rows) == 2
        assert rows[0].hit_ratio == pytest.approx(0.9)
        assert rows[1].hit_ratio == pytest.approx(0.4)

    def test_row_label_is_shade_char(self):
        base = 1_000_000.0
        snaps = [_snap(100, 0, base + i) for i in range(3)]
        t = _tracker(snaps)
        rows = build_heatmap(t, bucket_seconds=60)
        assert rows[0].label in SHADES
