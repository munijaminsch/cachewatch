"""CLI entry-point for the cache health-score command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cachewatch.exporter import export_json
from cachewatch.scorer import compute_health_score
from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import CacheStats


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cachewatch-score",
        description="Compute a composite health score from a recorded session.",
    )
    p.add_argument(
        "input",
        metavar="FILE",
        help="JSON file produced by 'cachewatch export' (use '-' for stdin).",
    )
    p.add_argument(
        "--trend-weight",
        type=float,
        default=0.2,
        metavar="W",
        help="Weight (0-1) given to trend direction in the score (default: 0.2).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output result as JSON.",
    )
    return p


def _load_tracker(path: str) -> StatsTracker:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")

    records = json.loads(raw)
    tracker = StatsTracker()
    for rec in records:
        from datetime import datetime, timezone
        ts = datetime.fromisoformat(rec["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        tracker.record(
            CacheStats(
                hits=rec["hits"],
                misses=rec["misses"],
                timestamp=ts,
            )
        )
    return tracker


def run(args: argparse.Namespace) -> int:
    tracker = _load_tracker(args.input)
    result = compute_health_score(tracker, trend_weight=args.trend_weight)

    if result is None:
        print("No data available to compute a health score.", file=sys.stderr)
        return 1

    if args.as_json:
        out = {
            "score": result.score,
            "grade": result.grade,
            "avg_hit_ratio": result.avg_hit_ratio,
            "trough": result.trough,
            "trend_slope": result.trend_slope,
        }
        print(json.dumps(out, indent=2))
    else:
        print(str(result))

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
