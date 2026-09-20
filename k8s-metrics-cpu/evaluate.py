#!/usr/bin/env python3
"""
Custom Pod Autoscaler - Evaluator (evaluate.py)
Implements the workflow in Section 5.2.2 / Figure 20 of MDPI Mathematics 2023 paper:
1. Receives Cur_r and Avg_u in JSON format from Metric Gatherer.
2. Reads historical metrics sequence Seq[] from local database (db.py).
3. If Seq_len >= 24:
     Feeds Seq[-24:] to pre-trained GRU model (GRU_Model_24.pt) to predict next-step CPU (Pre_u).
     Computes proactive target replicas: Tar_r = ceil(Cur_r * (Pre_u / Tar_ut)).
4. Fallback (if Seq_len < 24 or Tar_r == 0):
     Computes reactive target replicas: Tar_r = ceil(Cur_r * (Avg_u / Tar_ut)).
5. Emits target replica JSON to stdout: {"targetReplicas": Tar_r}
"""

import sys
import json
import math
import os
import numpy as np

# Add directory and root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from db import MetricsDatabase
from model.gru_model import GRUInferenceEngine


def get_model_and_scaler_paths() -> tuple:
    """Finds GRU_Model_24.pt and scaler.json across standard locations."""
    possible_dirs = [
        current_dir,
        os.path.join(current_dir, "saved_models"),
        os.path.join(current_dir, "..", "model", "saved_models"),
        "/model/saved_models",
        "/"
    ]
    model_path = None
    scaler_path = None

    for d in possible_dirs:
        pt_candidate = os.path.join(d, "GRU_Model_24.pt")
        onnx_candidate = os.path.join(d, "GRU_Model_24.onnx")
        sc_candidate = os.path.join(d, "scaler.json")

        if model_path is None:
            if os.path.exists(pt_candidate):
                model_path = pt_candidate
            elif os.path.exists(onnx_candidate):
                model_path = onnx_candidate

        if scaler_path is None and os.path.exists(sc_candidate):
            scaler_path = sc_candidate

    return model_path, scaler_path


def parse_evaluator_input(stdin_data: str) -> tuple:
    """
    Extracts cur_r and avg_u from CPA input JSON.
    """
    try:
        with open("/tmp/raw_eval_stdin.json", "w") as f:
            f.write(stdin_data)
    except Exception:
        pass

    data = json.loads(stdin_data) if stdin_data.strip() else {}

    cur_r = 1
    avg_u = 0.0

    if isinstance(data, dict):
        # Format 1: Passed from Metric Gatherer directly
        if "cur_r" in data and "avg_u" in data:
            cur_r = int(data["cur_r"])
            avg_u = float(data["avg_u"])
        # Format 2: CPA standard wrapper with metrics array
        elif "metrics" in data:
            for item in data["metrics"]:
                if isinstance(item, dict) and "value" in item:
                    val_str = item["value"]
                    try:
                        inner = json.loads(val_str)
                        if "cur_r" in inner:
                            cur_r = int(inner["cur_r"])
                        if "avg_u" in inner:
                            avg_u = float(inner["avg_u"])
                    except Exception:
                        pass
        # Format 3: Spec replicas
        if "resource" in data and "spec" in data["resource"]:
            spec_r = data["resource"]["spec"].get("replicas")
            if spec_r is not None:
                cur_r = int(spec_r)

    return max(1, cur_r), float(avg_u)


def evaluate_scaling(
    stdin_data: str,
    target_cpu_threshold: float = 50.0,
    window_size: int = 24,
    db_path: str = None
) -> dict:
    """
    Core autoscaling decision logic following Figure 20.
    """
    cur_r, avg_u = parse_evaluator_input(stdin_data)

    # Allow environment override for target CPU utilization
    env_tar_ut = os.environ.get("TARGET_CPU_UTILIZATION")
    if env_tar_ut:
        try:
            target_cpu_threshold = float(env_tar_ut)
        except ValueError:
            pass

    tar_ut = float(target_cpu_threshold)
    tar_r = 0
    decision_mode = "reactive_fallback"
    pre_u = None

    db = MetricsDatabase(db_path=db_path)
    seq = db.get_recent_sequence(n_steps=window_size)
    seq_len = len(seq)

    model_path, scaler_path = get_model_and_scaler_paths()

    # Step 1: Proactive Prediction if sufficient history and model available
    if seq_len >= window_size and model_path is not None:
        try:
            engine = GRUInferenceEngine(model_path, scaler_path=scaler_path)
            
            # Normalize sequence elements to [0, 1] range for GRU inference
            # (since training data had values in [0.02, 0.98])
            seq_normalized = []
            for val in seq[-window_size:]:
                v = float(val)
                if v > 1.0:
                    v = v / 100.0
                seq_normalized.append(min(1.0, max(0.0, v)))
            
            # Predict next step normalized CPU load
            pre_u_norm = float(engine.predict(seq_normalized, apply_scaling=True, apply_inverse_scale=True))
            pre_u_norm = min(1.0, max(0.0, pre_u_norm))
            
            # Convert to percentage scale
            pre_u_pct = pre_u_norm * 100.0
            
            # If current per-pod average exceeds 100% (e.g. pod limit >> request under spike),
            # propagate the load multiplier
            if avg_u > 100.0:
                last_val = max(0.01, seq_normalized[-1])
                trend_ratio = max(0.5, min(2.0, pre_u_norm / last_val))
                pre_u = avg_u * trend_ratio
            else:
                pre_u = pre_u_pct
            
            # Proactive replica calculation (Formula 1 from paper using Pre_u)
            tar_r = math.ceil(cur_r * (pre_u / tar_ut))
            decision_mode = "proactive_gru"
        except Exception as e:
            # On prediction error, fall back gracefully
            tar_r = 0
            decision_mode = f"fallback_error_{e}"

    # Step 2: Fallback to reactive HPA if history < 24 or predicted Tar_r == 0 (Figure 20)
    if tar_r == 0 or seq_len < window_size:
        # Standard reactive HPA calculation (Formula 1 from paper using Avg_u)
        if avg_u > 0:
            tar_r = math.ceil(cur_r * (avg_u / tar_ut))
        else:
            tar_r = cur_r
        decision_mode = "reactive_hpa"

    # Enforce minimum bound
    tar_r = max(1, int(tar_r))

    return {
        "targetReplicas": tar_r,
        "mode": decision_mode,
        "cur_r": cur_r,
        "avg_u": avg_u,
        "pre_u": pre_u,
        "seq_len": seq_len
    }


def main():
    try:
        raw_input = sys.stdin.read()
        eval_result = evaluate_scaling(raw_input)
        # CPA expects JSON with targetReplicas key
        print(json.dumps({"targetReplicas": eval_result["targetReplicas"]}))
    except Exception as e:
        # Fallback safe output
        print(json.dumps({"targetReplicas": 1, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
