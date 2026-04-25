# cachewatch

> A CLI tool to monitor and visualize Redis cache hit/miss ratios in real time.

---

## Installation

```bash
pip install cachewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/cachewatch.git
cd cachewatch && pip install -e .
```

---

## Usage

Connect to a local Redis instance and start monitoring:

```bash
cachewatch --host localhost --port 6379
```

Connect to a remote instance with a refresh interval:

```bash
cachewatch --host redis.example.com --port 6379 --interval 2
```

**Example output:**

```
┌─────────────────────────────────────┐
│         CacheWatch  v0.1.0          │
│  Host: localhost:6379               │
│  Hits:    18,432   ████████████░░░  │
│  Misses:   3,201   ███░░░░░░░░░░░░  │
│  Ratio:    85.2%                    │
└─────────────────────────────────────┘
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `localhost` | Redis host address |
| `--port` | `6379` | Redis port |
| `--interval` | `1` | Refresh interval in seconds |
| `--db` | `0` | Redis database index |

---

## Requirements

- Python 3.8+
- Redis 5.0+

---

## License

This project is licensed under the [MIT License](LICENSE).