"""Display module for rendering cache statistics in the terminal.

Provides a rich-based UI for visualizing Redis cache hit/miss ratios,
delta changes, and historical trends in real time.
"""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from cachewatch.stats_tracker import StatsDelta, StatsSnapshot

console = Console()


def format_ratio(ratio: float) -> Text:
    """Format a ratio as a colored percentage string.

    Green for high hit ratios, yellow for moderate, red for low.
    """
    percentage = ratio * 100
    if percentage >= 80:
        color = "green"
    elif percentage >= 50:
        color = "yellow"
    else:
        color = "red"
    return Text(f"{percentage:.1f}%", style=color)


def format_delta(value: Optional[float], label: str = "") -> Text:
    """Format a delta value with directional indicator and color."""
    if value is None:
        return Text("N/A", style="dim")
    sign = "+" if value >= 0 else ""
    color = "green" if value >= 0 else "red"
    return Text(f"{sign}{value:.1f} {label}".strip(), style=color)


def build_stats_table(snapshot: StatsSnapshot, delta: Optional[StatsDelta]) -> Table:
    """Build a Rich table showing current cache statistics and deltas."""
    table = Table(title="Cache Statistics", expand=True, show_lines=True)
    table.add_column("Metric", style="bold cyan", width=20)
    table.add_column("Current", justify="right", width=15)
    table.add_column("Change / sec", justify="right", width=15)

    stats = snapshot.stats

    table.add_row(
        "Hit Ratio",
        format_ratio(stats.hit_ratio),
        format_delta(delta.hit_ratio_delta if delta else None),
    )
    table.add_row(
        "Miss Ratio",
        format_ratio(stats.miss_ratio),
        format_delta(delta.miss_ratio_delta if delta else None),
    )
    table.add_row(
        "Total Requests",
        str(stats.total),
        format_delta(delta.requests_per_second if delta else None, "req/s"),
    )
    table.add_row(
        "Hits",
        str(stats.hits),
        "",
    )
    table.add_row(
        "Misses",
        str(stats.misses),
        "",
    )

    return table


def build_hit_ratio_bar(snapshot: StatsSnapshot) -> Panel:
    """Build a visual progress bar representing the current hit ratio."""
    ratio = snapshot.stats.hit_ratio

    progress = Progress(
        TextColumn("[bold]Hit Ratio[/bold]"),
        BarColumn(bar_width=50),
        TextColumn("{task.percentage:.1f}%"),
    )
    task = progress.add_task("hit", total=100, completed=ratio * 100)
    # Silence unused variable warning — task id is needed to register the task
    _ = task

    color = "green" if ratio >= 0.8 else "yellow" if ratio >= 0.5 else "red"
    return Panel(progress, border_style=color, padding=(0, 1))


def build_header(snapshot: StatsSnapshot) -> Panel:
    """Build a header panel showing the Redis host and timestamp."""
    ts = datetime.fromtimestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    host = snapshot.redis_host
    header_text = Text.assemble(
        ("CacheWatch ", "bold magenta"),
        ("\u2014 ", "dim"),
        (f"Redis: {host}", "cyan"),
        ("  |", "dim"),
        (f"  {ts}", "white"),
    )
    return Panel(header_text, style="bold", padding=(0, 1))


def render_snapshot(
    snapshot: StatsSnapshot,
    delta: Optional[StatsDelta] = None,
) -> Layout:
    """Compose a full terminal layout from a stats snapshot and optional delta."""
    layout = Layout()
    layout.split_column(
        Layout(build_header(snapshot), name="header", size=3),
        Layout(build_hit_ratio_bar(snapshot), name="bar", size=4),
        Layout(build_stats_table(snapshot, delta), name="table"),
    )
    return layout


def print_snapshot(snapshot: StatsSnapshot, delta: Optional[StatsDelta] = None) -> None:
    """Print a single snapshot to the console (non-live mode)."""
    console.print(render_snapshot(snapshot, delta))
