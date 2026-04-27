"""CLI sub-command: report the hit-ratio trend from a saved export file."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cachewatch.stats_tracker import StatsTracker
from cachewatch.trend import analyze_trend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachewatch-trend",
        description="Analyse the hit-ratio trend from a JSON export file.",
    )
    parser.add_argument(
        "file",
        help="Path to a JSON export produced by 'cachewatch-export'.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.001,
        metavar="T",
        help="Slope threshold (hit-ratio/s) to classify as stable (default: 0.001).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the direction keyword and exit code (0=stable/improving, 1=degrading).",
    )
    return parser


def _load_tracker(path: str) -> StatsTracker:
    """Reconstruct a StatsTracker from a JSON export file."""
    from unittest.mock import MagicMock

    with open(path) as fh:
        records: List[dict] = json.load(fh)

    tracker = StatsTracker()
    for rec in records:
        snap = MagicMock()
        snap.timestamp = float(rec["timestamp"])
        snap.hit_ratio = float(rec["hit_ratio"])
        snap.stats = MagicMock()
        # Patch history to return accumulated list later via record side-effect
        tracker._history.append(snap)  # type: ignore[attr-defined]
    return tracker


def run(args: argparse.Namespace) -> int:
    try:
        tracker = _load_tracker(args.file)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = analyze_trend(tracker, stable_threshold=args.threshold)

    if result is None:
        print("Not enough data to compute trend (need at least 2 snapshots).",
              file=sys.stderr)
        return 2

    if args.quiet:
        print(result.direction)
    else:
        print(result)

    return 1 if result.direction == "degrading" else 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
