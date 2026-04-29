"""Tests for cachewatch.cli_heatmap."""

from __future__ import annotations

import json
import os
from typing import List

import pytest

from cachewatch.cli_heatmap import build_parser, run, _load_tracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(tmp_path, records) -> str:
    path = str(tmp_path / "snaps.json")
    with open(path, "w") as fh:
        json.dump(records, fh)
    return path


def _make_records(n: int = 5, base: float = 1_000_000.0) -> List[dict]:
    return [
        {"hits": 80, "misses": 20, "timestamp": base + i}
        for i in range(n)
    ]


def _make_args(**kwargs):
    defaults = {"file": "dummy.json", "bucket": 60, "title": "Test Heatmap"}
    defaults.update(kwargs)
    ns = type("Namespace", (), defaults)()
    return ns


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

class TestBuildParser:
    def test_returns_parser(self):
        p = build_parser()
        assert p is not None

    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["--file", "x.json"])
        assert args.bucket == 60
        assert "Heatmap" in args.title

    def test_custom_bucket(self):
        p = build_parser()
        args = p.parse_args(["--file", "x.json", "--bucket", "30"])
        assert args.bucket == 30


# ---------------------------------------------------------------------------
# _load_tracker
# ---------------------------------------------------------------------------

class TestLoadTracker:
    def test_missing_file_returns_none(self):
        result = _load_tracker("/nonexistent/path/file.json")
        assert result is None

    def test_invalid_json_returns_none(self, tmp_path):
        path = str(tmp_path / "bad.json")
        with open(path, "w") as fh:
            fh.write("not json")
        assert _load_tracker(path) is None

    def test_valid_file_returns_tracker(self, tmp_path):
        path = _write_json(tmp_path, _make_records())
        tracker = _load_tracker(path)
        assert tracker is not None
        assert len(tracker._history) == 5  # noqa: SLF001


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

class TestRun:
    def test_missing_file_returns_1(self):
        args = _make_args(file="/no/such/file.json")
        assert run(args) == 1

    def test_valid_file_returns_0(self, tmp_path):
        path = _write_json(tmp_path, _make_records())
        args = _make_args(file=path)
        assert run(args) == 0

    def test_empty_snapshot_list_returns_0(self, tmp_path):
        path = _write_json(tmp_path, [])
        args = _make_args(file=path)
        assert run(args) == 0
