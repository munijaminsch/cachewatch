"""Rich table display for ranker results."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from cachewatch.display import _ratio_color
from cachewatch.ranker import RankEntry


def build_rank_table(entries: List[RankEntry], title: str = "Tracker Rankings") -> Table:
    """Build a Rich table from a list of RankEntry objects."""
    table = Table(title=title, show_lines=False)
    table.add_column("Rank", style="bold", justify="right", width=6)
    table.add_column("Name", style="cyan")
    table.add_column("Avg Hit Ratio", justify="right")

    for entry in entries:
        rank_str = f"#{entry.rank}"
        if entry.avg_hit_ratio is not None:
            color = _ratio_color(entry.avg_hit_ratio)
            ratio_str = f"[{color}]{entry.avg_hit_ratio:.2%}[/{color}]"
        else:
            ratio_str = "[dim]N/A[/dim]"
        table.add_row(rank_str, entry.name, ratio_str)

    return table


def print_rank_table(entries: List[RankEntry], title: str = "Tracker Rankings") -> None:
    """Print the rank table to stdout."""
    console = Console()
    table = build_rank_table(entries, title=title)
    console.print(table)
