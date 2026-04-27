"""CLI sub-command: cachewatch export — dump collected stats to a file."""

from __future__ import annotations

import argparse
import sys

from cachewatch.exporter import export_csv, export_json, save_to_file
from cachewatch.redis_collector import RedisCollector
from cachewatch.stats_tracker import StatsTracker


FORMATS = ("json", "csv")


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    """Return (or attach) the argument parser for the export sub-command."""
    kwargs = dict(
        description="Collect Redis cache stats and export them to a file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if subparsers is not None:
        parser = subparsers.add_parser("export", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("--host", default="127.0.0.1", help="Redis host")
    parser.add_argument("--port", type=int, default=6379, help="Redis port")
    parser.add_argument("--samples", type=int, default=10, help="Number of samples to collect")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between samples")
    parser.add_argument("--format", choices=FORMATS, default="json", dest="fmt", help="Output format")
    parser.add_argument("--output", "-o", required=True, help="Destination file path")
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the export command; returns an exit code."""
    import time

    tracker = StatsTracker(maxlen=args.samples)
    collector = RedisCollector(host=args.host, port=args.port)

    print(f"Collecting {args.samples} samples from {args.host}:{args.port} …", file=sys.stderr)
    for i in range(args.samples):
        try:
            snapshot = collector.collect()
            tracker.record(snapshot)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] sample {i + 1} failed: {exc}", file=sys.stderr)
        if i < args.samples - 1:
            time.sleep(args.interval)

    if args.fmt == "json":
        content = export_json(tracker)
    else:
        content = export_csv(tracker)

    if not content:
        print("No data collected — nothing written.", file=sys.stderr)
        return 1

    save_to_file(content, args.output)
    print(f"Exported {len(tracker.history())} records to {args.output} ({args.fmt}).", file=sys.stderr)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
