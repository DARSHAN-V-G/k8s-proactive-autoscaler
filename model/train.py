"""
Training and Export Pipeline for GRU Workload Predictor
Adheres to hyperparameter configuration in Table 2:
- Hidden Units: 50
- Activation: ReLU
- Batch Size: 512 (or configurable)
- Optimizer: Adam (lr=1e-3)
- Loss: MSE
- Window Size: 24
- Saves scaler, PyTorch checkpoint, and exported ONNX model.
"""

import os
import sys
import argparse
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.dataset_loader import WorkloadDataLoader
from model.gru_model import GRUWorkloadPredictor, export_model_to_torchscript, export_model_to_onnx


def train_gru_model(
    dataset_path: str = "data/borg_processed_timeseries.csv",
    output_dir: str = "model/saved_models",
    window_size: int = 24,
    epochs: int = 50,
    batch_size: int = 512,
    lr: float = 0.001,
    device: str = "cpu"
) -> dict:
    """
    Executes training loop and model export.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Check Dataset
    if not os.path.exists(dataset_path):
        fallback = "data/borg_processed_timeseries.csv"
        if os.path.exists(fallback):
            dataset_path = fallback
        else:
            raise FileNotFoundError(f"Dataset not found at '{dataset_path}'")

    # 2. Data Loading & Preprocessing
    loader = WorkloadDataLoader(window_size=window_size, target_col="cpu_rate")
    X_train, y_train, X_val, y_val, X_test, y_test = loader.load_and_preprocess_csv(dataset_path)

    scaler_path = os.path.join(output_dir, "scaler.json")
    loader.save_scaler(scaler_path)
    print(f"Fitted scaler bounds saved -> {scaler_path}")

    train_dataset = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    val_dataset = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # 3. Model Setup
    model = GRUWorkloadPredictor(input_dim=1, hidden_dim=50, output_dim=1).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print(f"Beginning training on device '{device}': {epochs} epochs, {len(X_train)} training sequences...")
    start_time = time.time()

    history = {"train_loss": [], "val_loss": []}
    best_val_loss = float("inf")
    best_weights_path = os.path.join(output_dir, "best_gru_weights.pt")

    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                pred = model(batch_x)
                val_loss = criterion(pred, batch_y)
                val_losses.append(val_loss.item())

        avg_train_loss = float(np.mean(train_losses))
        avg_val_loss = float(np.mean(val_losses))
        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), best_weights_path)

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch [{epoch:03d}/{epochs:03d}] - Train Loss: {avg_train_loss:.6f} | Val Loss: {avg_val_loss:.6f}")

    total_time = time.time() - start_time
    print(f"Training completed in {total_time:.2f}s. Best Val MSE: {best_val_loss:.6f}")

    # 4. Load Best Model and Export
    model.load_state_dict(torch.load(best_weights_path, weights_only=True))
    
    # Export TorchScript JIT (zero-dependency standalone deployment)
    pt_path = os.path.join(output_dir, "GRU_Model_24.pt")
    export_model_to_torchscript(model.to("cpu"), output_path=pt_path, seq_len=window_size)

    # Export ONNX format
    onnx_path = os.path.join(output_dir, "GRU_Model_24.onnx")
    export_model_to_onnx(model.to("cpu"), output_path=onnx_path, seq_len=window_size)

    return {
        "history": history,
        "total_time_sec": total_time,
        "best_val_loss": best_val_loss,
        "pt_path": pt_path,
        "onnx_path": onnx_path,
        "scaler_path": scaler_path
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train GRU Workload Predictor")
    parser.add_argument("--dataset", type=str, default="data/sample_cluster_data.csv", help="Path to CSV dataset")
    parser.add_argument("--output-dir", type=str, default="model/saved_models", help="Directory to save exported models")
    parser.add_argument("--window-size", type=int, default=24, help="Historical window step size (default: 24)")
    parser.add_argument("--epochs", type=int, default=40, help="Number of training epochs (default: 40)")
    parser.add_argument("--batch-size", type=int, default=512, help="Batch size (default: 512)")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate (default: 0.001)")
    args = parser.parse_args()

    train_gru_model(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        window_size=args.window_size,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
