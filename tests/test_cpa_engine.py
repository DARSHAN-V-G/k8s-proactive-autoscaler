"""
Unit & Integration Tests for Phase 2: Custom Pod Autoscaler Engine (db.py, metric.py, evaluate.py)
"""

import os
import sys
import json
import tempfile
import numpy as np
import pytest

# Add k8s-metrics-cpu to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "k8s-metrics-cpu")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import MetricsDatabase
from metric import process_metrics
from evaluate import evaluate_scaling


def test_metrics_database_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        db = MetricsDatabase(db_path=db_path)

        assert db.get_sequence_length() == 0

        # Insert 30 observations
        for i in range(30):
            db.insert_metric(avg_u=float(i + 1), cur_r=2, timestamp=1000.0 + i)

        assert db.get_sequence_length() == 30

        # Retrieve last 24 steps
        seq = db.get_recent_sequence(n_steps=24)
        assert len(seq) == 24
        # Should be in chronological order (oldest to newest): 7 to 30
        assert seq[0] == 7.0
        assert seq[-1] == 30.0

        # Prune records keeping only 10
        db.prune_old_records(keep_last=10)
        assert db.get_sequence_length() == 10

        # Clear
        db.clear()
        assert db.get_sequence_length() == 0


def test_metric_gatherer_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        os.environ["METRICS_DB_PATH"] = db_path

        # Simulate CPA JSON metric input for 3 pods: 400m, 600m, 800m (Avg = 60%)
        sample_cpa_input = json.dumps({
            "resource": {
                "spec": {"replicas": 3}
            },
            "metrics": [
                {"value": "400m"},
                {"value": "600m"},
                {"value": "800m"}
            ]
        })

        result = process_metrics(sample_cpa_input)
        assert result["cur_r"] == 3
        # 400m=40%, 600m=60%, 800m=80% -> Avg = 60.0%
        assert result["avg_u"] == 60.0

        # Verify persisted into SQLite DB
        db = MetricsDatabase(db_path=db_path)
        assert db.get_sequence_length() == 1
        assert db.get_recent_sequence(1)[0] == 60.0


def test_evaluator_cold_start_reactive_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        db = MetricsDatabase(db_path=db_path)

        # Insert only 5 observations (less than window_size 24)
        for i in range(5):
            db.insert_metric(avg_u=80.0, cur_r=2)

        # Input: current replicas = 2, avg_u = 80.0%, target threshold = 50%
        # Reactive formula: ceil(2 * (80.0 / 50.0)) = ceil(3.2) = 4 replicas
        cpa_input = json.dumps({"cur_r": 2, "avg_u": 80.0})
        res = evaluate_scaling(cpa_input, target_cpu_threshold=50.0, window_size=24, db_path=db_path)

        assert res["mode"] == "reactive_hpa"
        assert res["targetReplicas"] == 4
        assert res["cur_r"] == 2


def test_evaluator_proactive_gru_scaling():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        db = MetricsDatabase(db_path=db_path)

        # Seed database with 24 rising CPU load points (e.g., traffic surge starting)
        for val in np.linspace(30.0, 75.0, 24):
            db.insert_metric(avg_u=float(val), cur_r=2)

        cpa_input = json.dumps({"cur_r": 2, "avg_u": 75.0})
        res = evaluate_scaling(cpa_input, target_cpu_threshold=50.0, window_size=24, db_path=db_path)

        # Should trigger proactive prediction mode
        assert res["mode"] == "proactive_gru"
        assert res["targetReplicas"] >= 2
        assert res["pre_u"] is not None
        print(f"\nProactive prediction Pre_u: {res['pre_u']:.2f}% -> Target Replicas: {res['targetReplicas']}")


def test_evaluator_minimum_replica_safety():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        db = MetricsDatabase(db_path=db_path)

        # Idle load: 0% CPU
        db.insert_metric(avg_u=0.0, cur_r=1)

        cpa_input = json.dumps({"cur_r": 1, "avg_u": 0.0})
        res = evaluate_scaling(cpa_input, target_cpu_threshold=50.0, window_size=24, db_path=db_path)

        # Must never scale to 0 replicas
        assert res["targetReplicas"] == 1
