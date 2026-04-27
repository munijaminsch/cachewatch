"""Tests for cachewatch.cli_forecast."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from cachewatch.cli_forecast import build_parser, run


def _make_args(**kwargs) -> SimpleNamespace:
    defaults = {
        "file": "data.json",
        "ahead": 60.0,
        "window": 10,
        "output_json": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _write_json(path: Path, snapshots: list) -> None:
    path.write_text(json.dumps(snapshots))


class TestBuildParser:
    def test_returns_parser(self):
        parser = build_parser()
        assert parser is not None

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.json"])
        assert args.ahead == 60.0
        assert args.window == 10
        assert args.output_json is False

    def test_custom_ahead(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.json", "--ahead", "120"])
        assert args.ahead == 120.0

    def test_json_flag(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.json", "--json"])
        assert args.output_json is True


class TestRun:
    def test_returns_1_when_insufficient_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "data.json"
            _write_json(p, [{"hits": 10, "misses": 5, "timestamp": 0.0}])
            args = _make_args(file=str(p))
            assert run(args) == 1

    def test_returns_0_with_valid_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "data.json"
            _write_json(p, [
                {"hits": 40, "misses": 60, "timestamp": 0.0},
                {"hits": 60, "misses": 40, "timestamp": 10.0},
            ])
            args = _make_args(file=str(p))
            assert run(args) == 0

    def test_json_output_is_valid(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "data.json"
            _write_json(p, [
                {"hits": 50, "misses": 50, "timestamp": 0.0},
                {"hits": 70, "misses": 30, "timestamp": 10.0},
            ])
            args = _make_args(file=str(p), output_json=True)
            rc = run(args)
            assert rc == 0
            out = capsys.readouterr().out
            data = json.loads(out)
            assert "predicted_ratio" in data
            assert "slope" in data
            assert "seconds_ahead" in data

    def test_predicted_ratio_within_bounds(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "data.json"
            _write_json(p, [
                {"hits": 50, "misses": 50, "timestamp": 0.0},
                {"hits": 70, "misses": 30, "timestamp": 10.0},
            ])
            args = _make_args(file=str(p), output_json=True)
            run(args)
            out = capsys.readouterr().out
            data = json.loads(out)
            assert 0.0 <= data["predicted_ratio"] <= 1.0
