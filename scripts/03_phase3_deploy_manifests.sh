#!/usr/bin/env bash
# ==============================================================================
# Phase 3: Deploy Operator, CRDs & Target Applications
# Research Paper: "Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  PHASE 3: DEPLOYING K8S OPERATOR, CRDS & TARGET APPLICATIONS       ${NC}"
echo -e "${BLUE}====================================================================${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}Error: kubectl is not installed or not in PATH.${NC}"
    exit 1
fi

# 1. Install Metrics Server (with insecure TLS for Kind)
echo -e "\n${GREEN}[Step 1/5]${NC} Deploying Kubernetes Metrics Server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch -n kube-system deployment metrics-server --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]' || true

# 2. Deploy CPA Operator and RBAC ClusterRole
echo -e "\n${GREEN}[Step 2/5]${NC} Deploying CustomPodAutoscaler Operator & RBAC..."
kubectl apply -f manifests/crd-operator/cpa-operator.yaml

# 3. Deploy Target Benchmarking Applications (php-cpa & php-hpa)
echo -e "\n${GREEN}[Step 3/5]${NC} Deploying Target PHP Deployments (php-cpa & php-hpa)..."
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml

# 4. Deploy Native Reactive HPA and Proactive CustomPodAutoscaler
echo -e "\n${GREEN}[Step 4/5]${NC} Applying Reactive HPA and Proactive CPA Scalers..."
kubectl apply -f manifests/hpa.yaml
kubectl apply -f manifests/cpa.yaml

# 5. Wait for Deployments and Autoscaler Pods to be Available
echo -e "\n${GREEN}[Step 5/5]${NC} Waiting for Pods and Autoscalers to initialize..."
kubectl rollout status deployment/php-cpa --timeout=120s
kubectl rollout status deployment/php-hpa --timeout=120s
kubectl rollout status deployment/custom-pod-autoscaler-operator --timeout=120s

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}  PHASE 3 COMPLETE! Operator, Apps & Scalers are active.           ${NC}"
echo -e "${GREEN}====================================================================${NC}"
kubectl get pods,cpa,hpa
