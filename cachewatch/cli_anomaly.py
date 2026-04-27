"""CLI sub-command: detect anomalies in recorded stats."""
import argparse
import sys
from cachewatch.anomaly import AnomalyDetector
from cachewatch.stats_tracker import StatsTracker
from cachewatch.redis_collector import RedisCollector


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="cachewatch anomaly",
        description="Detect anomalies in Redis cache hit ratio.",
    )
    if parent is not None:
        parser = parent.add_parser("anomaly", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("--host", default="localhost", help="Redis host")
    parser.add_argument("--port", type=int, default=6379, help="Redis port")
    parser.add_argument("--samples", type=int, default=20, help="Number of samples to collect")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between samples")
    parser.add_argument("--drop", type=float, default=0.10, help="Drop threshold (0-1)")
    parser.add_argument("--spike", type=float, default=0.10, help="Spike threshold (0-1)")
    parser.add_argument("--flat-window", type=int, default=5, dest="flat_window")
    return parser


def run(args: argparse.Namespace) -> int:
    import time

    collector = RedisCollector(host=args.host, port=args.port)
    tracker = StatsTracker()
    detector = AnomalyDetector(
        drop_threshold=args.drop,
        spike_threshold=args.spike,
        flat_window=args.flat_window,
    )

    print(f"Collecting {args.samples} samples from {args.host}:{args.port} …")
    for _ in range(args.samples):
        try:
            snapshot = collector.collect()
            tracker.record(snapshot)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        time.sleep(args.interval)

    anomalies = detector.detect(tracker)
    if not anomalies:
        print("No anomalies detected.")
        return 0

    print(f"\nDetected {len(anomalies)} anomaly(ies):")
    for anomaly in anomalies:
        print(f"  {anomaly}")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":  # pragma: no cover
    main()
