"""CLI sub-command: generate a summary report from recorded history."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from typing import List

from cachewatch.redis_collector import CacheStats, RedisCollector
from cachewatch.stats_tracker import StatsTracker
from cachewatch.snapshot_filter import (
    average_hit_ratio,
    filter_last_n_seconds,
    peak_hit_ratio,
    trough_hit_ratio,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-report",
        description="Print a summary report of cache hit/miss statistics.",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Time window in seconds to include in the report (default: 60).",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10,
        metavar="N",
        help="Number of samples to collect before reporting (default: 10).",
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis connection URL (default: redis://localhost:6379).",
    )
    return parser


def _print_report(snapshots: List[CacheStats], window: float) -> None:
    """Print a formatted summary report to stdout.

    Args:
        snapshots: List of CacheStats snapshots within the reporting window.
        window: The time window in seconds that the report covers.
    """
    count = len(snapshots)
    avg = average_hit_ratio(snapshots)
    peak = peak_hit_ratio(snapshots)
    trough = trough_hit_ratio(snapshots)

    print(f"\n=== CacheWatch Report (last {window:.0f}s) ===")
    print(f"  Snapshots in window : {count}")
    if avg is not None:
        print(f"  Average hit ratio   : {avg:.2%}")
        print(f"  Peak hit ratio      : {peak:.2%}")
        print(f"  Trough hit ratio    : {trough:.2%}")
    else:
        print("  No data in the selected window.")
    print()


def run(args: argparse.Namespace) -> int:
    """Execute the report sub-command.

    Collects *args.samples* snapshots from Redis, filters them to the
    requested time window, and prints a summary report.

    Returns:
        0 on success, 1 if any collection error occurs.
    """
    collector = RedisCollector(args.redis_url)
    tracker = StatsTracker()

    print(f"Collecting {args.samples} samples from {args.redis_url} …")
    for i in range(args.samples):
        try:
            stats = collector.collect()
            tracker.record(stats)
        except Exception as exc:  # noqa: BLE001
            print(
                f"Error collecting sample {i + 1}/{args.samples}: {exc}",
                file=sys.stderr,
            )
            return 1

    snapshots = filter_last_n_seconds(tracker, seconds=args.window)
    _print_report(snapshots, args.window)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
