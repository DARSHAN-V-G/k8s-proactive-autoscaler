# PowerShell script to deploy the full comparative testbed to Kubernetes
# Matches Listing 17 from MDPI Mathematics 2023 paper

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Deploying Proactive CPA vs Reactive HPA Benchmark Testbed" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Write-Host "1. Deploying Target Applications (php-cpa & php-hpa)..." -ForegroundColor Yellow
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml

Write-Host "2. Waiting for Deployments to become Available..." -ForegroundColor Yellow
kubectl wait --for=condition=available deployment/php-cpa --timeout=60s
kubectl wait --for=condition=available deployment/php-hpa --timeout=60s

Write-Host "3. Deploying Autoscalers (CustomPodAutoscaler & Native HPA)..." -ForegroundColor Yellow
kubectl apply -f manifests/cpa.yaml
kubectl apply -f manifests/hpa.yaml

Write-Host "4. Deploying Traffic Load Generator..." -ForegroundColor Yellow
kubectl apply -f manifests/load-generator.yaml

Write-Host "`nAll components deployed successfully!" -ForegroundColor Green
Write-Host "Monitor scaling live with: kubectl get pods,hpa,custompodautoscalers -w" -ForegroundColor Cyan
