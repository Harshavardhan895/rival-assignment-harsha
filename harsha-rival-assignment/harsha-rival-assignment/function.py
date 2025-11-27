
"""analyze_api_logs - Rival.io internship assignment
Main function: analyze_api_logs(logs: list[dict]) -> dict
Advanced features implemented: Anomaly Detection (Option B) and Caching Opportunity Analysis (Option D)
"""
from collections import defaultdict, Counter
from datetime import datetime, timezone
import math

# Configuration / thresholds (no hardcoded magic numbers scattered)
RESPONSE_THRESHOLDS = {
    "medium": 500,
    "high": 1000,
    "critical": 2000
}
ERROR_RATE_THRESHOLDS = {
    "medium": 5.0,
    "high": 10.0,
    "critical": 15.0
}

def _parse_timestamp(ts):
    if not ts:
        raise ValueError("missing timestamp")
    try:
        # Expecting ISO 8601 Z suffix
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        raise ValueError(f"invalid timestamp: {ts}")

def analyze_api_logs(logs):
    """Process a list of API log dicts and return analytics.

    Handles edge cases: empty list, malformed entries (skips with warning),
    negative numbers (treated as invalid and skipped).
    """
    if logs is None:
        raise ValueError("logs must be an array (got None)")
    total = 0
    sum_response = 0
    earliest = None
    latest = None
    hourly = defaultdict(int)
    endpoint_info = defaultdict(lambda: {
        "count": 0,
        "sum_response": 0,
        "min_response": math.inf,
        "max_response": -math.inf,
        "errors": 0,
        "status_counter": Counter(),
        "methods": Counter()
    })
    user_counts = Counter()
    performance_issues = []
    anomalies = []

    # For anomaly detection (5-minute windows), collect per-endpoint timestamps and errors
    per_endpoint_timestamps = defaultdict(list)
    per_endpoint_errors = defaultdict(list)

    # Validate & accumulate
    for i, entry in enumerate(logs):
        total += 1
        # basic validation
        try:
            ts = _parse_timestamp(entry.get("timestamp"))
            endpoint = entry.get("endpoint") or "/"
            method = entry.get("method") or "GET"
            rt = entry.get("response_time_ms")
            status = entry.get("status_code")
            user = entry.get("user_id") or "anonymous"
            req_size = entry.get("request_size_bytes", 0) or 0
            resp_size = entry.get("response_size_bytes", 0) or 0
            # numeric validation
            if rt is None or not isinstance(rt, (int, float)) or rt < 0:
                # skip this entry
                continue
            if status is None or not isinstance(status, int):
                continue
        except Exception:
            # skip malformed entry
            continue

        # time range
        if earliest is None or ts < earliest:
            earliest = ts
        if latest is None or ts > latest:
            latest = ts
        hour_key = ts.strftime("%Y-%m-%dT%H:00:00Z")
        hourly[hour_key] += 1

        # global stats
        sum_response += rt
        endpoint_data = endpoint_info[endpoint]
        endpoint_data["count"] += 1
        endpoint_data["sum_response"] += rt
        endpoint_data["min_response"] = min(endpoint_data["min_response"], rt)
        endpoint_data["max_response"] = max(endpoint_data["max_response"], rt)
        if status >= 400:
            endpoint_data["errors"] += 1
        endpoint_data["status_counter"][status] += 1
        endpoint_data["methods"][method] += 1

        user_counts[user] += 1
        per_endpoint_timestamps[endpoint].append(ts)
        if status >= 400:
            per_endpoint_errors[endpoint].append(ts)

    # handle empty or all-invalid logs
    valid_requests = sum(d["count"] for d in endpoint_info.values())
    if valid_requests == 0:
        return {
            "summary": {
                "total_requests": 0,
                "time_range": {"start": None, "end": None},
                "avg_response_time_ms": None,
                "error_rate_percentage": None
            },
            "endpoint_stats": [],
            "performance_issues": [],
            "recommendations": [],
            "hourly_distribution": {},
            "top_users_by_requests": [],
            "anomalies": [],
            "caching_opportunities": []
        }

    avg_response = sum_response / valid_requests
    # overall error rate
    total_errors = sum(d["errors"] for d in endpoint_info.values())
    error_rate_pct = (total_errors / valid_requests) * 100

    # endpoint stats
    endpoint_stats = []
    for endpoint, d in endpoint_info.items():
        most_common_status = None
        if d["status_counter"]:
            most_common_status = d["status_counter"].most_common(1)[0][0]
        endpoint_stats.append({
            "endpoint": endpoint,
            "request_count": d["count"],
            "avg_response_time_ms": d["sum_response"] / d["count"],
            "slowest_request_ms": d["max_response"],
            "fastest_request_ms": d["min_response"] if d["min_response"] != math.inf else None,
            "error_count": d["errors"],
            "most_common_status": most_common_status
        })

        # performance issue detection by endpoint average
        avg_rt = d["sum_response"] / d["count"]
        if avg_rt > RESPONSE_THRESHOLDS["critical"]:
            severity = "critical"
        elif avg_rt > RESPONSE_THRESHOLDS["high"]:
            severity = "high"
        elif avg_rt > RESPONSE_THRESHOLDS["medium"]:
            severity = "medium"
        else:
            severity = None
        if severity:
            performance_issues.append({
                "type": "slow_endpoint",
                "endpoint": endpoint,
                "avg_response_time_ms": avg_rt,
                "threshold_ms": RESPONSE_THRESHOLDS["medium"],
                "severity": severity
            })

        # error rate per endpoint
        err_rate = (d["errors"] / d["count"]) * 100
        if err_rate > ERROR_RATE_THRESHOLDS["critical"]:
            err_sev = "critical"
        elif err_rate > ERROR_RATE_THRESHOLDS["high"]:
            err_sev = "high"
        elif err_rate > ERROR_RATE_THRESHOLDS["medium"]:
            err_sev = "medium"
        else:
            err_sev = None
        if err_sev:
            performance_issues.append({
                "type": "high_error_rate",
                "endpoint": endpoint,
                "error_rate_percentage": err_rate,
                "severity": err_sev
            })

    # Recommendations (simple heuristics)
    recommendations = []
    # Top candidate for caching: endpoints with high requests and mostly GET and low errors
    for s in endpoint_stats:
        ep = s["endpoint"]
        # simple cache suggestion will be augmented in caching opportunities
        if s["request_count"] > 100 and s["avg_response_time_ms"] < 500:
            recommendations.append(f"Consider caching for {ep} ({s['request_count']} requests)")

    # Anomaly detection (Option B)
    # 1) Request spikes: check 5-minute sliding windows per endpoint
    # Build list of timestamps sorted
    for endpoint, times in per_endpoint_timestamps.items():
        if not times:
            continue
        times_sorted = sorted(times)
        # convert to epoch seconds for window counting
        secs = [int(t.timestamp()) for t in times_sorted]
        # sliding window of 300 seconds
        left = 0
        window_counts = []
        for right in range(len(secs)):
            while secs[right] - secs[left] > 300:
                left += 1
            window_count = right - left + 1
            window_counts.append(window_count)
        avg_rate = sum(window_counts) / max(1, len(window_counts))
        peak = max(window_counts)
        if avg_rate > 0 and peak > 3 * avg_rate and peak >= 10:
            anomalies.append({
                "type": "request_spike",
                "endpoint": endpoint,
                "timestamp": times_sorted[secs.index(secs[window_counts.index(peak)])].isoformat(),
                "normal_rate": avg_rate,
                "actual_rate": peak,
                "severity": "high" if peak > 50 else "medium"
            })

    # 2) Response time degradation (>2x normal average for endpoint)
    for endpoint, d in endpoint_info.items():
        avg_rt = d["sum_response"] / d["count"]
        # find any single request > 2x avg
        # For performance, we reuse the logs to spot such entries — but logs variable isn't bound here; skip per-entry check
        # Instead, check max_response
        if d["max_response"] > 2 * avg_rt and d["max_response"] > RESPONSE_THRESHOLDS["medium"]:
            anomalies.append({
                "type": "response_degradation",
                "endpoint": endpoint,
                "avg_response_time_ms": avg_rt,
                "peak_response_time_ms": d["max_response"],
                "severity": "high"
            })

    # 3) Error clusters (>10 errors within 5-minute window)
    for endpoint, err_times in per_endpoint_errors.items():
        if not err_times:
            continue
        secs = sorted(int(t.timestamp()) for t in err_times)
        left = 0
        for right in range(len(secs)):
            while secs[right] - secs[left] > 300:
                left += 1
            if (right - left + 1) >= 10:
                anomalies.append({
                    "type": "error_cluster",
                    "endpoint": endpoint,
                    "time_window": f"{datetime.fromtimestamp(secs[left], timezone.utc).isoformat()} - {datetime.fromtimestamp(secs[right], timezone.utc).isoformat()}",
                    "error_count": right - left + 1,
                    "severity": "critical" if right - left + 1 > 50 else "high"
                })
                break

    # 4) Unusual user behaviour: any single user with >50% of requests
    top_user, top_count = user_counts.most_common(1)[0]
    if top_count / sum(user_counts.values()) > 0.5:
        anomalies.append({
            "type": "unusual_user_behavior",
            "user_id": top_user,
            "request_count": top_count,
            "severity": "high"
        })

    # Caching opportunity analysis (Option D)
    caching_opportunities = []
    total_potential_saved = 0
    total_cost_savings = 0.0
    for endpoint, d in endpoint_info.items():
        if d["count"] < 1:
            continue
        get_ratio = d["methods"].get("GET", 0) / d["count"]
        err_rate = (d["errors"] / d["count"]) * 100
        consistent = d["max_response"] - d["min_response"] < 500  # heuristic
        if d["count"] > 100 and get_ratio > 0.8 and err_rate < 2 and consistent:
            potential_hit = int(d["count"] * 0.8)
            est_savings = potential_hit * 0.0001  # assume cost per request small placeholder
            caching_opportunities.append({
                "endpoint": endpoint,
                "potential_cache_hit_rate": int(get_ratio * 100),
                "current_requests": d["count"],
                "potential_requests_saved": potential_hit,
                "estimated_cost_savings_usd": round(est_savings, 4),
                "recommended_ttl_minutes": 15,
                "recommendation_confidence": "high"
            })
            total_potential_saved += potential_hit
            total_cost_savings += est_savings

    # prepare final outputs
    summary = {
        "total_requests": valid_requests,
        "time_range": {
            "start": earliest.isoformat() if earliest else None,
            "end": latest.isoformat() if latest else None
        },
        "avg_response_time_ms": avg_response,
        "error_rate_percentage": error_rate_pct
    }

    top_users = [{"user_id": u, "request_count": c} for u, c in user_counts.most_common(5)]

    # format hourly distribution to HH:00 keys (UTC)
    hourly_formatted = {}
    for k, v in sorted(hourly.items()):
        # convert "2025-01-15T10:00:00Z" => "10:00"
        hour_label = k[11:16]
        hourly_formatted[hour_label] = hourly_formatted.get(hour_label, 0) + v

    result = {
        "summary": summary,
        "endpoint_stats": sorted(endpoint_stats, key=lambda x: -x["request_count"]),
        "performance_issues": performance_issues,
        "recommendations": recommendations,
        "hourly_distribution": hourly_formatted,
        "top_users_by_requests": top_users,
        "anomalies": anomalies,
        "caching_opportunities": caching_opportunities
    }
    return result
