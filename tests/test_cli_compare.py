"""Tests for cachewatch.cli_compare."""
from __future__ import annotations

import json
import os
import tempfile
from argparse import Namespace
from unittest.mock import patch, MagicMock

import pytest

from cachewatch.cli_compare import build_parser, run


BASE = 1_700_000_000.0


def _make_args(**kwargs) -> Namespace:
    defaults = dict(
        input="data.json",
        start_a=BASE,
        end_a=BASE + 10,
        start_b=BASE + 20,
        end_b=BASE + 30,
        json=False,
    )
    defaults.update(kwargs)
    return Namespace(**defaults)


def _write_json(records, tmp_dir):
    path = os.path.join(tmp_dir, "data.json")
    with open(path, "w") as fh:
        json.dump(records, fh)
    return path


class TestBuildParser:
    def test_returns_parser(self):
        p = build_parser()
        assert p is not None

    def test_required_args(self):
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args([])

    def test_json_flag_default_false(self):
        p = build_parser()
        args = p.parse_args([
            "--input", "x.json",
            "--start-a", "0", "--end-a", "10",
            "--start-b", "20", "--end-b", "30",
        ])
        assert args.json is False


class TestRun:
    def test_missing_file_returns_1(self):
        args = _make_args(input="/nonexistent/path.json")
        assert run(args) == 1

    def test_run_text_output(self, capsys):
        records = [
            {"timestamp": BASE + 1, "hits": 80, "misses": 20},
            {"timestamp": BASE + 25, "hits": 90, "misses": 10},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(records, tmp)
            args = _make_args(input=path)
            rc = run(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "ComparisonResult" in out

    def test_run_json_output(self, capsys):
        records = [
            {"timestamp": BASE + 1, "hits": 80, "misses": 20},
            {"timestamp": BASE + 25, "hits": 90, "misses": 10},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(records, tmp)
            args = _make_args(input=path, json=True)
            rc = run(args)
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "delta" in data
        assert "improved" in data

    def test_run_no_data_returns_none_fields(self, capsys):
        records: list = []
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(records, tmp)
            args = _make_args(input=path, json=True)
            rc = run(args)
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["delta"] is None
