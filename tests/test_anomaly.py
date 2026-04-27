"""Tests for cachewatch.anomaly module."""
import time
import pytest
from unittest.mock import MagicMock
from cachewatch.anomaly import Anomaly, AnomalyDetector
from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


TS = 1_700_000_000.0


def _snap(hit_ratio: float, ts_offset: float = 0.0):
    """Create a minimal snapshot mock."""
    snap = MagicMock()
    snap.hit_ratio = hit_ratio
    snap.timestamp = TS + ts_offset
    return snap


def _tracker(ratios):
    tracker = MagicMock(spec=StatsTracker)
    tracker.history.return_value = [
        _snap(r, i * 10.0) for i, r in enumerate(ratios)
    ]
    return tracker


class TestAnomaly:
    def test_str_contains_kind_and_ratio(self):
        a = Anomaly(kind="drop", description="big drop", ratio=0.42, timestamp=TS)
        s = str(a)
        assert "DROP" in s
        assert "42.00%" in s

    def test_str_spike(self):
        a = Anomaly(kind="spike", description="sudden spike", ratio=0.99, timestamp=TS)
        assert "SPIKE" in str(a)


class TestAnomalyDetector:
    def test_no_anomalies_when_single_snapshot(self):
        detector = AnomalyDetector()
        tracker = _tracker([0.80])
        assert detector.detect(tracker) == []

    def test_no_anomalies_when_empty(self):
        detector = AnomalyDetector()
        tracker = _tracker([])
        assert detector.detect(tracker) == []

    def test_detects_drop(self):
        detector = AnomalyDetector(drop_threshold=0.10)
        tracker = _tracker([0.90, 0.75])
        anomalies = detector.detect(tracker)
        assert len(anomalies) == 1
        assert anomalies[0].kind == "drop"

    def test_detects_spike(self):
        detector = AnomalyDetector(spike_threshold=0.10)
        tracker = _tracker([0.50, 0.65])
        anomalies = detector.detect(tracker)
        assert len(anomalies) == 1
        assert anomalies[0].kind == "spike"

    def test_no_anomaly_within_threshold(self):
        detector = AnomalyDetector(drop_threshold=0.10, spike_threshold=0.10)
        tracker = _tracker([0.80, 0.82, 0.79, 0.81])
        drops_or_spikes = [a for a in detector.detect(tracker) if a.kind != "flat"]
        assert drops_or_spikes == []

    def test_detects_flat_line(self):
        detector = AnomalyDetector(flat_window=4, flat_tolerance=0.005)
        tracker = _tracker([0.80, 0.801, 0.800, 0.801, 0.800])
        flat = [a for a in detector.detect(tracker) if a.kind == "flat"]
        assert len(flat) == 1

    def test_latest_returns_last_anomaly(self):
        detector = AnomalyDetector(drop_threshold=0.10)
        tracker = _tracker([0.90, 0.70])
        latest = detector.latest(tracker)
        assert latest is not None
        assert latest.kind == "drop"

    def test_latest_none_when_no_anomalies(self):
        detector = AnomalyDetector()
        tracker = _tracker([0.80, 0.81])
        assert detector.latest(tracker) is None
