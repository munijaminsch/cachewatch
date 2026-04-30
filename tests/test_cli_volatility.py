"""Tests for cachewatch.cli_volatility."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from cachewatch.cli_volatility import build_parser, run


def _write_json(records) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(records, fh)
    return path


def _make_records(n: int = 4):
    return [
        {"hits": 10 * (i + 1), "misses": i, "timestamp": float(i)}
        for i in range(n)
    ]


def _make_args(**kwargs):
    defaults = {"file": "data.json", "last_n": None, "json": False}
    defaults.update(kwargs)
    import argparse
    return argparse.Namespace(**defaults)


class TestBuildParser:
    def test_returns_parser(self):
        p = build_parser()
        assert p is not None

    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["myfile.json"])
        assert args.file == "myfile.json"
        assert args.last_n is None
        assert args.json is False

    def test_last_n_flag(self):
        p = build_parser()
        args = p.parse_args(["f.json", "--last-n", "10"])
        assert args.last_n == 10

    def test_json_flag(self):
        p = build_parser()
        args = p.parse_args(["f.json", "--json"])
        assert args.json is True


class TestRun:
    def test_missing_file_returns_1(self):
        args = _make_args(file="/nonexistent/path.json")
        assert run(args) == 1

    def test_empty_file_returns_1(self, capsys):
        path = _write_json([])
        try:
            args = _make_args(file=path)
            result = run(args)
            assert result == 1
        finally:
            os.unlink(path)

    def test_valid_data_returns_0(self, capsys):
        path = _write_json(_make_records())
        try:
            args = _make_args(file=path)
            with patch("cachewatch.cli_volatility.print_volatility_table"):
                result = run(args)
            assert result == 0
        finally:
            os.unlink(path)

    def test_json_output_contains_keys(self, capsys):
        path = _write_json(_make_records())
        try:
            args = _make_args(file=path, json=True)
            result = run(args)
            assert result == 0
            captured = capsys.readouterr()
            payload = json.loads(captured.out)
            assert "std_dev" in payload
            assert "mean" in payload
            assert "window" in payload
        finally:
            os.unlink(path)

    def test_last_n_respected(self, capsys):
        path = _write_json(_make_records(6))
        try:
            args = _make_args(file=path, last_n=2, json=True)
            result = run(args)
            assert result == 0
            payload = json.loads(capsys.readouterr().out)
            assert payload["window"] == 2
        finally:
            os.unlink(path)
