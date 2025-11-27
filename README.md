
# Rival.io - Internship Assignment (Harsha Vardhan)

This repository contains a production-quality solution for the Rival.io take-home assignment.

**Main deliverable:** `analyze_api_logs(logs)` implemented in `function.py`.

**Advanced features implemented:** 
- Anomaly Detection (Option B)
- Caching Opportunity Analysis (Option D)

## How to run
Requirements: Python 3.9+

1. (Optional) Create virtualenv:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run tests:
   ```
   python -m unittest discover -v
   ```

## Project structure
See DESIGN.md for design decisions.

## Usage example
```py
from function import analyze_api_logs
import json
logs = json.load(open('tests/test_data_sample_small.json'))
out = analyze_api_logs(logs)
print(json.dumps(out, indent=2))
```

## Complexity
- Time: O(N) for single-pass aggregations and O(N log N) when sorting per-endpoint timestamps for anomaly windows.
- Space: O(E + U) where E=endpoints observed, U=unique users.
"# rival-assignment-harsha" 
