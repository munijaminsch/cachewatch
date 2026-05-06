"""Rich display helpers for RhythmResult."""

from __future__ import annotations

from typing import Optional

from rich.table import Table
from rich import print as rprint

from cachewatch.rhythm import RhythmResult


def _fmt(value: Optional[float], decimals: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _strength_style(strength: float) -> str:
    if strength >= 0.7:
        return "bold green"
    if strength >= 0.4:
        return "yellow"
    return "red"


def build_rhythm_table(result: Optional[RhythmResult]) -> Table:
    """Return a Rich Table summarising *result*."""
    table = Table(title="Rhythm / Periodicity Analysis", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    if result is None:
        table.add_row("Status", "[dim]Insufficient data[/dim]")
        return table

    style = _strength_style(result.strength)
    table.add_row("Period (seconds)", f"{result.period_seconds:.2f}")
    table.add_row(
        "Strength",
        f"[{style}]{result.strength * 100:.1f}%[/{style}]",
    )
    table.add_row("Mean Hit Ratio", _fmt(result.mean_ratio))
    table.add_row("Snapshots Used", str(result.sample_count))
    return table


def print_rhythm_table(result: Optional[RhythmResult]) -> None:
    """Print the rhythm table to stdout via Rich."""
    rprint(build_rhythm_table(result))
