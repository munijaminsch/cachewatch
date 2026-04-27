"""Tests for cachewatch.exporter."""

from __future__ import annotations

import json
import csv
import io
from unittest.mock import MagicMock, patch

import pytest

from cachewatch.redis_collector import CacheStats
from cachewatch.stats_tracker import StatsTracker
from cachewatch.exporter import (
    export_json,
    export_csv,
    export_latest_json,
    save_to_file,
)


def _make_tracker(*hit_miss_pairs):
    """Build a StatsTracker pre-populated with snapshots."""
    tracker = StatsTracker(maxlen=50)
    for hits, misses in hit_miss_pairs:
        tracker.record(CacheStats(hits=hits, misses=misses))
    return tracker


class TestExportJson:
    def test_empty_tracker_returns_empty_list(self):
        tracker = StatsTracker()
        result = json.loads(export_json(tracker))
        assert result == []

    def test_contains_all_snapshots(self):
        tracker = _make_tracker((10, 5), (20, 8))
        result = json.loads(export_json(tracker))
        assert len(result) == 2

    def test_fields_present(self):
        tracker = _make_tracker((100, 25))
        record = json.loads(export_json(tracker))[0]
        for field in ("hits", "misses", "total", "hit_ratio", "miss_ratio", "timestamp"):
            assert field in record

    def test_hit_ratio_value(self):
        tracker = _make_tracker((80, 20))
        record = json.loads(export_json(tracker))[0]
        assert record["hit_ratio"] == pytest.approx(0.8, abs=1e-4)
        assert record["total"] == 100


class TestExportCsv:
    def test_empty_tracker_returns_empty_string(self):
        tracker = StatsTracker()
        assert export_csv(tracker) == ""

    def test_csv_has_header_and_rows(self):
        tracker = _make_tracker((50, 50), (60, 40))
        content = export_csv(tracker)
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) == 2
        assert "hit_ratio" in rows[0]

    def test_csv_values_correct(self):
        tracker = _make_tracker((3, 1))
        content = export_csv(tracker)
        reader = csv.DictReader(io.StringIO(content))
        row = next(reader)
        assert float(row["hit_ratio"]) == pytest.approx(0.75, abs=1e-4)


class TestExportLatestJson:
    def test_returns_none_when_empty(self):
        tracker = StatsTracker()
        assert export_latest_json(tracker) is None

    def test_returns_single_snapshot(self):
        tracker = _make_tracker((40, 10), (90, 10))
        result = json.loads(export_latest_json(tracker))
        # latest should reflect the second snapshot
        assert result["hits"] == 90


class TestSaveToFile:
    def test_writes_content(self, tmp_path):
        target = tmp_path / "output.json"
        save_to_file('{"ok": true}', str(target))
        assert target.read_text() == '{"ok": true}'
