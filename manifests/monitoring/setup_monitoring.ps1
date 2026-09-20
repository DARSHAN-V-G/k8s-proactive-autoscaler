# Setup Prometheus & Kube-State-Metrics monitoring stack in Kubernetes (PowerShell)

Write-Host "==> 1. Deploying Kube-State-Metrics..." -ForegroundColor Cyan
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service-account.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role-binding.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service.yaml

Write-Host "==> 2. Deploying Prometheus Server..." -ForegroundColor Cyan
kubectl apply -f manifests/monitoring/prometheus.yaml

Write-Host "==> 3. Waiting for Prometheus Pod to be Ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available deployment/prometheus --timeout=90s

Write-Host "`n==> Prometheus monitoring is ready!" -ForegroundColor Green
Write-Host "==> Access Prometheus UI: http://localhost:9090 (or 'kubectl port-forward svc/prometheus 9090:9090')" -ForegroundColor Yellow
