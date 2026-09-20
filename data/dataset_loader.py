"""
Dataset Loader and Preprocessor for Kubernetes Workload Sequences
Implements:
- Data scaling (MinMaxScaler normalization)
- 24-step (configurable) sliding window sequence generation for time-series forecasting
- Train/Validation/Test splitting
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Optional


class WorkloadDataLoader:
    def __init__(self, window_size: int = 24, target_col: str = "cpu_rate"):
        self.window_size = window_size
        self.target_col = target_col
        self.min_val: float = 0.0
        self.max_val: float = 1.0

    def fit_scaler(self, values: np.ndarray) -> None:
        """Fits the min-max scaler bounds on training values."""
        self.min_val = float(np.min(values))
        self.max_val = float(np.max(values))
        # Prevent division by zero
        if self.max_val == self.min_val:
            self.max_val = self.min_val + 1e-5

    def transform(self, values: np.ndarray) -> np.ndarray:
        """Scales values to [0, 1] range."""
        return (values - self.min_val) / (self.max_val - self.min_val)

    def inverse_transform(self, scaled_values: np.ndarray) -> np.ndarray:
        """Restores scaled values back to original scale."""
        return scaled_values * (self.max_val - self.min_val) + self.min_val

    def save_scaler(self, path: str) -> None:
        """Saves scaler parameters to a JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"min_val": self.min_val, "max_val": self.max_val, "window_size": self.window_size}, f)

    def load_scaler(self, path: str) -> None:
        """Loads scaler parameters from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
            self.min_val = data["min_val"]
            self.max_val = data["max_val"]
            self.window_size = data.get("window_size", self.window_size)

    def create_sliding_windows(
        self, data_sequence: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Creates (X, y) sliding window sequences:
        X shape: (N - window_size, window_size, 1)
        y shape: (N - window_size, 1)
        """
        if len(data_sequence) <= self.window_size:
            raise ValueError(
                f"Data sequence length ({len(data_sequence)}) must be greater than window size ({self.window_size})"
            )

        X, y = [], []
        for i in range(len(data_sequence) - self.window_size):
            X.append(data_sequence[i : i + self.window_size])
            y.append(data_sequence[i + self.window_size])

        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y, dtype=np.float32)

        # Ensure 3D shape (samples, window_size, 1) and 2D target (samples, 1)
        if X_arr.ndim == 2:
            X_arr = np.expand_dims(X_arr, axis=-1)
        if y_arr.ndim == 1:
            y_arr = np.expand_dims(y_arr, axis=-1)

        return X_arr, y_arr

    def load_and_preprocess_csv(
        self,
        csv_path: str,
        train_ratio: float = 0.8,
        machine_id: Optional[str] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Loads CSV, filters by machine if provided, scales data, and returns train/val/test splits.
        """
        df = pd.read_csv(csv_path)
        if machine_id and "machine_id" in df.columns:
            df = df[df["machine_id"] == machine_id]

        raw_values = df[self.target_col].values

        # Split into train (80%) and test (20%) before fitting scaler to prevent data leakage
        train_len = int(len(raw_values) * train_ratio)
        train_raw = raw_values[:train_len]
        test_raw = raw_values[train_len:]

        self.fit_scaler(train_raw)

        train_scaled = self.transform(train_raw)
        test_scaled = self.transform(test_raw)

        X_train_full, y_train_full = self.create_sliding_windows(train_scaled)
        X_test, y_test = self.create_sliding_windows(test_scaled)

        # Split train into train (85%) and validation (15%)
        val_split = int(len(X_train_full) * 0.85)
        X_train, y_train = X_train_full[:val_split], y_train_full[:val_split]
        X_val, y_val = X_train_full[val_split:], y_train_full[val_split:]

        return X_train, y_train, X_val, y_val, X_test, y_test
