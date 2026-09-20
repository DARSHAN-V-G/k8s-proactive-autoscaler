# Teardown & Cleanup Script (PowerShell)
$ClusterName = "k8s-autoscaler"

Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "  TEARDOWN & CLEANUP                                                " -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Yellow

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "`n[1/4] Deleting Load Generator..." -ForegroundColor Green
kubectl delete -f manifests/load-generator.yaml --ignore-not-found=true

Write-Host "`n[2/4] Deleting Target Applications & Scalers..." -ForegroundColor Green
kubectl delete -f manifests/cpa.yaml --ignore-not-found=true
kubectl delete -f manifests/hpa.yaml --ignore-not-found=true
kubectl delete -f manifests/php-cpa.yaml --ignore-not-found=true
kubectl delete -f manifests/php-hpa.yaml --ignore-not-found=true

Write-Host "`n[3/4] Deleting Monitoring Resources (Prometheus)..." -ForegroundColor Green
kubectl delete -f manifests/monitoring/prometheus.yaml --ignore-not-found=true

Write-Host "`n[4/4] Deleting CPA Operator..." -ForegroundColor Green
kubectl delete -f manifests/crd-operator/cpa-operator.yaml --ignore-not-found=true

Write-Host "`nTo delete the entire Kind cluster and free Docker resources, run:" -ForegroundColor Green
Write-Host "kind delete cluster --name $ClusterName" -ForegroundColor Yellow

Write-Host "`nCleanup completed!" -ForegroundColor Green
