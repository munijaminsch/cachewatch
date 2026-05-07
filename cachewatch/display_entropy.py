"""Rich display helpers for :class:`~cachewatch.entropy.EntropyResult`."""
from __future__ import annotations

from typing import Optional

from rich.table import Table
from rich import print as rprint

from cachewatch.entropy import EntropyResult


def _fmt(value: Optional[float], decimals: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _bar(normalized: float, width: int = 20) -> str:
    """Return a simple ASCII progress bar for a 0-1 normalised value."""
    filled = round(normalized * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def build_entropy_table(result: EntropyResult) -> Table:
    """Build a :class:`rich.table.Table` summarising *result*."""
    table = Table(title="Hit-Ratio Entropy", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim", min_width=18)
    table.add_column("Value", justify="right")

    table.add_row("Entropy (nats)", _fmt(result.entropy))
    table.add_row("Max Entropy (nats)", _fmt(result.max_entropy))
    table.add_row(
        "Normalised",
        f"{result.normalized * 100:.1f}%  {_bar(result.normalized)}",
    )
    table.add_row("Sample Size", str(result.sample_size))

    # Bucket distribution sub-table
    buckets = len(result.bucket_counts)
    step = 1.0 / buckets
    dist_rows = []
    for i, count in enumerate(result.bucket_counts):
        lo = f"{i * step:.1f}"
        hi = f"{(i + 1) * step:.1f}"
        dist_rows.append((f"[{lo}, {hi})", str(count)))

    table.add_section()
    table.add_row("[bold]Bucket[/bold]", "[bold]Count[/bold]")
    for label, cnt in dist_rows:
        table.add_row(label, cnt)

    return table


def print_entropy_table(result: EntropyResult) -> None:
    """Print the entropy table to stdout using Rich."""
    rprint(build_entropy_table(result))
