"""
Baseline Model Implementations for Empirical Comparison (Paper Section 3.2 & 4.3):
- ARIMA(3, 1, 2)
- LSTM (50 hidden units)
- BiLSTM (100 hidden units)
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Optional


class LSTMWorkloadPredictor(nn.Module):
    """
    Standard LSTM model (50 hidden units, ReLU activation).
    """
    def __init__(self, input_dim: int = 1, hidden_dim: int = 50, output_dim: int = 1):
        super(LSTMWorkloadPredictor, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True
        )
        self.relu = nn.ReLU()
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        activated = self.relu(last_step)
        return self.fc(activated)


class BiLSTMWorkloadPredictor(nn.Module):
    """
    Bidirectional LSTM model (100 hidden units, ReLU activation).
    """
    def __init__(self, input_dim: int = 1, hidden_dim: int = 100, output_dim: int = 1):
        super(BiLSTMWorkloadPredictor, self).__init__()
        self.bilstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.relu = nn.ReLU()
        # Bidirectional outputs 2 * hidden_dim
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.bilstm(x)
        last_step = lstm_out[:, -1, :]
        activated = self.relu(last_step)
        return self.fc(activated)


class ARIMAPredictor:
    """
    ARIMA(p=3, d=1, q=2) baseline predictor as specified in the paper.
    """
    def __init__(self, order: tuple = (3, 1, 2)):
        self.order = order

    def predict_next(self, history: np.ndarray) -> float:
        """
        Fits ARIMA on the recent historical window and forecasts 1 step ahead.
        """
        import warnings
        try:
            from statsmodels.tsa.arima.model import ARIMA
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ARIMA(history, order=self.order)
                fitted = model.fit()
                forecast = fitted.forecast(steps=1)
                return float(forecast[0])
        except Exception:
            return float(np.mean(history[-5:]))
