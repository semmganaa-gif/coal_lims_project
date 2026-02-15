# Performance Testing

This document has been consolidated into the comprehensive performance guide.

See **[Performance & Optimization Guide](Performance_Optimization_Guide.md)** -- specifically:

- **Section 4: Load Testing** -- k6 setup, Locust setup, test scripts, and baseline targets
- **Section 4.3: Baseline Performance Targets** -- response time, throughput, and error rate thresholds

The load testing scripts remain in the `performance/` directory:

| Script | Command |
|--------|---------|
| Smoke test | `k6 run performance/smoke_test.js` |
| Load test | `k6 run performance/load_test.js` |
| Stress test | `k6 run performance/stress_test.js` |
| Locust | `locust -f performance/locustfile.py --host=http://localhost:5000` |
