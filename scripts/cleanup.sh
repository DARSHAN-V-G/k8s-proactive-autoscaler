#!/usr/bin/env bash
# ==============================================================================
# Teardown & Cleanup Script
# Research Paper: "Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"
# ==============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CLUSTER_NAME="k8s-autoscaler"

echo -e "${YELLOW}====================================================================${NC}"
echo -e "${YELLOW}  TEARDOWN & CLEANUP                                                ${NC}"
echo -e "${YELLOW}====================================================================${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo -e "\n${GREEN}[1/4]${NC} Deleting Load Generator..."
kubectl delete -f manifests/load-generator.yaml --ignore-not-found=true

echo -e "\n${GREEN}[2/4]${NC} Deleting Target Applications & Scalers (CPA, HPA, php-cpa, php-hpa)..."
kubectl delete -f manifests/cpa.yaml --ignore-not-found=true
kubectl delete -f manifests/hpa.yaml --ignore-not-found=true
kubectl delete -f manifests/php-cpa.yaml --ignore-not-found=true
kubectl delete -f manifests/php-hpa.yaml --ignore-not-found=true

echo -e "\n${GREEN}[3/4]${NC} Deleting Monitoring Resources (Prometheus)..."
kubectl delete -f manifests/monitoring/prometheus.yaml --ignore-not-found=true

echo -e "\n${GREEN}[4/4]${NC} Deleting CPA Operator..."
kubectl delete -f manifests/crd-operator/cpa-operator.yaml --ignore-not-found=true

echo -e "\n${GREEN}To delete the entire Kind cluster and free Docker resources, run:${NC}"
echo -e "${YELLOW}kind delete cluster --name ${CLUSTER_NAME}${NC}"

echo -e "\n${GREEN}Cleanup completed!${NC}"
