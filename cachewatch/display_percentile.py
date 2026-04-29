"""Rich table rendering for PercentileResult."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table

from cachewatch.percentile import PercentileResult


def _fmt(value: Optional[float]) -> str:
    """Format a ratio as a percentage string, or 'n/a'."""
    if value is None:
        return "[dim]n/a[/dim]"
    pct = value * 100.0
    if pct >= 90:
        color = "green"
    elif pct >= 70:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{pct:.1f}%[/{color}]"


def build_percentile_table(result: PercentileResult) -> Table:
    """Return a Rich :class:`Table` summarising the percentile result."""
    table = Table(title="Hit-Ratio Percentiles", show_header=True, header_style="bold cyan")
    table.add_column("Percentile", style="bold", justify="right")
    table.add_column("Hit Ratio", justify="center")

    rows = [
        ("p50 (median)", result.p50),
        ("p90", result.p90),
        ("p95", result.p95),
        ("p99", result.p99),
    ]
    for label, value in rows:
        table.add_row(label, _fmt(value))

    table.caption = f"Sample count: {result.sample_count}"
    return table


def print_percentile_table(result: PercentileResult, console: Optional[Console] = None) -> None:
    """Print the percentile table to *console* (defaults to a new Console)."""
    if console is None:
        console = Console()
    console.print(build_percentile_table(result))
