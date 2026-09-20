#!/usr/bin/env bash
# ==============================================================================
# Phase 4: Observability, Traffic Stress Testing & Benchmark Simulation
# Research Paper: "Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  PHASE 4: MONITORING, TRAFFIC GENERATION & SIMULATION REPORT       ${NC}"
echo -e "${BLUE}====================================================================${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_CMD=$(command -v python3 || command -v python)

# 1. Deploy Prometheus & Kube-State-Metrics Monitoring
echo -e "\n${GREEN}[Step 1/4]${NC} Deploying Prometheus and Kube-State-Metrics..."
kubectl apply -f manifests/monitoring/prometheus.yaml
kubectl rollout status deployment/prometheus --timeout=120s

# 2. Deploy Traffic Load Generator (Stress Testing php-cpa & php-hpa)
echo -e "\n${GREEN}[Step 2/4]${NC} Launching Traffic Load Generator..."
kubectl apply -f manifests/load-generator.yaml
kubectl scale deployment load-generator --replicas=5
kubectl rollout status deployment/load-generator --timeout=60s

# 3. Run Standalone Offline Autoscaling Simulation
echo -e "\n${GREEN}[Step 3/4]${NC} Running Offline Autoscaling Simulation (Figure 21 Replication)..."
$PYTHON_CMD sim/simulate_autoscaling.py

# 4. Display Live Status & Prometheus Dashboard Info
echo -e "\n${GREEN}[Step 4/4]${NC} Live Cluster Status Summary:"
kubectl get deployment php-cpa php-hpa
echo ""
kubectl get pods

echo -e "\n${CYAN}====================================================================${NC}"
echo -e "${CYAN}  OBSERVABILITY & MONITORING INSTRUCTIONS                           ${NC}"
echo -e "${CYAN}====================================================================${NC}"
echo -e "1. Forward Prometheus port to view live scaling graph in your browser:"
echo -e "   ${YELLOW}kubectl port-forward svc/prometheus 9090:9090${NC}"
echo -e "2. Open Prometheus in your browser:"
echo -e "   ${YELLOW}http://localhost:9090${NC}"
echo -e "3. Execute query in Prometheus Expression bar:"
echo -e "   ${YELLOW}kube_deployment_status_replicas{deployment=~\"php-.*\"}${NC}"
echo -e "4. Offline simulation comparison plot saved to:"
echo -e "   ${YELLOW}docs/plots/scaling_comparison.png${NC}"
echo -e "${CYAN}====================================================================${NC}"
