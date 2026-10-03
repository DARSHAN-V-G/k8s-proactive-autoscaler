#!/usr/bin/env bash
# ==============================================================================
# One-Click Teardown Script for Google Cloud Platform (GCP)
# Deletes the GKE Cluster and Artifact Registry to avoid any cloud costs.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}====================================================================${NC}"
echo -e "${RED}  CLEANUP / TEARDOWN: KUBERNETES PROACTIVE AUTOSCALER ON GCP        ${NC}"
echo -e "${RED}====================================================================${NC}"

CLUSTER_NAME="k8s-autoscaler"
ZONE="us-central1-a"
REGION="us-central1"
REPO_NAME="autoscaler-images"

# 1. Delete GKE Cluster
echo -e "\n${YELLOW}[Step 1/2]${NC} Deleting GKE cluster '${CLUSTER_NAME}' in zone '${ZONE}'..."
if gcloud container clusters describe "${CLUSTER_NAME}" --zone="${ZONE}" &>/dev/null; then
    gcloud container clusters delete "${CLUSTER_NAME}" --zone="${ZONE}" --quiet
    echo -e "${GREEN}GKE cluster deleted.${NC}"
else
    echo "GKE cluster '${CLUSTER_NAME}' not found or already deleted."
fi

# 2. Delete Artifact Registry Repository
echo -e "\n${YELLOW}[Step 2/2]${NC} Deleting Google Artifact Registry repository '${REPO_NAME}'..."
if gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" &>/dev/null; then
    gcloud artifacts repositories delete "${REPO_NAME}" --location="${REGION}" --quiet
    echo -e "${GREEN}Artifact Registry repository deleted.${NC}"
else
    echo "Artifact Registry repository '${REPO_NAME}' not found or already deleted."
fi

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN}  CLEANUP COMPLETE! All GCP resources have been deleted safely.     ${NC}"
echo -e "${BLUE}====================================================================${NC}"
