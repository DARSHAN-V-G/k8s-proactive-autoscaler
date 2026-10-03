# Phase 1: Workload Data Pipeline & GRU Model Training (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  PHASE 1: WORKLOAD GENERATION, GRU TRAINING & MODEL EXPORT        " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Find python (virtual environment preferred)
$PythonCmd = "python"
if (Test-Path "$RepoRoot\.venv\Scripts\python.exe") {
    $PythonCmd = "$RepoRoot\.venv\Scripts\python.exe"
}

Write-Host "`n[Step 1/5] Installing Python Dependencies..." -ForegroundColor Green
& $PythonCmd -m pip install -r requirements.txt --quiet

Write-Host "`n[Step 2/5] Verifying / Processing Google Borg Workload Trace..." -ForegroundColor Green
if ((Test-Path "data/borg_traces_data.csv") -and (-not (Test-Path "data/borg_processed_timeseries.csv"))) {
    & $PythonCmd data/preprocess_borg_traces.py
}

Write-Host "`n[Step 3/5] Training 24-Step GRU Neural Network on CPU..." -ForegroundColor Green
& $PythonCmd model/train.py --epochs 30 --batch_size 64 --lr 0.001

Write-Host "`n[Step 4/5] Evaluating Baselines (ARIMA, LSTM, BiLSTM) vs GRU..." -ForegroundColor Green
& $PythonCmd model/evaluate.py

Write-Host "`n[Step 5/5] Synchronizing Model Weights to CPA Runtime..." -ForegroundColor Green
& $PythonCmd k8s-metrics-cpu/sync_weights.py

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  PHASE 1 COMPLETE! Model artifacts ready in saved_models/          " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
