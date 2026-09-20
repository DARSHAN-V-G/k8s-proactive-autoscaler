#!/usr/bin/env bash
# Setup Prometheus & Kube-State-Metrics monitoring stack in Kubernetes (WSL2/Linux)

set -e

echo "==> 1. Deploying Kube-State-Metrics (exposes deployment replica metrics)..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service-account.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role-binding.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service.yaml

echo "==> 2. Deploying Prometheus Server..."
kubectl apply -f manifests/monitoring/prometheus.yaml

echo "==> 3. Waiting for Prometheus Pod to be Ready..."
kubectl rollout status deployment/prometheus --timeout=90s

echo ""
echo "==> Prometheus monitoring is ready!"
echo "==> Access the Prometheus UI at: http://localhost:9090 (or via 'kubectl port-forward svc/prometheus 9090:9090')"
