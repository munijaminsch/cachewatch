"""CLI entry-point: cachewatch volatility."""
from __future__ import annotations

import argparse
import json
import sys

from cachewatch.exporter import export_json
from cachewatch.stats_tracker import StatsTracker
from cachewatch.volatility import compute_volatility
from cachewatch.display_volatility import print_volatility_table


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cachewatch volatility",
        description="Show hit-ratio volatility for a recorded session.",
    )
    p.add_argument("file", help="JSON export file produced by cachewatch export")
    p.add_argument(
        "--last-n",
        type=int,
        default=None,
        metavar="N",
        help="Only consider the last N snapshots (default: all)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output result as JSON instead of a table",
    )
    return p


def _load_tracker(path: str) -> StatsTracker:
    with open(path) as fh:
        records = json.load(fh)
    tracker = StatsTracker()
    for rec in records:
        from cachewatch.redis_collector import CacheStats
        stats = CacheStats(hits=rec["hits"], misses=rec["misses"])
        tracker.record(stats, timestamp=rec["timestamp"])
    return tracker


def run(args: argparse.Namespace) -> int:
    try:
        tracker = _load_tracker(args.file)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"Error loading file: {exc}", file=sys.stderr)
        return 1

    result = compute_volatility(tracker, last_n=args.last_n)
    if result is None:
        print("No data available.", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "window": result.window,
            "std_dev": result.std_dev,
            "mean": result.mean,
            "min_ratio": result.min_ratio,
            "max_ratio": result.max_ratio,
        }
        print(json.dumps(payload, indent=2))
    else:
        print_volatility_table(result)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
