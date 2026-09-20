"""
Unit tests for Autoscaling Simulation Engine (Phase 4)
"""

import os
import sys
import tempfile
import numpy as np
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.simulate_autoscaling import AutoscalingSimulator


def test_autoscaling_simulator_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        plot_path = os.path.join(tmpdir, "test_plot.png")

        # Create 50 steps of workload: baseline 30% -> spike 85% -> drop 30%
        workload = np.concatenate([
            np.full(25, 30.0),
            np.full(10, 85.0),
            np.full(15, 30.0)
        ])

        sim = AutoscalingSimulator(
            target_cpu_threshold=50.0,
            pod_startup_delay_steps=2,
            downscale_stabilization_steps=4
        )

        metrics = sim.simulate_workload(
            workload,
            step_interval_sec=10,
            output_plot_path=plot_path
        )

        assert metrics["Total Steps"] == 50
        assert os.path.exists(plot_path)
        assert "CPA SLA Violations (steps)" in metrics
        assert "HPA SLA Violations (steps)" in metrics
