#!/usr/bin/env bash
# Shell script to tear down all testbed components cleanly (WSL2/Linux)

echo "==> Tearing down benchmark resources..."

kubectl delete -f manifests/load-generator.yaml --ignore-not-found
kubectl delete -f manifests/cpa.yaml --ignore-not-found
kubectl delete -f manifests/hpa.yaml --ignore-not-found
kubectl delete -f manifests/php-cpa.yaml --ignore-not-found
kubectl delete -f manifests/php-hpa.yaml --ignore-not-found

echo "==> Cleanup complete."
