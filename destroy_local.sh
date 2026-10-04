#!/usr/bin/env bash
# ==============================================================================
# Teardown Script: Stop & Delete Local Kind Cluster and Background Forwarders
# Kills Prometheus port-forward (port 9090) and deletes the Kind cluster.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CLUSTER_NAME="k8s-autoscaler"

echo -e "${RED}====================================================================${NC}"
echo -e "${RED}  STOPPING & CLEANING UP LOCAL K8s AUTOSCALER TESTBED               ${NC}"
echo -e "${RED}====================================================================${NC}"

# Step 1: Kill background port-forwarding processes
echo -e "\n${YELLOW}[Step 1/2]${NC} Stopping background Prometheus port-forward on port 9090..."
if pgrep -f "kubectl port-forward.*9090" > /dev/null 2>&1; then
    pkill -f "kubectl port-forward.*9090" 2>/dev/null || true
    echo -e "${GREEN}Terminated Prometheus port-forward process.${NC}"
else
    echo "No active Prometheus port-forward found on port 9090."
fi

# Step 2: Delete Kind Cluster
echo -e "\n${YELLOW}[Step 2/2]${NC} Deleting Kind cluster '${CLUSTER_NAME}'..."
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    kind delete cluster --name "${CLUSTER_NAME}"
    echo -e "${GREEN}Kind cluster '${CLUSTER_NAME}' deleted successfully.${NC}"
else
    echo "Kind cluster '${CLUSTER_NAME}' does not exist or was already deleted."
fi

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN}  TEARDOWN COMPLETE! All local containers and clusters removed.    ${NC}"
echo -e "${BLUE}====================================================================${NC}"
