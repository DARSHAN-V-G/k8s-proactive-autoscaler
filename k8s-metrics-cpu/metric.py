#!/usr/bin/env python3
"""
Custom Pod Autoscaler - Metric Gatherer (metric.py)
Implements the workflow in Section 5.2.2 / Figure 19 of MDPI Mathematics 2023 paper:
1. Reads pod metrics JSON passed by CPA from K8s Metrics Server via stdin.
2. Extracts current replicas (Cur_r) and CPU usage of each pod.
3. Computes total CPU (Tot_u) and average CPU usage (Avg_u).
4. Persists Avg_u and Cur_r into local SQLite database (db.py).
5. Outputs JSON payload to stdout: {"cur_r": Cur_r, "avg_u": Avg_u}
"""

import sys
import json
import os
import re

# Add directory to path for db import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import MetricsDatabase


def parse_cpu_value(value_str) -> float:
    """
    Parses Kubernetes CPU string into numeric percentage or millicores.
    Examples: '150m' -> 15.0%, '500m' -> 50.0%, '0.35' -> 35.0%, 45.0 -> 45.0
    """
    if isinstance(value_str, (int, float)):
        return float(value_str)
    
    val = str(value_str).strip()
    if val.endswith("m"):
        # Millicores: 1000m = 100% of 1 core, so 100m = 10%
        return float(val[:-1]) / 10.0
    elif val.endswith("%"):
        return float(val[:-1])
    else:
        try:
            num = float(val)
            # If formatted as a fraction [0.0, 1.0], convert to percentage
            if 0.0 <= num <= 1.0:
                return num * 100.0
            return num
        except ValueError:
            return 0.0


def process_metrics(stdin_data: str) -> dict:
    """
    Parses CPA stdin metrics and calculates Cur_r and Avg_u.
    """
    try:
        with open("/tmp/raw_metric_stdin.json", "w") as f:
            f.write(stdin_data)
    except Exception:
        pass

    data = json.loads(stdin_data) if stdin_data.strip() else {}

    cur_r = 1
    cpu_values = []

    # Handle various CPA metric JSON formats
    if isinstance(data, dict):
        # 1. CPA resource spec format
        if "resource" in data and "spec" in data["resource"]:
            cur_r = data["resource"]["spec"].get("replicas", 1)
        elif "cur_r" in data:
            cur_r = int(data["cur_r"])
        elif "replicas" in data:
            cur_r = int(data["replicas"])

        # 2. Extract metrics list
        if "kubernetesMetrics" in data:
            for km in data["kubernetesMetrics"]:
                if "current_replicas" in km:
                    cur_r = max(cur_r, int(km["current_replicas"]))
                res = km.get("resource", {})
                pod_metrics = res.get("pod_metrics_info", {})
                requests = res.get("requests", {})
                for pod_name, pinfo in pod_metrics.items():
                    val = float(pinfo.get("Value", 0))
                    req = float(requests.get(pod_name, 50))
                    if req > 0:
                        # Utilization percentage against requested CPU (matches HPA logic)
                        utilization_pct = (val / req) * 100.0
                    else:
                        utilization_pct = val / 10.0
                    cpu_values.append(utilization_pct)
        elif "metrics" in data:
            for item in data["metrics"]:
                if isinstance(item, dict):
                    v = item.get("value", item.get("cpu", 0.0))
                    cpu_values.append(parse_cpu_value(v))
                else:
                    cpu_values.append(parse_cpu_value(item))
        elif "cpu_values" in data:
            cpu_values = [parse_cpu_value(v) for v in data["cpu_values"]]
        elif "avg_u" in data:
            cpu_values = [parse_cpu_value(data["avg_u"])]

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                v = item.get("value", item.get("cpu", 0.0))
                cpu_values.append(parse_cpu_value(v))
            else:
                cpu_values.append(parse_cpu_value(item))
        cur_r = max(1, len(cpu_values))

    # Calculate Tot_u and Avg_u
    if cpu_values:
        tot_u = sum(cpu_values)
        cur_r = max(cur_r, len(cpu_values))
        avg_u = tot_u / max(1, len(cpu_values))
    else:
        tot_u = 0.0
        avg_u = 0.0

    # Ensure bounds
    cur_r = max(1, int(cur_r))
    avg_u = round(float(avg_u), 3)

    # Persist to local database
    db = MetricsDatabase()
    db.insert_metric(avg_u=avg_u, cur_r=cur_r)
    db.prune_old_records(keep_last=1000)

    return {
        "cur_r": cur_r,
        "avg_u": avg_u
    }


def main():
    try:
        raw_input = sys.stdin.read()
        result = process_metrics(raw_input)
        print(json.dumps(result))
    except Exception as e:
        # Fallback response on error
        error_resp = {"cur_r": 1, "avg_u": 0.0, "error": str(e)}
        print(json.dumps(error_resp))
        sys.exit(1)


if __name__ == "__main__":
    main()
