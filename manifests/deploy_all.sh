#!/usr/bin/env bash
# Shell script to deploy the full comparative testbed to Kubernetes (WSL2/Linux)
# Matches Listing 17 from MDPI Mathematics 2023 paper

set -e

echo "=========================================================="
echo " Deploying Proactive CPA vs Reactive HPA Benchmark Testbed"
echo "=========================================================="

echo "==> 1. Deploying Target Applications (php-cpa & php-hpa)..."
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml

echo "==> 2. Waiting for Deployments to become Available..."
kubectl wait --for=condition=available deployment/php-cpa --timeout=60s
kubectl wait --for=condition=available deployment/php-hpa --timeout=60s

echo "==> 3. Deploying Autoscalers (CustomPodAutoscaler & Native HPA)..."
kubectl apply -f manifests/cpa.yaml
kubectl apply -f manifests/hpa.yaml

echo "==> 4. Deploying Traffic Load Generator..."
kubectl apply -f manifests/load-generator.yaml

echo ""
echo "==> All components deployed successfully!"
echo "==> Monitor scaling live with: kubectl get pods,hpa,custompodautoscalers -w"
