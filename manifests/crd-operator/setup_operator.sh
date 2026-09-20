#!/usr/bin/env bash
# Shell script to install Custom Pod Autoscaler Operator into local Kubernetes cluster (WSL2/Linux)

set -e

echo "==> Installing Custom Pod Autoscaler Operator (CRD, RBAC, Deployment)..."
kubectl apply -f manifests/crd-operator/cpa-operator.yaml

echo "==> Waiting for Custom Pod Autoscaler Operator pod to become ready..."
kubectl rollout status deployment/custom-pod-autoscaler-operator --timeout=60s
kubectl get pods -l app=custom-pod-autoscaler-operator
echo "==> Custom Pod Autoscaler Operator installed successfully!"
