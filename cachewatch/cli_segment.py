"""CLI command: cachewatch segment — split recorded snapshots into windows."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cachewatch.exporter import export_json
from cachewatch.segmenter import segment_by_count, segment_by_duration
from cachewatch.stats_tracker import StatsTracker


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cachewatch segment",
        description="Segment snapshot history into labeled windows.",
    )
    p.add_argument("input", help="Path to JSON snapshot file")
    mode = p.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        "--by-count",
        type=int,
        metavar="N",
        default=None,
        help="Split into segments of N snapshots each",
    )
    mode.add_argument(
        "--by-duration",
        type=float,
        metavar="SECONDS",
        default=None,
        help="Split into time windows of SECONDS width",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )
    return p


def _load_tracker(path: str) -> StatsTracker:
    from cachewatch.exporter import export_json  # noqa: F401 – reuse import path
    import json as _json
    from cachewatch.redis_collector import CacheStats

    with open(path) as fh:
        records = _json.load(fh)
    tracker = StatsTracker()
    for r in records:
        stats = CacheStats(hits=r["hits"], misses=r["misses"])
        tracker.record(stats, timestamp=r["timestamp"])
    return tracker


def run(args: argparse.Namespace) -> None:
    tracker = _load_tracker(args.input)

    if args.by_duration is not None:
        segments = segment_by_duration(tracker, window_seconds=args.by_duration)
    else:
        size = args.by_count if args.by_count is not None else 10
        segments = segment_by_count(tracker, segment_size=size)

    if args.json:
        output = [
            {
                "label": seg.label,
                "count": seg.count,
                "average_hit_ratio": seg.average_hit_ratio,
                "start_ts": seg.start_ts,
                "end_ts": seg.end_ts,
            }
            for seg in segments
        ]
        print(json.dumps(output, indent=2))
    else:
        if not segments:
            print("No segments produced.")
            return
        for seg in segments:
            print(str(seg))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
