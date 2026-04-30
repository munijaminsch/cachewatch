"""CLI entry-point: compare a tracker JSON file against a baseline JSON file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats
from cachewatch.baseline import compare_to_baseline
from cachewatch.display_baseline import print_baseline_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-baseline",
        description="Compare a recorded tracker against a baseline tracker.",
    )
    parser.add_argument("current", help="Path to current tracker JSON export.")
    parser.add_argument("baseline", help="Path to baseline tracker JSON export.")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.02,
        help="Delta tolerance to consider ratios 'on par' (default: 0.02).",
    )
    parser.add_argument("--title", default="Baseline Comparison", help="Table title.")
    return parser


def _load_tracker(path: str) -> StatsTracker:
    data = json.loads(Path(path).read_text())
    tracker = StatsTracker(max_history=len(data) + 1)
    for entry in data:
        snap_mock = type(
            "_Snap",
            (),
            {
                "stats": CacheStats(
                    hits=entry.get("hits", 0),
                    misses=entry.get("misses", 0),
                ),
                "timestamp": entry.get("timestamp", 0.0),
            },
        )()
        tracker._history.append(snap_mock)  # type: ignore[attr-defined]
    return tracker


def run(args: argparse.Namespace) -> int:
    try:
        current_tracker = _load_tracker(args.current)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading current file: {exc}", file=sys.stderr)
        return 1

    try:
        baseline_tracker = _load_tracker(args.baseline)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading baseline file: {exc}", file=sys.stderr)
        return 1

    result = compare_to_baseline(current_tracker, baseline_tracker, tolerance=args.tolerance)
    print_baseline_table(result, title=args.title)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
