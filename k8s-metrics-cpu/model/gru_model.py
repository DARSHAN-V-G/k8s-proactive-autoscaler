"""
GRU Workload Prediction Model (PyTorch, TorchScript & ONNX Runtime)
Adheres to the architecture in MDPI Mathematics 2023 paper:
- 50 hidden units
- ReLU activation
- Adam optimizer, MSE loss
- 24-step historical window input
- Fast TorchScript / ONNX runtime exporter & inference engine (<15ms latency)
"""

import os
import json
import numpy as np
from typing import Optional, Union

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = None
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:
    class GRUWorkloadPredictor(nn.Module):
        """
        GRU neural network model for Kubernetes CPU load forecasting.
        Architecture:
          Input (Batch, 24, 1) -> GRU (50 units) -> ReLU -> Linear(50, 1) -> Output (Batch, 1)
        """
        def __init__(self, input_dim: int = 1, hidden_dim: int = 50, output_dim: int = 1):
            super(GRUWorkloadPredictor, self).__init__()
            self.input_dim = input_dim
            self.hidden_dim = hidden_dim
            self.output_dim = output_dim
            self.gru = nn.GRU(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=1,
                batch_first=True
            )
            self.relu = nn.ReLU()
            self.fc = nn.Linear(hidden_dim, output_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch_size, seq_len, input_dim)
            gru_out, _ = self.gru(x)
            last_step = gru_out[:, -1, :]
            activated = self.relu(last_step)
            out = self.fc(activated)
            return out


    def export_model_to_torchscript(
        model: nn.Module,
        output_path: str = "model/saved_models/GRU_Model_24.pt",
        seq_len: int = 24,
        input_dim: int = 1
    ) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        model.eval()
        scripted_model = torch.jit.script(model)
        torch.jit.save(scripted_model, output_path)
        print(f"Model successfully saved as TorchScript JIT -> {output_path}")
        return output_path
else:
    class GRUWorkloadPredictor:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is not installed in this environment. Use ONNX runtime instead.")

    def export_model_to_torchscript(*args, **kwargs):
        raise ImportError("PyTorch is not installed in this environment.")



class GRUInferenceEngine:
    def __init__(self, model_path: str, scaler_path: Optional[str] = None):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        self.model_path = model_path
        self.scaler_path = scaler_path
        self.min_val = 0.0
        self.max_val = 1.0

        if scaler_path and os.path.exists(scaler_path):
            with open(scaler_path, "r") as f:
                s_data = json.load(f)
                self.min_val = s_data.get("min_val", 0.0)
                self.max_val = s_data.get("max_val", 1.0)

        # Detect model format
        if model_path.endswith(".pt") or model_path.endswith(".pth"):
            if not TORCH_AVAILABLE:
                raise ImportError(f"Cannot load PyTorch model {model_path}: PyTorch is not installed in this environment.")
            self.mode = "torchscript"
            try:
                self.model = torch.jit.load(model_path, map_location="cpu")
            except Exception:
                self.model = GRUWorkloadPredictor()
                self.model.load_state_dict(torch.load(model_path, map_location="cpu"))
            self.model.eval()
        elif model_path.endswith(".onnx"):
            self.mode = "onnx"
            import onnxruntime as ort
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 1
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.session = ort.InferenceSession(model_path, sess_options=opts, providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        else:
            raise ValueError(f"Unsupported model extension for: {model_path}")

    def predict(
        self,
        sequence: Union[np.ndarray, list],
        apply_scaling: bool = True,
        apply_inverse_scale: bool = True
    ) -> float:
        arr = np.array(sequence, dtype=np.float32)

        is_percentage = False
        if np.max(arr) > 1.0 and self.max_val <= 1.0:
            arr = arr / 100.0
            is_percentage = True

        if apply_scaling and (self.max_val > self.min_val):
            arr = (arr - self.min_val) / (self.max_val - self.min_val)

        if arr.ndim == 1:
            arr = arr.reshape(1, len(arr), 1)
        elif arr.ndim == 2:
            arr = np.expand_dims(arr, axis=-1)

        if self.mode == "torchscript":
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is not installed.")
            with torch.no_grad():
                tensor_in = torch.from_numpy(arr)
                pred = self.model(tensor_in).numpy()
        else:
            pred = self.session.run([self.output_name], {self.input_name: arr})[0]

        val = float(pred[0, 0]) if pred.ndim > 1 else float(pred[0])

        if apply_inverse_scale and (self.max_val > self.min_val):
            val = val * (self.max_val - self.min_val) + self.min_val

        if is_percentage and val <= 1.0:
            val = val * 100.0

        return val
