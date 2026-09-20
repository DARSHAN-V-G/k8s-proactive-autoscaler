#!/usr/bin/env bash
# ==============================================================================
# Phase 2: Build CPA Container & Kind Local Cluster Setup
# Research Paper: "Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

CLUSTER_NAME="k8s-autoscaler"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  PHASE 2: KIND CLUSTER SETUP & CPA DOCKER IMAGE BUILD             ${NC}"
echo -e "${BLUE}====================================================================${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Error: Docker is not installed or running. Please start Docker.${NC}"
    exit 1
fi

# Check Kind
if ! command -v kind &> /dev/null; then
    echo -e "${YELLOW}Error: kind CLI is not installed. Please install kind: https://kind.sigs.k8s.io/${NC}"
    exit 1
fi

# 1. Create 3-Node Kind Cluster if not already existing
echo -e "\n${GREEN}[Step 1/4]${NC} Verifying Kind Cluster '${CLUSTER_NAME}'..."
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster '${CLUSTER_NAME}' is already running."
else
    echo "Creating 3-node Kind cluster from kind-config.yaml..."
    kind create cluster --config kind-config.yaml --name "${CLUSTER_NAME}"
fi

# 2. Build custom k8s-metrics-cpu Docker Image
echo -e "\n${GREEN}[Step 2/4]${NC} Building CPA Docker Image (k8s-metrics-cpu:latest)..."
docker build -t k8s-metrics-cpu:latest ./k8s-metrics-cpu

# 3. Pull required upstream images to local cache
echo -e "\n${GREEN}[Step 3/4]${NC} Pre-pulling upstream Kubernetes images..."
docker pull custompodautoscaler/operator:v1.2.1
docker pull registry.k8s.io/hpa-example:latest
docker pull registry.k8s.io/metrics-server/metrics-server:v0.6.3
docker pull prom/prometheus:v2.45.0
docker pull registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.9.2
docker pull busybox:latest

# 4. Load all container images into Kind cluster nodes
echo -e "\n${GREEN}[Step 4/4]${NC} Sideloading Docker images into Kind nodes..."
kind load docker-image k8s-metrics-cpu:latest --name "${CLUSTER_NAME}"
kind load docker-image custompodautoscaler/operator:v1.2.1 --name "${CLUSTER_NAME}"
kind load docker-image registry.k8s.io/hpa-example:latest --name "${CLUSTER_NAME}"
kind load docker-image registry.k8s.io/metrics-server/metrics-server:v0.6.3 --name "${CLUSTER_NAME}"
kind load docker-image prom/prometheus:v2.45.0 --name "${CLUSTER_NAME}"
kind load docker-image registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.9.2 --name "${CLUSTER_NAME}"
kind load docker-image busybox:latest --name "${CLUSTER_NAME}"

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}  PHASE 2 COMPLETE! Cluster running and images loaded.             ${NC}"
echo -e "${GREEN}====================================================================${NC}"
