"""Rank multiple StatsTracker instances by their average hit ratio."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from cachewatch.snapshot_filter import average_hit_ratio
from cachewatch.stats_tracker import StatsTracker


@dataclass
class RankEntry:
    """A single entry in a ranking result."""

    name: str
    tracker: StatsTracker
    avg_hit_ratio: Optional[float]
    rank: int

    def __str__(self) -> str:
        ratio_str = (
            f"{self.avg_hit_ratio:.2%}" if self.avg_hit_ratio is not None else "N/A"
        )
        return f"#{self.rank} {self.name}: {ratio_str}"


def rank_trackers(
    named_trackers: List[Tuple[str, StatsTracker]],
    ascending: bool = False,
) -> List[RankEntry]:
    """Rank trackers by average hit ratio.

    Args:
        named_trackers: List of (name, tracker) pairs to rank.
        ascending: If True, rank lowest ratio first (worst performers first).

    Returns:
        List of RankEntry objects sorted by average hit ratio.
        Trackers with no data are placed at the end.
    """
    entries: List[RankEntry] = []

    for name, tracker in named_trackers:
        snapshots = tracker.history()
        ratio = average_hit_ratio(snapshots) if snapshots else None
        entries.append(RankEntry(name=name, tracker=tracker, avg_hit_ratio=ratio, rank=0))

    def sort_key(entry: RankEntry):
        if entry.avg_hit_ratio is None:
            return (1, 0.0)
        return (0, entry.avg_hit_ratio if ascending else -entry.avg_hit_ratio)

    entries.sort(key=sort_key)

    for i, entry in enumerate(entries, start=1):
        entry.rank = i

    return entries
