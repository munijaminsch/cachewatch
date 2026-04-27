"""CLI entry point for comparing two time-window hit ratios."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cachewatch.stats_tracker import StatsTracker
from cachewatch.exporter import export_json
from cachewatch.comparator import compare_windows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-compare",
        description="Compare hit ratios between two time windows.",
    )
    parser.add_argument("--input", required=True, help="JSON export file to read snapshots from.")
    parser.add_argument("--start-a", type=float, required=True, metavar="TS", help="Start of window A (unix timestamp).")
    parser.add_argument("--end-a", type=float, required=True, metavar="TS", help="End of window A (unix timestamp).")
    parser.add_argument("--start-b", type=float, required=True, metavar="TS", help="Start of window B (unix timestamp).")
    parser.add_argument("--end-b", type=float, required=True, metavar="TS", help="End of window B (unix timestamp).")
    parser.add_argument("--json", action="store_true", help="Output result as JSON.")
    return parser


def _load_tracker(path: str) -> StatsTracker:
    """Reconstruct a StatsTracker from a JSON export file."""
    from cachewatch.redis_collector import CacheStats
    from cachewatch.stats_tracker import Snapshot  # type: ignore
    from unittest.mock import MagicMock

    with open(path) as fh:
        records = json.load(fh)

    tracker = StatsTracker()
    for r in records:
        snap = MagicMock()
        snap.timestamp = r["timestamp"]
        snap.stats = CacheStats(hits=r["hits"], misses=r["misses"])
        tracker._history.append(snap)
    return tracker


def run(args: argparse.Namespace) -> int:
    try:
        tracker = _load_tracker(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error loading input file: {exc}", file=sys.stderr)
        return 1

    result = compare_windows(
        tracker,
        args.start_a, args.end_a,
        args.start_b, args.end_b,
    )

    if args.json:
        out = {
            "window_a_avg": result.window_a_avg,
            "window_b_avg": result.window_b_avg,
            "delta": result.delta,
            "improved": result.improved,
        }
        print(json.dumps(out, indent=2))
    else:
        print(str(result))

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))
