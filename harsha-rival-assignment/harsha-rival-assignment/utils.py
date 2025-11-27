
"""Helper utilities (validation, sample data generators)."""
import random, uuid
from datetime import datetime, timedelta, timezone

def generate_sample_logs(n=10000, start=None):
    """Generate n synthetic logs for performance testing."""
    if start is None:
        start = datetime(2025,1,15,10,0,0,tzinfo=timezone.utc)
    endpoints = ["/api/users","/api/payments","/api/reports","/api/search","/api/notifications"]
    methods = ["GET","POST","PUT","DELETE"]
    logs = []
    for i in range(n):
        ts = start + timedelta(seconds=i*2 % 3600)
        ep = random.choice(endpoints)
        method = random.choices(methods, weights=[0.7,0.2,0.05,0.05])[0]
        rt = int(abs(random.gauss(200, 300)))  # some will be > threshold
        status = 200 if random.random() > 0.05 else random.choice([400,404,500])
        user = f"user_{random.randint(1,200)}"
        logs.append({
            "timestamp": ts.isoformat().replace("+00:00","Z"),
            "endpoint": ep,
            "method": method,
            "response_time_ms": rt,
            "status_code": status,
            "user_id": user,
            "request_size_bytes": random.randint(100,5000),
            "response_size_bytes": random.randint(100,20000)
        })
    return logs
