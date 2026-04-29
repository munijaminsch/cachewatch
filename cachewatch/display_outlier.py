"""Rich table rendering for outlier detection results."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from cachewatch.outlier import OutlierResult

_console = Console()


def build_outlier_table(outliers: List[OutlierResult]) -> Table:
    table = Table(title="Cache Hit Ratio Outliers", show_lines=True)
    table.add_column("Timestamp", style="dim", justify="right")
    table.add_column("Hit Ratio", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("Z-Score", justify="right")
    table.add_column("Direction")

    for r in outliers:
        direction = "[red]low[/red]" if r.hit_ratio < r.mean else "[green]high[/green]"
        z_color = "red" if abs(r.z_score) >= 3.0 else "yellow"
        table.add_row(
            f"{r.timestamp:.2f}",
            f"{r.hit_ratio:.3f}",
            f"{r.mean:.3f}",
            f"{r.std_dev:.3f}",
            f"[{z_color}]{r.z_score:+.2f}[/{z_color}]",
            direction,
        )

    return table


def print_outlier_table(outliers: List[OutlierResult]) -> None:
    if not outliers:
        _console.print("[green]No outliers detected.[/green]")
        return
    _console.print(build_outlier_table(outliers))
