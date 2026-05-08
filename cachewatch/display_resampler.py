"""Rich display helpers for resampled snapshot data."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from cachewatch.resampler import ResampledPoint

_console = Console()


def _fmt(value: float | None, decimals: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _ratio_style(ratio: float | None) -> str:
    if ratio is None:
        return "dim"
    if ratio >= 0.9:
        return "bold green"
    if ratio >= 0.7:
        return "yellow"
    return "bold red"


def build_resampler_table(points: List[ResampledPoint]) -> Table:
    """Build a Rich table from a list of :class:`ResampledPoint` objects."""
    table = Table(title="Resampled Hit Ratios", show_lines=False)
    table.add_column("Bucket (ts)", style="cyan", no_wrap=True)
    table.add_column("Interval (s)", justify="right")
    table.add_column("Snapshots", justify="right")
    table.add_column("Avg Hit Ratio", justify="right")

    for pt in points:
        style = _ratio_style(pt.average_hit_ratio)
        table.add_row(
            f"{pt.bucket_ts:.0f}",
            str(pt.interval_seconds),
            str(pt.count),
            _fmt(pt.average_hit_ratio),
            style=style,
        )
    return table


def print_resampler_table(points: List[ResampledPoint]) -> None:
    """Print the resampled table to stdout via Rich."""
    table = build_resampler_table(points)
    _console.print(table)
