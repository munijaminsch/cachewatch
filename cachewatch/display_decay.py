"""Rich table display for DecayResult."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from cachewatch.decay import DecayResult


def _fmt(value: Optional[float], decimals: int = 4, sign: bool = False) -> str:
    if value is None:
        return "N/A"
    fmt = f"{{:+.{decimals}f}}" if sign else f"{{:.{decimals}f}}"
    return fmt.format(value)


def build_decay_table(result: Optional[DecayResult]) -> Table:
    """Return a Rich Table summarising *result*."""
    table = Table(
        title="Cache Hit-Ratio Decay Analysis",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="bold", min_width=22)
    table.add_column("Value", justify="right", min_width=18)

    if result is None:
        table.add_row("Status", "[yellow]Insufficient data[/yellow]")
        return table

    delta = result.final_ratio - result.initial_ratio
    delta_color = "green" if delta >= 0 else "red"
    rate_color = "green" if result.decay_rate >= 0 else "red"

    table.add_row("Snapshots analysed", str(result.snapshot_count))
    table.add_row("Initial hit ratio", _fmt(result.initial_ratio))
    table.add_row("Final hit ratio", _fmt(result.final_ratio))
    table.add_row(
        "Total change",
        f"[{delta_color}]{_fmt(delta, sign=True)}[/{delta_color}]",
    )
    table.add_row(
        "Decay rate (ratio/s)",
        f"[{rate_color}]{_fmt(result.decay_rate, decimals=6, sign=True)}[/{rate_color}]",
    )
    hl = (
        f"{result.half_life_seconds:.1f} s"
        if result.half_life_seconds is not None
        else "[dim]N/A (stable or improving)[/dim]"
    )
    table.add_row("Half-life", hl)
    return table


def print_decay_table(result: Optional[DecayResult], console: Optional[Console] = None) -> None:
    """Print the decay table to *console* (or a default Console)."""
    if console is None:
        console = Console()
    console.print(build_decay_table(result))
