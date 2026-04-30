"""Tests for cachewatch.display_momentum."""

from __future__ import annotations

from rich.table import Table

from cachewatch.momentum import MomentumPoint
from cachewatch.display_momentum import (
    _fmt_ratio,
    _fmt_momentum,
    _momentum_style,
    build_momentum_table,
)


class TestFmtRatio:
    def test_none_returns_na(self):
        assert _fmt_ratio(None) == "N/A"

    def test_formats_four_decimals(self):
        assert _fmt_ratio(0.8) == "0.8000"

    def test_zero(self):
        assert _fmt_ratio(0.0) == "0.0000"


class TestFmtMomentum:
    def test_none_returns_na(self):
        assert _fmt_momentum(None) == "N/A"

    def test_positive_has_plus_and_per_second(self):
        result = _fmt_momentum(0.01)
        assert "+" in result
        assert "/s" in result

    def test_negative_no_plus(self):
        result = _fmt_momentum(-0.02)
        assert "+" not in result
        assert "/s" in result

    def test_zero_has_plus(self):
        result = _fmt_momentum(0.0)
        assert "+" in result


class TestMomentumStyle:
    def test_none_is_dim(self):
        assert _momentum_style(None) == "dim"

    def test_positive_is_green(self):
        assert _momentum_style(0.05) == "green"

    def test_negative_is_red(self):
        assert _momentum_style(-0.05) == "red"

    def test_zero_is_yellow(self):
        assert _momentum_style(0.0) == "yellow"


class TestBuildMomentumTable:
    def _make_points(self):
        return [
            MomentumPoint(timestamp=1000.0, hit_ratio=0.8, momentum=None),
            MomentumPoint(timestamp=1010.0, hit_ratio=0.85, momentum=0.005),
            MomentumPoint(timestamp=1020.0, hit_ratio=0.75, momentum=-0.01),
        ]

    def test_returns_rich_table(self):
        table = build_momentum_table(self._make_points())
        assert isinstance(table, Table)

    def test_table_has_three_columns(self):
        table = build_momentum_table(self._make_points())
        assert len(table.columns) == 3

    def test_empty_points_returns_empty_table(self):
        table = build_momentum_table([])
        assert isinstance(table, Table)
        assert table.row_count == 0

    def test_row_count_matches_points(self):
        points = self._make_points()
        table = build_momentum_table(points)
        assert table.row_count == len(points)
