"""Export cache stats snapshots to various output formats."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


def _snapshot_to_dict(snapshot) -> dict:
    """Convert a CacheStats snapshot to a serialisable dict."""
    return {
        "timestamp": snapshot.timestamp.isoformat() if hasattr(snapshot, "timestamp") else datetime.utcnow().isoformat(),
        "hits": snapshot.hits,
        "misses": snapshot.misses,
        "total": snapshot.total,
        "hit_ratio": round(snapshot.hit_ratio, 4),
        "miss_ratio": round(snapshot.miss_ratio, 4),
    }


def export_json(tracker: StatsTracker, *, indent: int = 2) -> str:
    """Return the full history as a JSON string."""
    records = [_snapshot_to_dict(s) for s in tracker.history()]
    return json.dumps(records, indent=indent)


def export_csv(tracker: StatsTracker) -> str:
    """Return the full history as a CSV string."""
    snapshots = tracker.history()
    if not snapshots:
        return ""

    fieldnames = ["timestamp", "hits", "misses", "total", "hit_ratio", "miss_ratio"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for snapshot in snapshots:
        writer.writerow(_snapshot_to_dict(snapshot))
    return buf.getvalue()


def export_latest_json(tracker: StatsTracker) -> Optional[str]:
    """Return only the latest snapshot as a JSON string, or None if empty."""
    latest = tracker.latest()
    if latest is None:
        return None
    return json.dumps(_snapshot_to_dict(latest), indent=2)


def save_to_file(content: str, path: str) -> None:
    """Write exported content to a file on disk."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
