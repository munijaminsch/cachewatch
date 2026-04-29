"""Sampler: downsample a tracker's snapshots by keeping every Nth entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker, Snapshot


@dataclass
class SampleResult:
    """Result of a downsampling operation."""

    original_count: int
    sampled_count: int
    snapshots: List[Snapshot]
    step: int

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"SampleResult(original={self.original_count}, "
            f"sampled={self.sampled_count}, step={self.step})"
        )


def sample_snapshots(
    snapshots: List[Snapshot],
    step: int = 2,
) -> SampleResult:
    """Return every *step*-th snapshot from *snapshots*.

    Parameters
    ----------
    snapshots:
        Ordered list of :class:`~cachewatch.stats_tracker.Snapshot` objects.
    step:
        Keep one snapshot every *step* entries (must be >= 1).

    Returns
    -------
    SampleResult
        Container with the downsampled list and metadata.
    """
    if step < 1:
        raise ValueError(f"step must be >= 1, got {step}")

    sampled = snapshots[::step]
    return SampleResult(
        original_count=len(snapshots),
        sampled_count=len(sampled),
        snapshots=sampled,
        step=step,
    )


def sample_tracker(
    tracker: StatsTracker,
    step: int = 2,
    max_points: Optional[int] = None,
) -> SampleResult:
    """Downsample all snapshots stored in *tracker*.

    Parameters
    ----------
    tracker:
        Source of snapshots.
    step:
        Passed directly to :func:`sample_snapshots`.
    max_points:
        If provided, *step* is automatically computed so that at most
        *max_points* snapshots are returned (overrides *step*).
    """
    all_snaps: List[Snapshot] = tracker.history()

    if max_points is not None and max_points >= 1 and len(all_snaps) > max_points:
        step = max(1, len(all_snaps) // max_points)

    return sample_snapshots(all_snaps, step=step)
