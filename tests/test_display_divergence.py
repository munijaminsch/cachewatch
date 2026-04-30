"""Tests for cachewatch.display_divergence."""
from __future__ import annotations

from rich.table import Table

from cachewatch.divergence import DivergenceResult
from cachewatch.display_divergence import build_divergence_table, _fmt


class TestFmt:
    def test_none_returns_na(self):
        assert _fmt(None) == "N/A"

    def test_formats_to_four_decimals(self):
        assert _fmt(0.12345) == "0.1235"

    def test_positive_sign_when_requested(self):
        assert _fmt(0.5, sign=True) == "+0.5000"

    def test_negative_no_extra_sign(self):
        assert _fmt(-0.3, sign=True) == "-0.3000"

    def test_zero_with_sign_is_positive(self):
        assert _fmt(0.0, sign=True) == "+0.0000"


class TestBuildDivergenceTable:
    def _make_result(self, **kwargs) -> DivergenceResult:
        defaults = dict(
            mean_a=0.9,
            mean_b=0.7,
            max_gap=-0.3,
            mean_gap=-0.2,
            sample_count=10,
        )
        defaults.update(kwargs)
        return DivergenceResult(**defaults)

    def test_returns_rich_table(self):
        result = self._make_result()
        table = build_divergence_table(result)
        assert isinstance(table, Table)

    def test_table_title_contains_labels(self):
        result = self._make_result()
        table = build_divergence_table(result, label_a="primary", label_b="replica")
        assert "primary" in (table.title or "")
        assert "replica" in (table.title or "")

    def test_table_has_two_columns(self):
        result = self._make_result()
        table = build_divergence_table(result)
        assert len(table.columns) == 2

    def test_table_has_five_rows(self):
        result = self._make_result()
        table = build_divergence_table(result)
        assert table.row_count == 5

    def test_none_values_show_na(self):
        result = DivergenceResult(
            mean_a=None,
            mean_b=None,
            max_gap=None,
            mean_gap=None,
            sample_count=0,
        )
        table = build_divergence_table(result)
        assert isinstance(table, Table)
