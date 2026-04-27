"""Alert system for cache hit ratio thresholds."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

DEFAULT_WARN_THRESHOLD = 0.7
DEFAULT_CRIT_THRESHOLD = 0.5


@dataclass
class Alert:
    level: str  # 'warn' or 'crit'
    hit_ratio: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return (
            f"[{self.level.upper()}] {self.timestamp.strftime('%H:%M:%S')} "
            f"Hit ratio {self.hit_ratio:.1%} is below "
            f"{self.level} threshold {self.threshold:.1%}"
        )


class AlertManager:
    """Monitors hit ratio snapshots and fires threshold-based alerts."""

    def __init__(
        self,
        warn_threshold: float = DEFAULT_WARN_THRESHOLD,
        crit_threshold: float = DEFAULT_CRIT_THRESHOLD,
        max_history: int = 50,
    ) -> None:
        if crit_threshold >= warn_threshold:
            raise ValueError(
                "crit_threshold must be strictly less than warn_threshold"
            )
        self.warn_threshold = warn_threshold
        self.crit_threshold = crit_threshold
        self.max_history = max_history
        self._alerts: List[Alert] = []

    def evaluate(self, hit_ratio: float) -> Optional[Alert]:
        """Evaluate a hit ratio and return an Alert if a threshold is breached."""
        alert: Optional[Alert] = None

        if hit_ratio < self.crit_threshold:
            alert = Alert(
                level="crit",
                hit_ratio=hit_ratio,
                threshold=self.crit_threshold,
            )
        elif hit_ratio < self.warn_threshold:
            alert = Alert(
                level="warn",
                hit_ratio=hit_ratio,
                threshold=self.warn_threshold,
            )

        if alert is not None:
            self._alerts.append(alert)
            if len(self._alerts) > self.max_history:
                self._alerts.pop(0)

        return alert

    @property
    def alerts(self) -> List[Alert]:
        """Return a copy of the recorded alert history."""
        return list(self._alerts)

    def clear(self) -> None:
        """Clear all recorded alerts."""
        self._alerts.clear()
