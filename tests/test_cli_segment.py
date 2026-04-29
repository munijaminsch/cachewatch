"""Tests for cachewatch.cli_segment."""
import json
import os
import tempfile
from argparse import Namespace
from unittest.mock import patch

import pytest

from cachewatch.cli_segment import build_parser, run


def _write_json(records) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(records, fh)
    return path


def _make_records(n: int = 6):
    return [
        {"hits": 10 + i, "misses": 2, "timestamp": float(1_000_000 + i)}
        for i in range(n)
    ]


class TestBuildParser:
    def test_returns_parser(self):
        p = build_parser()
        assert p is not None

    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["some_file.json"])
        assert args.by_count is None
        assert args.by_duration is None
        assert args.json is False

    def test_by_count_arg(self):
        p = build_parser()
        args = p.parse_args(["f.json", "--by-count", "5"])
        assert args.by_count == 5

    def test_by_duration_arg(self):
        p = build_parser()
        args = p.parse_args(["f.json", "--by-duration", "30"])
        assert args.by_duration == 30.0

    def test_mutually_exclusive(self):
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args(["f.json", "--by-count", "3", "--by-duration", "10"])


class TestRun:
    def test_run_by_count_prints_segments(self, capsys):
        path = _write_json(_make_records(6))
        args = Namespace(input=path, by_count=3, by_duration=None, json=False)
        run(args)
        captured = capsys.readouterr()
        assert "seg_0" in captured.out
        assert "seg_1" in captured.out
        os.unlink(path)

    def test_run_by_duration_prints_segments(self, capsys):
        path = _write_json(_make_records(4))
        args = Namespace(input=path, by_count=None, by_duration=2.0, json=False)
        run(args)
        captured = capsys.readouterr()
        assert "w_" in captured.out
        os.unlink(path)

    def test_run_json_output(self, capsys):
        path = _write_json(_make_records(4))
        args = Namespace(input=path, by_count=2, by_duration=None, json=True)
        run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert "label" in data[0]
        assert "average_hit_ratio" in data[0]
        os.unlink(path)

    def test_empty_file_no_segments(self, capsys):
        path = _write_json([])
        args = Namespace(input=path, by_count=5, by_duration=None, json=False)
        run(args)
        captured = capsys.readouterr()
        assert "No segments" in captured.out
        os.unlink(path)

    def test_default_count_used_when_neither_flag(self, capsys):
        path = _write_json(_make_records(12))
        args = Namespace(input=path, by_count=None, by_duration=None, json=True)
        run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        # default segment_size=10 → 2 segments for 12 snapshots
        assert len(data) == 2
        os.unlink(path)
