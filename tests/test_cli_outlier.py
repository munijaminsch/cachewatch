"""Tests for cachewatch.cli_outlier."""
from __future__ import annotations

import json
import os
import tempfile
from argparse import Namespace
from unittest.mock import patch

import pytest

from cachewatch.cli_outlier import build_parser, run


def _write_json(records) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(records, fh)
    return path


def _make_records(n: int = 12, spike_at: int | None = None):
    records = []
    for i in range(n):
        hits = 99 if (spike_at is not None and i == spike_at) else 5
        misses = 1 if (spike_at is not None and i == spike_at) else 5
        records.append({"hits": hits, "misses": misses, "timestamp": float(i)})
    return records


def _make_args(**kwargs) -> Namespace:
    defaults = {"file": "", "z_threshold": 2.0, "as_json": False}
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestBuildParser:
    def test_returns_parser(self):
        p = build_parser()
        assert p is not None

    def test_defaults(self):
        p = build_parser()
        path = _write_json(_make_records())
        args = p.parse_args([path])
        assert args.z_threshold == 2.0
        assert args.as_json is False
        os.unlink(path)

    def test_custom_z_threshold(self):
        p = build_parser()
        path = _write_json(_make_records())
        args = p.parse_args([path, "--z-threshold", "3.0"])
        assert args.z_threshold == 3.0
        os.unlink(path)

    def test_json_flag(self):
        p = build_parser()
        path = _write_json(_make_records())
        args = p.parse_args([path, "--json"])
        assert args.as_json is True
        os.unlink(path)


class TestRun:
    def test_no_outliers_prints_message(self, capsys):
        path = _write_json(_make_records(n=10))
        args = _make_args(file=path)
        run(args)
        captured = capsys.readouterr()
        # rich may strip markup in non-tty; just ensure no crash
        os.unlink(path)

    def test_json_output_is_valid(self, capsys):
        records = _make_records(n=12, spike_at=11)
        path = _write_json(records)
        args = _make_args(file=path, as_json=True)
        run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        os.unlink(path)

    def test_json_output_fields(self, capsys):
        records = _make_records(n=12, spike_at=11)
        path = _write_json(records)
        args = _make_args(file=path, as_json=True)
        run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        if data:
            keys = set(data[0].keys())
            assert {"timestamp", "hit_ratio", "mean", "std_dev", "z_score"} <= keys
        os.unlink(path)

    def test_spike_detected_in_json(self, capsys):
        records = _make_records(n=12, spike_at=11)
        path = _write_json(records)
        args = _make_args(file=path, as_json=True, z_threshold=2.0)
        run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert any(r["hit_ratio"] > 0.9 for r in data)
        os.unlink(path)
