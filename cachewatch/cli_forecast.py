"""CLI entry point: cachewatch forecast — predict future hit ratio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cachewatch.exporter import export_json
from cachewatch.forecast import forecast_hit_ratio
from cachewatch.stats_tracker import StatsTracker
from cachewatch.exporter import _snapshot_to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch forecast",
        description="Predict future Redis hit ratio using linear trend.",
    )
    parser.add_argument(
        "file",
        help="Path to a JSON snapshot file produced by 'cachewatch export'.",
    )
    parser.add_argument(
        "--ahead",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="How many seconds into the future to forecast (default: 60).",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=10,
        metavar="N",
        help="Number of recent snapshots used for slope calculation (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output result as JSON.",
    )
    return parser


def _load_tracker(path: str) -> StatsTracker:
    from cachewatch.redis_collector import CacheStats

    raw = json.loads(Path(path).read_text())
    tracker = StatsTracker()
    for entry in raw:
        tracker.record(
            CacheStats(
                hits=entry["hits"],
                misses=entry["misses"],
                timestamp=entry["timestamp"],
            )
        )
    return tracker


def run(args: argparse.Namespace) -> int:
    tracker = _load_tracker(args.file)
    result = forecast_hit_ratio(tracker, seconds_ahead=args.ahead, window=args.window)

    if result is None:
        print("Not enough data to generate a forecast (need at least 2 snapshots).", file=sys.stderr)
        return 1

    if args.output_json:
        print(
            json.dumps({
                "seconds_ahead": result.seconds_ahead,
                "current_ratio": result.current_ratio,
                "predicted_ratio": result.predicted_ratio,
                "slope": result.slope,
            })
        )
    else:
        print(result)

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
