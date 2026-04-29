"""CLI entry point for outlier detection."""
from __future__ import annotations

import argparse
import json
import sys

from cachewatch.exporter import export_json
from cachewatch.outlier import detect_outliers
from cachewatch.display_outlier import print_outlier_table
from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-outlier",
        description="Detect outlier snapshots by z-score of hit ratio.",
    )
    parser.add_argument(
        "file",
        help="JSON export file produced by cachewatch-export.",
    )
    parser.add_argument(
        "--z-threshold",
        type=float,
        default=2.0,
        metavar="Z",
        help="Z-score threshold for outlier classification (default: 2.0).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON instead of a table.",
    )
    return parser


def _load_tracker(path: str) -> StatsTracker:
    with open(path) as fh:
        records = json.load(fh)
    tracker = StatsTracker()
    for rec in records:
        snap = CacheStats(
            hits=rec["hits"],
            misses=rec["misses"],
            timestamp=rec["timestamp"],
        )
        tracker.record(snap)
    return tracker


def run(args: argparse.Namespace) -> None:
    tracker = _load_tracker(args.file)
    outliers = detect_outliers(tracker, z_threshold=args.z_threshold)

    if args.as_json:
        data = [
            {
                "timestamp": r.timestamp,
                "hit_ratio": r.hit_ratio,
                "mean": r.mean,
                "std_dev": r.std_dev,
                "z_score": r.z_score,
            }
            for r in outliers
        ]
        print(json.dumps(data, indent=2))
    else:
        print_outlier_table(outliers)


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":  # pragma: no cover
    main()
