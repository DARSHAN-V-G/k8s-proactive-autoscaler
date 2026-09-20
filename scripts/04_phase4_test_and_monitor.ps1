# Phase 4: Observability, Traffic Stress Testing & Benchmark Simulation (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  PHASE 4: MONITORING, TRAFFIC GENERATION & SIMULATION REPORT       " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Find python
$PythonCmd = "python"
if (Test-Path "$RepoRoot\.venv\Scripts\python.exe") {
    $PythonCmd = "$RepoRoot\.venv\Scripts\python.exe"
}

# 1. Deploy Prometheus
Write-Host "`n[Step 1/4] Deploying Prometheus and Kube-State-Metrics..." -ForegroundColor Green
kubectl apply -f manifests/monitoring/prometheus.yaml
kubectl rollout status deployment/prometheus --timeout=120s

# 2. Deploy Traffic Load Generator
Write-Host "`n[Step 2/4] Launching Traffic Load Generator..." -ForegroundColor Green
kubectl apply -f manifests/load-generator.yaml
kubectl scale deployment load-generator --replicas=5
kubectl rollout status deployment/load-generator --timeout=60s

# 3. Run Standalone Offline Simulation
Write-Host "`n[Step 3/4] Running Offline Autoscaling Simulation (Figure 21 Replication)..." -ForegroundColor Green
& $PythonCmd sim/simulate_autoscaling.py

# 4. Display Status & Info
Write-Host "`n[Step 4/4] Live Cluster Status Summary:" -ForegroundColor Green
kubectl get deployment php-cpa php-hpa
Write-Host ""
kubectl get pods

Write-Host "`n====================================================================" -ForegroundColor Cyan
Write-Host "  OBSERVABILITY & MONITORING INSTRUCTIONS                           " -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "1. Forward Prometheus port in a separate terminal:"
Write-Host "   kubectl port-forward svc/prometheus 9090:9090" -ForegroundColor Yellow
Write-Host "2. Open Prometheus in your browser:"
Write-Host "   http://localhost:9090" -ForegroundColor Yellow
Write-Host "3. Execute query in Prometheus Expression bar:"
Write-Host "   kube_deployment_status_replicas{deployment=~`"php-.*`"}" -ForegroundColor Yellow
Write-Host "4. Offline simulation comparison plot saved to:"
Write-Host "   docs/plots/scaling_comparison.png" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Cyan
