# Performance Testing

Coal LIMS-ийн гүйцэтгэлийн тестүүд.

## k6 (Recommended)

### Installation

```bash
# Windows (winget)
winget install k6

# macOS
brew install k6

# Docker
docker pull grafana/k6
```

### Running Tests

```bash
# Smoke test (quick validation)
k6 run performance/smoke_test.js

# Load test (normal load)
k6 run performance/load_test.js

# Stress test (find limits)
k6 run performance/stress_test.js

# Custom base URL
k6 run -e BASE_URL=http://production-server:5000 performance/load_test.js
```

### Test Types

| Test | Purpose | Duration | Users |
|------|---------|----------|-------|
| smoke_test.js | Quick validation | 30s | 1 |
| load_test.js | Normal load | 4m | 10-20 |
| stress_test.js | Find limits | 11m | 50-200 |

## Locust (Python Alternative)

### Installation

```bash
pip install locust
```

### Running Tests

```bash
# Start web UI
locust -f performance/locustfile.py --host=http://localhost:5000

# Headless mode
locust -f performance/locustfile.py --host=http://localhost:5000 \
    --headless -u 10 -r 2 -t 1m
```

Open http://localhost:8089 for the web interface.

## Thresholds

| Metric | Target |
|--------|--------|
| Response time (p95) | < 2000ms |
| Error rate | < 10% |
| Login time (p95) | < 3000ms |
| API response (p95) | < 1000ms |

## Results

Results are saved to `performance/results.json` after k6 runs.
