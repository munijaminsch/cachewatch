"""Rich table display for smoothed hit-ratio data."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from cachewatch.smoothing import SmoothedPoint


def _fmt(value: float | None, precision: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{precision}f}"


def build_smoothing_table(points: List[SmoothedPoint], window: int) -> Table:
    """Build a Rich table from a list of SmoothedPoints."""
    table = Table(
        title=f"Smoothed Hit Ratio (window={window})",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Timestamp", style="dim", justify="right")
    table.add_column("Raw Ratio", justify="right")
    table.add_column("Smoothed Ratio", justify="right")

    for pt in points:
        raw_str = _fmt(pt.raw_ratio)
        smoothed_str = _fmt(pt.smoothed_ratio)

        if pt.smoothed_ratio is not None:
            if pt.smoothed_ratio >= 0.9:
                smoothed_style = "green"
            elif pt.smoothed_ratio >= 0.7:
                smoothed_style = "yellow"
            else:
                smoothed_style = "red"
        else:
            smoothed_style = "dim"

        table.add_row(
            f"{pt.timestamp:.1f}",
            raw_str,
            f"[{smoothed_style}]{smoothed_str}[/{smoothed_style}]",
        )

    return table


def print_smoothing_table(
    points: List[SmoothedPoint], window: int, console: Console | None = None
) -> None:
    """Print the smoothing table to the console."""
    if console is None:
        console = Console()
    table = build_smoothing_table(points, window=window)
    console.print(table)
