"""Tests for cachewatch.alert module."""

import pytest
from cachewatch.alert import Alert, AlertManager, DEFAULT_WARN_THRESHOLD, DEFAULT_CRIT_THRESHOLD


class TestAlert:
    def test_str_contains_level_and_ratio(self):
        alert = Alert(level="warn", hit_ratio=0.65, threshold=0.70)
        text = str(alert)
        assert "WARN" in text
        assert "65.0%" in text
        assert "70.0%" in text

    def test_str_crit_level(self):
        alert = Alert(level="crit", hit_ratio=0.40, threshold=0.50)
        assert "CRIT" in str(alert)


class TestAlertManager:
    def test_default_thresholds(self):
        mgr = AlertManager()
        assert mgr.warn_threshold == DEFAULT_WARN_THRESHOLD
        assert mgr.crit_threshold == DEFAULT_CRIT_THRESHOLD

    def test_invalid_thresholds_raises(self):
        with pytest.raises(ValueError):
            AlertManager(warn_threshold=0.5, crit_threshold=0.6)

    def test_no_alert_above_warn_threshold(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5)
        result = mgr.evaluate(0.85)
        assert result is None
        assert mgr.alerts == []

    def test_warn_alert_between_thresholds(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5)
        result = mgr.evaluate(0.65)
        assert result is not None
        assert result.level == "warn"
        assert result.hit_ratio == pytest.approx(0.65)
        assert len(mgr.alerts) == 1

    def test_crit_alert_below_crit_threshold(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5)
        result = mgr.evaluate(0.40)
        assert result is not None
        assert result.level == "crit"

    def test_alerts_history_accumulates(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5)
        mgr.evaluate(0.60)
        mgr.evaluate(0.45)
        assert len(mgr.alerts) == 2

    def test_alerts_history_capped_at_max(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5, max_history=3)
        for _ in range(5):
            mgr.evaluate(0.40)
        assert len(mgr.alerts) == 3

    def test_clear_resets_history(self):
        mgr = AlertManager()
        mgr.evaluate(0.40)
        mgr.clear()
        assert mgr.alerts == []

    def test_evaluate_at_exact_warn_threshold_no_alert(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5)
        result = mgr.evaluate(0.70)
        assert result is None

    def test_evaluate_at_exact_crit_threshold_no_crit_alert(self):
        mgr = AlertManager(warn_threshold=0.7, crit_threshold=0.5)
        result = mgr.evaluate(0.50)
        # exactly at crit threshold — not strictly below, so warn fires
        assert result is not None
        assert result.level == "warn"
