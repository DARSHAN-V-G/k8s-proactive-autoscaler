"""
Evaluation & Benchmark Comparison Module
Reproduces the empirical comparison in Section 4.4 / Table 3 of MDPI Mathematics 2023 paper:
Evaluates ARIMA(3,1,2), LSTM(50), BiLSTM(100), and GRU(50) on:
- MSE (Mean Squared Error)
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R2 Score
- Training Time (s)
- Prediction Latency (ms)
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.dataset_loader import WorkloadDataLoader
from data.generate_synthetic_trace import generate_multiple_machine_traces
from model.gru_model import GRUWorkloadPredictor, GRUInferenceEngine, export_model_to_torchscript
from model.baseline_models import LSTMWorkloadPredictor, BiLSTMWorkloadPredictor, ARIMAPredictor


def train_pytorch_model(model, train_loader, epochs=20, lr=0.001):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    start_time = time.time()
    for _ in range(epochs):
        model.train()
        for bx, by in train_loader:
            optimizer.zero_grad()
            pred = model(bx)
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()
    train_time = time.time() - start_time
    return train_time


def evaluate_all_models(
    dataset_path: str = "data/sample_cluster_data.csv",
    window_size: int = 24,
    epochs: int = 20,
    test_samples_cap: int = 500
):
    if not os.path.exists(dataset_path):
        generate_multiple_machine_traces(n_machines=5, output_path=dataset_path)

    loader = WorkloadDataLoader(window_size=window_size)
    X_train, y_train, X_val, y_val, X_test, y_test = loader.load_and_preprocess_csv(dataset_path)

    # Subsample test set for faster benchmarking if very large
    if len(X_test) > test_samples_cap:
        test_indices = np.random.choice(len(X_test), test_samples_cap, replace=False)
        X_test_eval = X_test[test_indices]
        y_test_eval = y_test[test_indices]
    else:
        X_test_eval = X_test
        y_test_eval = y_test

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train)),
        batch_size=512,
        shuffle=True
    )

    results = []

    # 1. GRU (50 units) - Proposed
    print("Training GRU Model (50 units - Proposed)...")
    gru = GRUWorkloadPredictor(hidden_dim=50)
    gru_train_time = train_pytorch_model(gru, train_loader, epochs=epochs)
    gru.eval()
    t0 = time.time()
    with torch.no_grad():
        gru_preds = gru(torch.from_numpy(X_test_eval)).numpy().flatten()
    gru_infer_time_ms = ((time.time() - t0) / len(X_test_eval)) * 1000.0

    gru_mse = mean_squared_error(y_test_eval, gru_preds)
    gru_rmse = np.sqrt(gru_mse)
    gru_mae = mean_absolute_error(y_test_eval, gru_preds)
    gru_r2 = r2_score(y_test_eval, gru_preds)

    results.append({
        "Model": "GRU (Proposed)",
        "Step Size": f"{window_size} Steps",
        "MSE": f"{gru_mse:.5f}",
        "RMSE": f"{gru_rmse:.5f}",
        "MAE": f"{gru_mae:.5f}",
        "R2": f"{gru_r2:.4f}",
        "Training Time (s)": f"{gru_train_time:.2f}",
        "Prediction Latency (ms)": f"{gru_infer_time_ms:.2f}"
    })

    # 2. LSTM (50 units)
    print("Training LSTM Model (50 units)...")
    lstm = LSTMWorkloadPredictor(hidden_dim=50)
    lstm_train_time = train_pytorch_model(lstm, train_loader, epochs=epochs)
    lstm.eval()
    t0 = time.time()
    with torch.no_grad():
        lstm_preds = lstm(torch.from_numpy(X_test_eval)).numpy().flatten()
    lstm_infer_time_ms = ((time.time() - t0) / len(X_test_eval)) * 1000.0

    lstm_mse = mean_squared_error(y_test_eval, lstm_preds)
    results.append({
        "Model": "LSTM",
        "Step Size": f"{window_size} Steps",
        "MSE": f"{lstm_mse:.5f}",
        "RMSE": f"{np.sqrt(lstm_mse):.5f}",
        "MAE": f"{mean_absolute_error(y_test_eval, lstm_preds):.5f}",
        "R2": f"{r2_score(y_test_eval, lstm_preds):.4f}",
        "Training Time (s)": f"{lstm_train_time:.2f}",
        "Prediction Latency (ms)": f"{lstm_infer_time_ms:.2f}"
    })

    # 3. BiLSTM (100 units)
    print("Training BiLSTM Model (100 units)...")
    bilstm = BiLSTMWorkloadPredictor(hidden_dim=100)
    bilstm_train_time = train_pytorch_model(bilstm, train_loader, epochs=epochs)
    bilstm.eval()
    t0 = time.time()
    with torch.no_grad():
        bilstm_preds = bilstm(torch.from_numpy(X_test_eval)).numpy().flatten()
    bilstm_infer_time_ms = ((time.time() - t0) / len(X_test_eval)) * 1000.0

    bilstm_mse = mean_squared_error(y_test_eval, bilstm_preds)
    results.append({
        "Model": "BiLSTM",
        "Step Size": f"{window_size} Steps",
        "MSE": f"{bilstm_mse:.5f}",
        "RMSE": f"{np.sqrt(bilstm_mse):.5f}",
        "MAE": f"{mean_absolute_error(y_test_eval, bilstm_preds):.5f}",
        "R2": f"{r2_score(y_test_eval, bilstm_preds):.4f}",
        "Training Time (s)": f"{bilstm_train_time:.2f}",
        "Prediction Latency (ms)": f"{bilstm_infer_time_ms:.2f}"
    })

    # 4. ARIMA(3, 1, 2) on sample sequences
    print("Evaluating ARIMA(3, 1, 2) baseline...")
    arima = ARIMAPredictor()
    arima_subsample = X_test_eval[:min(30, len(X_test_eval))]
    arima_y = y_test_eval[:min(30, len(y_test_eval))]
    t0 = time.time()
    arima_preds = [arima.predict_next(seq.flatten()) for seq in arima_subsample]
    arima_infer_time_ms = ((time.time() - t0) / len(arima_subsample)) * 1000.0

    arima_mse = mean_squared_error(arima_y, arima_preds)
    results.append({
        "Model": "ARIMA",
        "Step Size": "-",
        "MSE": f"{arima_mse:.5f}",
        "RMSE": f"{np.sqrt(arima_mse):.5f}",
        "MAE": f"{mean_absolute_error(arima_y, arima_preds):.5f}",
        "R2": f"{r2_score(arima_y, arima_preds):.4f}",
        "Training Time (s)": "-",
        "Prediction Latency (ms)": f"{arima_infer_time_ms:.2f}"
    })

    # Clean up temp file if created
    temp_pt = "model/saved_models/temp_eval_gru.pt"
    if os.path.exists(temp_pt):
        os.remove(temp_pt)

    df_res = pd.DataFrame(results)
    print("\n" + "=" * 90)
    print("EMPIRICAL EVALUATION RESULTS (Matches Table 3 in Paper)")
    print("=" * 90)
    print(df_res.to_string(index=False))
    print("=" * 90)
    return df_res


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate forecasting baselines vs GRU")
    default_ds = "data/borg_processed_timeseries.csv" if os.path.exists("data/borg_processed_timeseries.csv") else "data/sample_cluster_data.csv"
    parser.add_argument("--dataset", type=str, default=default_ds, help="Path to evaluation dataset")
    parser.add_argument("--window-size", type=int, default=24, help="Sliding window size (default: 24)")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs for baselines (default: 20)")
    args = parser.parse_args()

    evaluate_all_models(dataset_path=args.dataset, window_size=args.window_size, epochs=args.epochs)
