"""Rich-table rendering for volatility results."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table

from cachewatch.volatility import VolatilityResult

_console = Console()


def _fmt(value: Optional[float]) -> str:
    return f"{value:.4f}" if value is not None else "n/a"


def build_volatility_table(result: VolatilityResult) -> Table:
    """Return a :class:`rich.table.Table` summarising *result*."""
    table = Table(title="Hit-Ratio Volatility", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Window (snapshots)", str(result.window))
    table.add_row("Std Dev", _fmt(result.std_dev))
    table.add_row("Mean", _fmt(result.mean))
    table.add_row("Min", _fmt(result.min_ratio))
    table.add_row("Max", _fmt(result.max_ratio))

    return table


def print_volatility_table(result: VolatilityResult) -> None:  # pragma: no cover
    """Print the volatility table to stdout."""
    _console.print(build_volatility_table(result))
