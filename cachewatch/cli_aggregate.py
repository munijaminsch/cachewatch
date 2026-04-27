"""CLI entry point for displaying aggregated bucket summaries."""

import argparse
import json
import sys

from cachewatch.aggregator import aggregate_by_seconds
from cachewatch.exporter import export_json
from cachewatch.stats_tracker import StatsTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-aggregate",
        description="Aggregate Redis cache stats into time buckets.",
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to a JSON snapshot file produced by cachewatch-export.",
    )
    parser.add_argument(
        "--bucket",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _load_tracker(path: str) -> StatsTracker:
    """Load snapshots from a JSON export file into a StatsTracker."""
    from cachewatch.redis_collector import CacheStats
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    with open(path) as fh:
        records = json.load(fh)

    tracker = StatsTracker()
    for rec in records:
        snap = MagicMock()
        snap.timestamp = datetime.fromisoformat(rec["timestamp"])
        snap.stats = CacheStats(hits=rec["hits"], misses=rec["misses"])
        # Directly inject into internal history
        tracker._history.append(snap)  # type: ignore[attr-defined]
    return tracker


def run(args: argparse.Namespace) -> None:
    try:
        tracker = _load_tracker(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error loading input file: {exc}", file=sys.stderr)
        sys.exit(1)

    buckets = aggregate_by_seconds(tracker, bucket_size=args.bucket)

    if not buckets:
        print("No data to aggregate.")
        return

    if args.format == "json":
        output = [
            {
                "bucket_start": b.bucket_start.isoformat(),
                "bucket_end": b.bucket_end.isoformat(),
                "avg_hit_ratio": round(b.avg_hit_ratio, 4),
                "min_hit_ratio": round(b.min_hit_ratio, 4),
                "max_hit_ratio": round(b.max_hit_ratio, 4),
                "total_hits": b.total_hits,
                "total_misses": b.total_misses,
                "sample_count": b.sample_count,
            }
            for b in buckets
        ]
        print(json.dumps(output, indent=2))
    else:
        for bucket in buckets:
            print(bucket)


def main() -> None:
    parser = build_parser()
    run(parser.parse_args())


if __name__ == "__main__":
    main()
