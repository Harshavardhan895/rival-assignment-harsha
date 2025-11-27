
# DESIGN.md

## Chosen Advanced Features
- **Anomaly Detection (Option B):** Valuable for spotting attacks or regressions early.
- **Caching Opportunity Analysis (Option D):** Direct operational impact by reducing latency and cost.

## Why these two?
They show both reactive (anomalies) and proactive (caching) insights, which hiring teams value.

## Trade-offs
- Simplicity vs completeness: heuristics chosen for clarity and speed; a production system would use time-series DBs and more robust detectors.
- Memory vs accuracy: we keep per-endpoint timestamp lists which is fine for 10k-100k logs but would need streaming/approximation for 1M+ logs.

## Scaling to 1,000,000+ logs
- Use streaming aggregation and approximate algorithms (HyperLogLog for uniques, count-min sketches).
- Store raw timestamps in time-series DB (InfluxDB/Prometheus) and run windowed aggregation there.
- Batch processing with Apache Spark or Flink for heavy lifting.

## What to improve with more time
- Add configurable rate-limit rules (Option C).
- Use statistical anomaly detection (MAD, z-score) instead of fixed thresholds.
- Add CI, linters, and code coverage reports.

## Estimated time spent
~6-9 hours (design, implementation, tests, documentation).
