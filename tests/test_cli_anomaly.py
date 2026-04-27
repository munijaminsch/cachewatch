"""Tests for cachewatch.cli_anomaly module."""
import argparse
import pytest
from unittest.mock import MagicMock, patch
from cachewatch.cli_anomaly import build_parser, run
from cachewatch.anomaly import Anomaly


TS = 1_700_000_000.0


def _make_args(**kwargs):
    defaults = dict(
        host="localhost",
        port=6379,
        samples=3,
        interval=0.0,
        drop=0.10,
        spike=0.10,
        flat_window=5,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildParser:
    def test_returns_parser(self):
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.host == "localhost"
        assert args.port == 6379
        assert args.samples == 20
        assert args.drop == 0.10

    def test_custom_args(self):
        parser = build_parser()
        args = parser.parse_args(["--host", "redis-server", "--port", "6380", "--samples", "5"])
        assert args.host == "redis-server"
        assert args.port == 6380
        assert args.samples == 5


class TestRun:
    def _fake_snapshot(self, ratio=0.80):
        snap = MagicMock()
        snap.hit_ratio = ratio
        snap.timestamp = TS
        return snap

    @patch("cachewatch.cli_anomaly.RedisCollector")
    @patch("cachewatch.cli_anomaly.AnomalyDetector")
    def test_no_anomalies_returns_zero(self, MockDetector, MockCollector):
        instance = MockCollector.return_value
        instance.collect.return_value = self._fake_snapshot()
        MockDetector.return_value.detect.return_value = []

        args = _make_args(samples=2)
        result = run(args)
        assert result == 0

    @patch("cachewatch.cli_anomaly.RedisCollector")
    @patch("cachewatch.cli_anomaly.AnomalyDetector")
    def test_anomalies_returns_zero_and_prints(self, MockDetector, MockCollector, capsys):
        instance = MockCollector.return_value
        instance.collect.return_value = self._fake_snapshot()
        anomaly = Anomaly(kind="drop", description="big drop", ratio=0.60, timestamp=TS)
        MockDetector.return_value.detect.return_value = [anomaly]

        args = _make_args(samples=2)
        result = run(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "DROP" in captured.out

    @patch("cachewatch.cli_anomaly.RedisCollector")
    def test_collector_error_returns_one(self, MockCollector):
        MockCollector.return_value.collect.side_effect = ConnectionError("refused")
        args = _make_args(samples=1)
        result = run(args)
        assert result == 1
