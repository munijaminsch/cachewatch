"""Rich display helpers for segmenter output."""
from __future__ import annotations

from typing import List

from cachewatch.display import _ratio_color, format_ratio
from cachewatch.segmenter import Segment

try:
    from rich.table import Table
    from rich.console import Console
    from rich import box as rich_box
    _RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RICH_AVAILABLE = False


def build_segment_table(segments: List[Segment]) -> "Table":
    """Return a Rich Table summarising the provided segments."""
    if not _RICH_AVAILABLE:  # pragma: no cover
        raise RuntimeError("rich is required for table display")

    table = Table(
        title="Cache Segments",
        box=rich_box.SIMPLE_HEAD,
        show_lines=False,
    )
    table.add_column("Label", style="bold cyan", no_wrap=True)
    table.add_column("Snapshots", justify="right")
    table.add_column("Avg Hit Ratio", justify="right")
    table.add_column("Start TS", justify="right")
    table.add_column("End TS", justify="right")

    for seg in segments:
        ratio = seg.average_hit_ratio
        ratio_str = format_ratio(ratio) if ratio is not None else "n/a"
        color = _ratio_color(ratio) if ratio is not None else "white"
        table.add_row(
            seg.label,
            str(seg.count),
            f"[{color}]{ratio_str}[/{color}]",
            f"{seg.start_ts:.1f}" if seg.start_ts is not None else "-",
            f"{seg.end_ts:.1f}" if seg.end_ts is not None else "-",
        )
    return table


def print_segment_table(segments: List[Segment]) -> None:
    """Print the segment summary table to stdout."""
    if not _RICH_AVAILABLE:  # pragma: no cover
        for seg in segments:
            print(str(seg))
        return
    console = Console()
    table = build_segment_table(segments)
    console.print(table)
