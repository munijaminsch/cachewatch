"""Rich table rendering for WindowResult."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table

from cachewatch.window import WindowResult


def _fmt(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:.4f}"


def build_window_table(result: WindowResult) -> Table:
    """Build a Rich table summarising a WindowResult."""
    table = Table(
        title=f"Sliding Window  ({result.window_seconds}s)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Snapshots in window", str(result.count))
    table.add_row("Avg hit ratio", _fmt(result.avg_hit_ratio))
    table.add_row("Min hit ratio", _fmt(result.min_hit_ratio))
    table.add_row("Max hit ratio", _fmt(result.max_hit_ratio))
    table.add_row("Range (max-min)", _fmt(result.range_hit_ratio))

    return table


def print_window_table(result: WindowResult) -> None:  # pragma: no cover
    """Print a WindowResult table to stdout."""
    console = Console()
    console.print(build_window_table(result))
