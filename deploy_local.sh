#!/usr/bin/env bash
# ==============================================================================
# One-Click Local Deployment & Benchmark Testbed (WSL2 / Linux)
# Provisions Kind cluster, builds lightweight ONNX CPA, installs metrics stack,
# exposes Prometheus on port 9090, and runs autonomous cyclic load waves.
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

CLUSTER_NAME="k8s-autoscaler"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  LOCAL DEPLOYMENT: K8s PROACTIVE AUTOSCALER BENCHMARK TESTBED     ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Navigate to project root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# 0. Check prerequisites
for cmd in docker kind kubectl; do
    if ! command -v $cmd &>/dev/null; then
        echo -e "${RED}Error: '$cmd' is not installed or not in PATH.${NC}"
        exit 1
    fi
done

# Step 1: Create Kind Cluster if not exists
echo -e "\n${GREEN}[Step 1/8]${NC} Checking / Creating Kind cluster '${CLUSTER_NAME}'..."
if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Creating new Kind cluster '${CLUSTER_NAME}'..."
    if [ -f "kind-config.yaml" ]; then
        kind create cluster --config kind-config.yaml
    else
        kind create cluster --name "${CLUSTER_NAME}"
    fi
else
    echo "Kind cluster '${CLUSTER_NAME}' is already active."
fi

# Step 2: Build Lightweight ONNX CPA Docker Image
echo -e "\n${GREEN}[Step 2/8]${NC} Building lightweight ONNX CPA image (k8s-metrics-cpu:latest)..."
docker build -t k8s-metrics-cpu:latest ./k8s-metrics-cpu

# Step 3: Load Docker Image into Kind Cluster
echo -e "\n${GREEN}[Step 3/8]${NC} Loading Docker image into Kind cluster..."
kind load docker-image k8s-metrics-cpu:latest --name "${CLUSTER_NAME}"

# Step 4: Install & Configure Metrics Server for Kind
echo -e "\n${GREEN}[Step 4/8]${NC} Setting up Metrics Server with Kind TLS patches..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"},{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-preferred-address-types=InternalIP"}]' 2>/dev/null || true

# Step 5: Install Custom Pod Autoscaler Operator & CRD
echo -e "\n${GREEN}[Step 5/8]${NC} Installing CPA Operator & granting cluster-admin RBAC..."
kubectl apply -f manifests/crd-operator/cpa-operator.yaml
kubectl create clusterrolebinding cpa-operator-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=default:custom-pod-autoscaler-operator 2>/dev/null || true

# Step 6: Deploy Target Applications & Autoscalers (maxReplicas: 30)
echo -e "\n${GREEN}[Step 6/8]${NC} Deploying php-cpa, php-hpa, and both Autoscalers..."
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml
kubectl apply -f manifests/hpa.yaml
kubectl apply -f manifests/cpa.yaml

# Step 7: Deploy Monitoring Stack (Kube-State-Metrics + Prometheus + Latency Exporter)
echo -e "\n${GREEN}[Step 7/8]${NC} Deploying Prometheus, Kube-State-Metrics, and Latency Exporter..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service-account.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role-binding.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service.yaml
kubectl apply -f manifests/monitoring/prometheus.yaml
kubectl apply -f manifests/monitoring/latency-exporter.yaml

# Step 8: Deploy Autonomous Traffic Pattern Generator
echo -e "\n${GREEN}[Step 8/8]${NC} Launching Autonomous Traffic Pattern Generator..."
kubectl apply -f manifests/traffic-pattern-generator.yaml

# Wait for Prometheus and Latency Exporter to be ready
echo "Waiting for Prometheus and Latency Exporter pods to become ready..."
kubectl rollout status deployment/latency-exporter --timeout=60s 2>/dev/null || true
kubectl rollout status deployment/prometheus --timeout=60s

# Kill any existing port-forward on 9090 and start fresh in background
pkill -f "kubectl port-forward.*9090" 2>/dev/null || true
nohup kubectl port-forward svc/prometheus 9090:9090 > /dev/null 2>&1 &

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN}  LOCAL DEPLOYMENT COMPLETE & RUNNING!                             ${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "Prometheus is live and exposed in the background at: ${CYAN}http://localhost:9090${NC}"
echo ""
echo -e "${YELLOW}Live Prometheus Graphs to Plot in Browser:${NC}"
echo -e "  1. Replicas Comparison : ${CYAN}kube_deployment_status_replicas{deployment=~\"php-.*\"}${NC}"
echo -e "  2. Response Time (QoS) : ${CYAN}http_response_time_seconds${NC}"
echo ""
echo -e "${YELLOW}Terminal Monitoring Commands:${NC}"
echo -e "  • Watch Live Scaling  : ${CYAN}kubectl get pods,hpa,cpa,deployment -w${NC}"
echo -e "  • Watch Traffic Waves : ${CYAN}kubectl logs -f deployment/traffic-pattern-generator${NC}"
echo -e "  • Watch AI Prediction : ${CYAN}kubectl logs -f pod/k8s-metrics-cpu${NC}"
echo ""
echo -e "${RED}When finished, stop & delete everything with: ${CYAN}bash destroy_local.sh${NC}"
echo -e "${BLUE}====================================================================${NC}"
