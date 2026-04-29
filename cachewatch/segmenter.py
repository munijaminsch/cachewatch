"""Segment tracker snapshots into labeled time windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker, Snapshot


@dataclass
class Segment:
    label: str
    snapshots: List[Snapshot] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.snapshots)

    @property
    def average_hit_ratio(self) -> Optional[float]:
        if not self.snapshots:
            return None
        return sum(s.stats.hit_ratio for s in self.snapshots) / len(self.snapshots)

    @property
    def start_ts(self) -> Optional[float]:
        return self.snapshots[0].timestamp if self.snapshots else None

    @property
    def end_ts(self) -> Optional[float]:
        return self.snapshots[-1].timestamp if self.snapshots else None

    def __str__(self) -> str:
        ratio = self.average_hit_ratio
        ratio_str = f"{ratio:.2%}" if ratio is not None else "n/a"
        return f"Segment({self.label!r}, n={self.count}, avg_hit_ratio={ratio_str})"


def segment_by_count(tracker: StatsTracker, segment_size: int, labels: Optional[List[str]] = None) -> List[Segment]:
    """Divide snapshots into fixed-size segments of *segment_size* each."""
    if segment_size < 1:
        raise ValueError("segment_size must be >= 1")
    snapshots = tracker.history()
    segments: List[Segment] = []
    for i, start in enumerate(range(0, len(snapshots), segment_size)):
        chunk = snapshots[start:start + segment_size]
        label = labels[i] if (labels and i < len(labels)) else f"seg_{i}"
        seg = Segment(label=label, snapshots=list(chunk))
        segments.append(seg)
    return segments


def segment_by_duration(tracker: StatsTracker, window_seconds: float) -> List[Segment]:
    """Divide snapshots into time-based windows of *window_seconds* width."""
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")
    snapshots = tracker.history()
    if not snapshots:
        return []
    origin = snapshots[0].timestamp
    segments: List[Segment] = []
    current_bucket: int = -1
    current_seg: Optional[Segment] = None
    for snap in snapshots:
        bucket = int((snap.timestamp - origin) / window_seconds)
        if bucket != current_bucket:
            current_bucket = bucket
            current_seg = Segment(label=f"w_{bucket}")
            segments.append(current_seg)
        current_seg.snapshots.append(snap)  # type: ignore[union-attr]
    return segments
