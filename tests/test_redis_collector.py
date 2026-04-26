"""Unit tests for RedisCollector."""

import pytest
from unittest.mock import MagicMock, patch

from cachewatch.redis_collector import CacheStats, RedisCollector


class TestCacheStats:
    def test_hit_ratio_zero_when_no_requests(self):
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_ratio == 0.0
        assert stats.miss_ratio == 1.0

    def test_hit_ratio_calculation(self):
        stats = CacheStats(hits=75, misses=25)
        assert stats.hit_ratio == pytest.approx(0.75)
        assert stats.miss_ratio == pytest.approx(0.25)

    def test_total(self):
        stats = CacheStats(hits=10, misses=5)
        assert stats.total == 15


class TestRedisCollector:
    @patch("cachewatch.redis_collector.redis.Redis")
    def test_ping_returns_true_on_success(self, mock_redis_cls):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_cls.return_value = mock_client

        collector = RedisCollector()
        assert collector.ping() is True

    @patch("cachewatch.redis_collector.redis.Redis")
    def test_ping_returns_false_on_error(self, mock_redis_cls):
        import redis as redis_lib
        mock_client = MagicMock()
        mock_client.ping.side_effect = redis_lib.RedisError("connection refused")
        mock_redis_cls.return_value = mock_client

        collector = RedisCollector()
        assert collector.ping() is False

    @patch("cachewatch.redis_collector.redis.Redis")
    def test_collect_returns_cache_stats(self, mock_redis_cls):
        mock_client = MagicMock()
        mock_client.info.return_value = {"keyspace_hits": "200", "keyspace_misses": "50"}
        mock_redis_cls.return_value = mock_client

        collector = RedisCollector()
        stats = collector.collect()

        assert stats.hits == 200
        assert stats.misses == 50
        assert stats.total == 250

    @patch("cachewatch.redis_collector.redis.Redis")
    def test_collect_raises_on_redis_error(self, mock_redis_cls):
        import redis as redis_lib
        mock_client = MagicMock()
        mock_client.info.side_effect = redis_lib.RedisError("timeout")
        mock_redis_cls.return_value = mock_client

        collector = RedisCollector()
        with pytest.raises(ConnectionError, match="Failed to collect Redis stats"):
            collector.collect()
