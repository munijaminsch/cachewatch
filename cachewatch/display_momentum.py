"""Rich table rendering for momentum data."""

from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from cachewatch.momentum import MomentumPoint


def _fmt_ratio(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "N/A"


def _fmt_momentum(value: float | None) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.4f}/s"


def _momentum_style(value: float | None) -> str:
    if value is None:
        return "dim"
    if value > 0:
        return "green"
    if value < 0:
        return "red"
    return "yellow"


def build_momentum_table(points: List[MomentumPoint]) -> Table:
    """Build a Rich ``Table`` from a list of :class:`MomentumPoint` objects."""
    table = Table(title="Hit-Ratio Momentum", show_lines=False)
    table.add_column("Timestamp", style="cyan", no_wrap=True)
    table.add_column("Hit Ratio", justify="right")
    table.add_column("Momentum", justify="right")

    for pt in points:
        style = _momentum_style(pt.momentum)
        table.add_row(
            f"{pt.timestamp:.1f}",
            _fmt_ratio(pt.hit_ratio),
            _fmt_momentum(pt.momentum),
            style=style,
        )

    return table


def print_momentum_table(points: List[MomentumPoint]) -> None:
    """Print the momentum table to stdout."""
    console = Console()
    console.print(build_momentum_table(points))
