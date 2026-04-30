"""Rich table display for DivergenceResult."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table

from cachewatch.divergence import DivergenceResult


def _fmt(value: Optional[float], sign: bool = False) -> str:
    if value is None:
        return "N/A"
    prefix = "+" if sign and value >= 0 else ""
    return f"{prefix}{value:.4f}"


def build_divergence_table(result: DivergenceResult, label_a: str = "A", label_b: str = "B") -> Table:
    """Build a Rich table summarising divergence between two trackers."""
    table = Table(title=f"Divergence: {label_a} vs {label_b}", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row(f"Mean hit-ratio ({label_a})", _fmt(result.mean_a))
    table.add_row(f"Mean hit-ratio ({label_b})", _fmt(result.mean_b))
    table.add_row("Mean gap (B − A)", _fmt(result.mean_gap, sign=True))
    table.add_row("Max gap (B − A)", _fmt(result.max_gap, sign=True))
    table.add_row("Samples compared", str(result.sample_count))

    return table


def print_divergence_table(
    result: DivergenceResult,
    label_a: str = "A",
    label_b: str = "B",
    console: Optional[Console] = None,
) -> None:  # pragma: no cover
    con = console or Console()
    con.print(build_divergence_table(result, label_a, label_b))
