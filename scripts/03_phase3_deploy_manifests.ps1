# Phase 3: Deploy Operator, CRDs & Target Applications (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  PHASE 3: DEPLOYING K8S OPERATOR, CRDS & TARGET APPLICATIONS       " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# 1. Install Metrics Server
Write-Host "`n[Step 1/5] Deploying Kubernetes Metrics Server..." -ForegroundColor Green
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch -n kube-system deployment metrics-server --type=json -p '[{\"op\":\"add\",\"path\":\"/spec/template/spec/containers/0/args/-\",\"value\":\"--kubelet-insecure-tls\"}]' 2>$null

# 2. Deploy CPA Operator & RBAC
Write-Host "`n[Step 2/5] Deploying CustomPodAutoscaler Operator & RBAC..." -ForegroundColor Green
kubectl apply -f manifests/crd-operator/cpa-operator.yaml

# 3. Deploy Target PHP Applications
Write-Host "`n[Step 3/5] Deploying Target PHP Deployments (php-cpa & php-hpa)..." -ForegroundColor Green
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml

# 4. Deploy Reactive HPA and Proactive CPA Scalers
Write-Host "`n[Step 4/5] Applying Reactive HPA and Proactive CPA Scalers..." -ForegroundColor Green
kubectl apply -f manifests/hpa.yaml
kubectl apply -f manifests/cpa.yaml

# 5. Wait for Deployments
Write-Host "`n[Step 5/5] Waiting for Pods and Autoscalers to initialize..." -ForegroundColor Green
kubectl rollout status deployment/php-cpa --timeout=120s
kubectl rollout status deployment/php-hpa --timeout=120s
kubectl rollout status deployment/custom-pod-autoscaler-operator --timeout=120s

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  PHASE 3 COMPLETE! Operator, Apps & Scalers are active.           " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
kubectl get pods,cpa,hpa
