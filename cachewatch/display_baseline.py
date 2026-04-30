"""Rich display helpers for baseline comparison results."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from cachewatch.baseline import BaselineResult

_VERDICT_STYLE: dict[str, str] = {
    "above": "bold green",
    "below": "bold red",
    "on_par": "bold yellow",
    "unknown": "dim",
}


def build_baseline_table(result: BaselineResult, title: str = "Baseline Comparison") -> Table:
    """Build a Rich :class:`Table` summarising the baseline comparison."""
    table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    def _fmt(v: float | None) -> str:
        return f"{v:.3f}" if v is not None else "N/A"

    verdict_style = _VERDICT_STYLE.get(result.verdict, "")

    delta_str = "N/A"
    if result.delta is not None:
        sign = "+" if result.delta >= 0 else ""
        delta_str = f"{sign}{result.delta:.3f}"

    table.add_row("Baseline Ratio", _fmt(result.baseline_ratio))
    table.add_row("Current Ratio", _fmt(result.current_ratio))
    table.add_row("Delta", delta_str)
    table.add_row("Verdict", f"[{verdict_style}]{result.verdict}[/{verdict_style}]")

    return table


def print_baseline_table(result: BaselineResult, title: str = "Baseline Comparison") -> None:
    """Print the baseline comparison table to stdout."""
    console = Console()
    console.print(build_baseline_table(result, title=title))
