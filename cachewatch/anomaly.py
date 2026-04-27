"""Anomaly detection for cache hit ratio trends."""
from dataclasses import dataclass
from typing import List, Optional
from cachewatch.stats_tracker import StatsTracker


@dataclass
class Anomaly:
    kind: str  # 'spike' | 'drop' | 'flat'
    description: str
    ratio: float
    timestamp: float

    def __str__(self) -> str:
        return f"[{self.kind.upper()}] {self.description} (ratio={self.ratio:.2%})"


class AnomalyDetector:
    """Detect anomalies in hit ratio history."""

    def __init__(
        self,
        drop_threshold: float = 0.10,
        spike_threshold: float = 0.10,
        flat_window: int = 5,
        flat_tolerance: float = 0.005,
    ) -> None:
        self.drop_threshold = drop_threshold
        self.spike_threshold = spike_threshold
        self.flat_window = flat_window
        self.flat_tolerance = flat_tolerance

    def detect(self, tracker: StatsTracker) -> List[Anomaly]:
        snapshots = tracker.history()
        if len(snapshots) < 2:
            return []

        anomalies: List[Anomaly] = []
        ratios = [s.hit_ratio for s in snapshots]

        for i in range(1, len(ratios)):
            prev, curr = ratios[i - 1], ratios[i]
            ts = snapshots[i].timestamp
            delta = curr - prev

            if delta <= -self.drop_threshold:
                anomalies.append(
                    Anomaly(
                        kind="drop",
                        description=f"Hit ratio dropped by {abs(delta):.2%}",
                        ratio=curr,
                        timestamp=ts,
                    )
                )
            elif delta >= self.spike_threshold:
                anomalies.append(
                    Anomaly(
                        kind="spike",
                        description=f"Hit ratio spiked by {delta:.2%}",
                        ratio=curr,
                        timestamp=ts,
                    )
                )

        # Flat-line detection over a rolling window
        if len(ratios) >= self.flat_window:
            window = ratios[-self.flat_window :]
            if max(window) - min(window) <= self.flat_tolerance:
                ts = snapshots[-1].timestamp
                anomalies.append(
                    Anomaly(
                        kind="flat",
                        description=(
                            f"Hit ratio has been flat for last {self.flat_window} samples"
                        ),
                        ratio=ratios[-1],
                        timestamp=ts,
                    )
                )

        return anomalies

    def latest(self, tracker: StatsTracker) -> Optional[Anomaly]:
        detected = self.detect(tracker)
        return detected[-1] if detected else None
