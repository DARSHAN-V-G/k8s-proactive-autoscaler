"""
Unit tests for data generation and preprocessing pipeline.
"""

import os
import tempfile
import numpy as np
import pytest
from data.generate_synthetic_trace import generate_workload_trace, generate_multiple_machine_traces
from data.dataset_loader import WorkloadDataLoader


def test_generate_workload_trace():
    df = generate_workload_trace(n_points=100, interval_sec=300, seed=42)
    assert len(df) == 100
    assert "cpu_rate" in df.columns
    assert "memory_rate" in df.columns
    assert (df["cpu_rate"] >= 0.0).all() and (df["cpu_rate"] <= 1.0).all()
    assert (df["memory_rate"] >= 0.0).all() and (df["memory_rate"] <= 1.0).all()


def test_sliding_window_dimensions():
    loader = WorkloadDataLoader(window_size=24)
    raw_series = np.linspace(0.1, 0.9, 100)
    X, y = loader.create_sliding_windows(raw_series)

    # 100 points with window 24 -> 76 samples
    assert X.shape == (76, 24, 1)
    assert y.shape == (76, 1)
    # Check that y is the step immediately following X[0]
    np.testing.assert_almost_equal(X[0, -1, 0], raw_series[23])
    np.testing.assert_almost_equal(y[0, 0], raw_series[24])


def test_scaler_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        scaler_file = os.path.join(tmpdir, "scaler.json")
        loader = WorkloadDataLoader(window_size=24)
        sample_data = np.array([0.1, 0.5, 0.9])
        loader.fit_scaler(sample_data)

        assert loader.min_val == 0.1
        assert loader.max_val == 0.9

        loader.save_scaler(scaler_file)
        assert os.path.exists(scaler_file)

        new_loader = WorkloadDataLoader()
        new_loader.load_scaler(scaler_file)
        assert new_loader.min_val == 0.1
        assert new_loader.max_val == 0.9
        assert new_loader.window_size == 24


def test_train_val_test_split():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "test_cluster.csv")
        generate_multiple_machine_traces(n_machines=2, n_points=500, output_path=csv_file)

        loader = WorkloadDataLoader(window_size=24)
        X_train, y_train, X_val, y_val, X_test, y_test = loader.load_and_preprocess_csv(csv_file)

        assert len(X_train) > 0
        assert len(X_val) > 0
        assert len(X_test) > 0
        assert X_train.shape[1:] == (24, 1)
        assert y_train.shape[1:] == (1,)
