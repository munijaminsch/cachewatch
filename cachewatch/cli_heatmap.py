"""CLI entry point for the cachewatch heatmap command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from cachewatch.exporter import export_json
from cachewatch.heatmap import build_heatmap
from cachewatch.display_heatmap import print_heatmap_table
from cachewatch.stats_tracker import StatsTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-heatmap",
        description="Display a hit-ratio heatmap bucketed over time.",
    )
    parser.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="Path to a JSON snapshot file produced by cachewatch export.",
    )
    parser.add_argument(
        "--bucket",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    parser.add_argument(
        "--title",
        default="Cache Hit Ratio Heatmap",
        help="Title shown above the heatmap table.",
    )
    return parser


def _load_tracker(path: str) -> Optional[StatsTracker]:
    try:
        with open(path) as fh:
            records = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading {path!r}: {exc}", file=sys.stderr)
        return None

    tracker = StatsTracker()
    for rec in records:
        from cachewatch.redis_collector import CacheStats
        from cachewatch.stats_tracker import Snapshot

        stats = CacheStats(hits=rec["hits"], misses=rec["misses"])
        snap = Snapshot(stats=stats, timestamp=rec["timestamp"])
        tracker._history.append(snap)  # noqa: SLF001
    return tracker


def run(args: argparse.Namespace) -> int:
    tracker = _load_tracker(args.file)
    if tracker is None:
        return 1
    rows = build_heatmap(tracker, bucket_seconds=args.bucket)
    print_heatmap_table(rows, title=args.title)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
