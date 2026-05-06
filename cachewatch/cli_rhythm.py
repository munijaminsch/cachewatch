"""CLI entry point: cachewatch rhythm — detect periodic patterns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cachewatch.exporter import export_json
from cachewatch.stats_tracker import StatsTracker
from cachewatch.rhythm import detect_rhythm
from cachewatch.display_rhythm import print_rhythm_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch rhythm",
        description="Detect periodic rhythms in cached hit-ratio data.",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        required=True,
        help="Path to a JSON export file produced by cachewatch export.",
    )
    parser.add_argument(
        "--min-period",
        type=int,
        default=2,
        metavar="N",
        help="Minimum lag (in snapshots) to consider as a period (default: 2).",
    )
    parser.add_argument(
        "--max-period",
        type=int,
        default=None,
        metavar="N",
        help="Maximum lag to consider (default: half the series length).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON instead of a Rich table.",
    )
    return parser


def _load_tracker(path: str) -> StatsTracker:
    raw = json.loads(Path(path).read_text())
    tracker = StatsTracker()
    for entry in raw:
        from cachewatch.redis_collector import CacheStats
        from cachewatch.stats_tracker import Snapshot
        stats = CacheStats(hits=entry["hits"], misses=entry["misses"])
        snap = Snapshot(stats=stats, timestamp=entry["timestamp"])
        tracker._history.append(snap)  # type: ignore[attr-defined]
    return tracker


def run(args: argparse.Namespace) -> int:
    try:
        tracker = _load_tracker(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error loading input file: {exc}", file=sys.stderr)
        return 1

    result = detect_rhythm(
        tracker,
        min_period=args.min_period,
        max_period=args.max_period,
    )

    if args.json:
        if result is None:
            print(json.dumps({"rhythm": None}))
        else:
            print(json.dumps({
                "period_seconds": result.period_seconds,
                "strength": result.strength,
                "sample_count": result.sample_count,
                "mean_ratio": result.mean_ratio,
            }))
    else:
        print_rhythm_table(result)

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run(build_parser().parse_args()))
