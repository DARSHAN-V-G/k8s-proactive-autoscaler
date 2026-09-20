# Phase 2: Build CPA Container & Kind Local Cluster Setup (PowerShell)
$ErrorActionPreference = "Stop"

$ClusterName = "k8s-autoscaler"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  PHASE 2: KIND CLUSTER SETUP & CPA DOCKER IMAGE BUILD             " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# 1. Check or create Kind cluster
Write-Host "`n[Step 1/4] Verifying Kind Cluster '$ClusterName'..." -ForegroundColor Green
$existingClusters = kind get clusters
if ($existingClusters -contains $ClusterName) {
    Write-Host "Cluster '$ClusterName' is already running."
} else {
    Write-Host "Creating 3-node Kind cluster from kind-config.yaml..."
    kind create cluster --config kind-config.yaml --name $ClusterName
}

# 2. Build custom k8s-metrics-cpu Docker Image
Write-Host "`n[Step 2/4] Building CPA Docker Image (k8s-metrics-cpu:latest)..." -ForegroundColor Green
docker build -t k8s-metrics-cpu:latest ./k8s-metrics-cpu

# 3. Pull required upstream images
Write-Host "`n[Step 3/4] Pre-pulling upstream Kubernetes images..." -ForegroundColor Green
docker pull custompodautoscaler/operator:v1.2.1
docker pull registry.k8s.io/hpa-example:latest
docker pull registry.k8s.io/metrics-server/metrics-server:v0.6.3
docker pull prom/prometheus:v2.45.0
docker pull registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.9.2
docker pull busybox:latest

# 4. Load all container images into Kind cluster nodes
Write-Host "`n[Step 4/4] Sideloading Docker images into Kind nodes..." -ForegroundColor Green
kind load docker-image k8s-metrics-cpu:latest --name $ClusterName
kind load docker-image custompodautoscaler/operator:v1.2.1 --name $ClusterName
kind load docker-image registry.k8s.io/hpa-example:latest --name $ClusterName
kind load docker-image registry.k8s.io/metrics-server/metrics-server:v0.6.3 --name $ClusterName
kind load docker-image prom/prometheus:v2.45.0 --name $ClusterName
kind load docker-image registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.9.2 --name $ClusterName
kind load docker-image busybox:latest --name $ClusterName

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  PHASE 2 COMPLETE! Cluster running and images loaded.             " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
