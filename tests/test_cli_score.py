"""Tests for cachewatch.cli_score."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from cachewatch.cli_score import build_parser, run


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "input": "data.json",
        "trend_weight": 0.2,
        "as_json": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_json(tmp_path: Path, records: list) -> str:
    p = tmp_path / "data.json"
    p.write_text(json.dumps(records), encoding="utf-8")
    return str(p)


def _record(hits: int, misses: int, ts: str) -> dict:
    return {"hits": hits, "misses": misses, "timestamp": ts}


class TestBuildParser:
    def test_returns_parser(self):
        p = build_parser()
        assert p is not None

    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["data.json"])
        assert args.trend_weight == 0.2
        assert args.as_json is False

    def test_custom_trend_weight(self):
        p = build_parser()
        args = p.parse_args(["data.json", "--trend-weight", "0.3"])
        assert args.trend_weight == pytest.approx(0.3)

    def test_json_flag(self):
        p = build_parser()
        args = p.parse_args(["data.json", "--json"])
        assert args.as_json is True


class TestRun:
    def test_returns_1_on_empty_file(self, tmp_path, capsys):
        path = _write_json(tmp_path, [])
        args = _make_args(input=path)
        assert run(args) == 1

    def test_returns_0_on_valid_data(self, tmp_path):
        records = [
            _record(80, 20, "2024-01-01T00:00:00+00:00"),
            _record(85, 15, "2024-01-01T00:00:01+00:00"),
            _record(90, 10, "2024-01-01T00:00:02+00:00"),
        ]
        path = _write_json(tmp_path, records)
        args = _make_args(input=path)
        assert run(args) == 0

    def test_text_output_contains_grade(self, tmp_path, capsys):
        records = [
            _record(900, 100, "2024-01-01T00:00:00+00:00"),
            _record(910, 90, "2024-01-01T00:00:01+00:00"),
        ]
        path = _write_json(tmp_path, records)
        args = _make_args(input=path)
        run(args)
        captured = capsys.readouterr()
        assert "grade=" in captured.out

    def test_json_output_has_required_keys(self, tmp_path, capsys):
        records = [
            _record(80, 20, "2024-01-01T00:00:00+00:00"),
            _record(85, 15, "2024-01-01T00:00:01+00:00"),
        ]
        path = _write_json(tmp_path, records)
        args = _make_args(input=path, as_json=True)
        run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        for key in ("score", "grade", "avg_hit_ratio", "trough", "trend_slope"):
            assert key in data

    def test_score_in_valid_range(self, tmp_path, capsys):
        records = [
            _record(70, 30, "2024-01-01T00:00:00+00:00"),
            _record(75, 25, "2024-01-01T00:00:01+00:00"),
        ]
        path = _write_json(tmp_path, records)
        args = _make_args(input=path, as_json=True)
        run(args)
        data = json.loads(capsys.readouterr().out)
        assert 0.0 <= data["score"] <= 100.0
