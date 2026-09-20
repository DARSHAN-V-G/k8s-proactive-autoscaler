"""
Unit tests for GRU Model Architecture, TorchScript JIT Export, and Inference Latency.
"""

import os
import time
import tempfile
import numpy as np
import torch
import pytest
from model.gru_model import GRUWorkloadPredictor, export_model_to_torchscript, GRUInferenceEngine


def test_gru_forward_shape():
    model = GRUWorkloadPredictor(input_dim=1, hidden_dim=50, output_dim=1)
    model.eval()

    # Batch of 8 samples, 24 timesteps, 1 feature
    dummy_input = torch.randn(8, 24, 1)
    out = model(dummy_input)

    assert out.shape == (8, 1)


def test_torchscript_export_and_inference_parity():
    model = GRUWorkloadPredictor(input_dim=1, hidden_dim=50, output_dim=1)
    model.eval()

    with tempfile.TemporaryDirectory() as tmpdir:
        pt_file = os.path.join(tmpdir, "test_gru.pt")
        export_model_to_torchscript(model, output_path=pt_file, seq_len=24)

        assert os.path.exists(pt_file)

        # Compare PyTorch raw model vs TorchScript engine output
        test_seq = np.random.uniform(0.1, 0.9, size=(24,)).astype(np.float32)

        # Raw PyTorch prediction
        with torch.no_grad():
            torch_in = torch.from_numpy(test_seq).reshape(1, 24, 1)
            raw_pred = float(model(torch_in)[0, 0].item())

        # GRUInferenceEngine prediction (raw forward pass comparison)
        engine = GRUInferenceEngine(pt_file)
        engine_pred = engine.predict(test_seq, apply_scaling=False, apply_inverse_scale=False)

        # Should match perfectly
        np.testing.assert_almost_equal(raw_pred, engine_pred, decimal=5)


def test_inference_latency_benchmark():
    """
    Paper benchmark requires prediction speed well below 65ms.
    TorchScript engine should execute in < 15ms on CPU.
    """
    model = GRUWorkloadPredictor(input_dim=1, hidden_dim=50, output_dim=1)
    model.eval()

    with tempfile.TemporaryDirectory() as tmpdir:
        pt_file = os.path.join(tmpdir, "speed_test.pt")
        export_model_to_torchscript(model, output_path=pt_file, seq_len=24)
        engine = GRUInferenceEngine(pt_file)

        test_seq = np.random.uniform(0.1, 0.9, size=(24,)).astype(np.float32)

        # Warmup
        for _ in range(5):
            _ = engine.predict(test_seq)

        latencies = []
        for _ in range(50):
            t0 = time.perf_counter()
            _ = engine.predict(test_seq)
            latencies.append((time.perf_counter() - t0) * 1000.0)

        avg_latency_ms = float(np.mean(latencies))
        print(f"\nAverage CPU inference latency: {avg_latency_ms:.3f} ms")
        assert avg_latency_ms < 65.0, f"Inference latency {avg_latency_ms:.2f}ms exceeds 65ms requirement!"
