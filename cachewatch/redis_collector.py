"""Redis stats collector module for cachewatch."""

import redis
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CacheStats:
    """Snapshot of Redis cache hit/miss statistics."""
    hits: int = 0
    misses: int = 0
    timestamp: float = 0.0

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.hits / self.total

    @property
    def miss_ratio(self) -> float:
        return 1.0 - self.hit_ratio


class RedisCollector:
    """Collects keyspace hit/miss stats from a Redis instance."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_connect_timeout=3,
            decode_responses=True,
        )

    def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self._client.ping()
        except redis.RedisError:
            return False

    def collect(self) -> CacheStats:
        """Fetch current keyspace_hits and keyspace_misses from Redis INFO."""
        import time
        try:
            info = self._client.info("stats")
            return CacheStats(
                hits=int(info.get("keyspace_hits", 0)),
                misses=int(info.get("keyspace_misses", 0)),
                timestamp=time.time(),
            )
        except redis.RedisError as exc:
            raise ConnectionError(f"Failed to collect Redis stats: {exc}") from exc

    def close(self) -> None:
        """Close the underlying Redis connection."""
        self._client.close()
