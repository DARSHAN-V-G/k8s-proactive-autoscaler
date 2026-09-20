# Custom Pod Autoscaler (CPA) - GRU Proactive Autoscaler Runtime Container
# Based on Section 5.2.3 of MDPI Mathematics 2023 paper

FROM custompodautoscaler/python:latest

# Install CPU-only PyTorch and NumPy using --extra-index-url
RUN pip install --no-cache-dir torch numpy --extra-index-url https://download.pytorch.org/whl/cpu

# Copy CPA configuration
COPY config.yaml /config.yaml
COPY config.yaml /app/config.yaml

# Copy Metric Gatherer and Evaluator scripts
COPY metric.py /metric.py
COPY evaluate.py /evaluate.py
COPY db.py /db.py

# Copy pre-trained GRU model & fitted scaler bounds
COPY saved_models /saved_models
COPY saved_models/GRU_Model_24.pt /GRU_Model_24.pt
COPY saved_models/scaler.json /scaler.json

# Copy model helper package
COPY model /model

# Make scripts executable
RUN chmod +x /metric.py /evaluate.py

