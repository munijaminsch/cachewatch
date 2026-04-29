"""Rich-based display helpers for the heatmap feature."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table
from rich import box
import datetime

from cachewatch.heatmap import HeatmapRow


def build_heatmap_table(rows: List[HeatmapRow], title: str = "Cache Hit Ratio Heatmap") -> Table:
    """Build a Rich Table visualising heatmap rows."""
    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Time", style="cyan", no_wrap=True)
    table.add_column("Shade", justify="center")
    table.add_column("Hit Ratio", justify="right")

    for row in rows:
        dt = datetime.datetime.fromtimestamp(row.timestamp).strftime("%H:%M:%S")
        ratio_str = f"{row.hit_ratio:.2%}" if row.hit_ratio is not None else "N/A"

        if row.hit_ratio is None:
            color = "white"
        elif row.hit_ratio >= 0.75:
            color = "green"
        elif row.hit_ratio >= 0.5:
            color = "yellow"
        else:
            color = "red"

        table.add_row(dt, f"[{color}]{row.label}[/{color}]", f"[{color}]{ratio_str}[/{color}]")

    return table


def print_heatmap_table(rows: List[HeatmapRow], title: str = "Cache Hit Ratio Heatmap") -> None:
    """Print the heatmap table to stdout."""
    console = Console()
    if not rows:
        console.print("[yellow]No data available for heatmap.[/yellow]")
        return
    table = build_heatmap_table(rows, title=title)
    console.print(table)
