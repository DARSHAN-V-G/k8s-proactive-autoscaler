#!/usr/bin/env bash
# ==============================================================================
# Phase 1: Workload Data Pipeline & GRU Model Training
# Research Paper: "Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  PHASE 1: WORKLOAD GENERATION, GRU TRAINING & MODEL EXPORT        ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Navigate to project root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1. Check Python installation
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${YELLOW}Error: Python is not installed. Please install Python 3.9+.${NC}"
    exit 1
fi
PYTHON_CMD=$(command -v python3 || command -v python)

echo -e "\n${GREEN}[Step 1/5]${NC} Installing Python Dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt --quiet

echo -e "\n${GREEN}[Step 2/5]${NC} Verifying / Processing Google Borg Workload Trace..."
if [ -f "data/borg_traces_data.csv" ] && [ ! -f "data/borg_processed_timeseries.csv" ]; then
    $PYTHON_CMD data/preprocess_borg_traces.py
fi

echo -e "\n${GREEN}[Step 3/5]${NC} Training 24-Step GRU Neural Network on CPU..."
$PYTHON_CMD model/train.py --epochs 30 --batch_size 64 --lr 0.001

echo -e "\n${GREEN}[Step 4/5]${NC} Evaluating Baselines (ARIMA, LSTM, BiLSTM) vs GRU..."
$PYTHON_CMD model/evaluate.py

echo -e "\n${GREEN}[Step 5/5]${NC} Synchronizing Trained Model Weights to CPA Runtime Engine..."
$PYTHON_CMD k8s-metrics-cpu/sync_weights.py

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}  PHASE 1 COMPLETE! Model artifacts ready in saved_models/          ${NC}"
echo -e "${GREEN}====================================================================${NC}"
