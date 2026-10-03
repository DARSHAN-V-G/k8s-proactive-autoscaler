#!/usr/bin/env bash
# ==============================================================================
# End-to-End Automated Deployment for Google Cloud Platform (GKE + GAR)
# Matches Project Write-up:
# - Google Kubernetes Engine (GKE) Cluster
# - Google Artifact Registry (GAR) Container Repository
# - Custom Pod Autoscaler (CPA) with 24-Step GRU Neural Network
# - Native Reactive Horizontal Pod Autoscaler (HPA)
# - Autonomous Traffic Pattern Generator
# - Prometheus & Kube-State-Metrics Monitoring
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  AUTONOMOUS DEPLOYMENT: KUBERNETES PROACTIVE AUTOSCALER ON GCP     ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Detect GCP Project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Error: No active GCP project detected.${NC}"
    echo "Please set your project using: gcloud config set project <YOUR_PROJECT_ID>"
    exit 1
fi

REGION="us-central1"
ZONE="us-central1-a"
CLUSTER_NAME="k8s-autoscaler"
REPO_NAME="autoscaler-images"

echo -e "Target GCP Project : ${CYAN}${PROJECT_ID}${NC}"
echo -e "Region / Zone      : ${CYAN}${REGION} / ${ZONE}${NC}"
echo -e "Cluster Name       : ${CYAN}${CLUSTER_NAME}${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Step 1: Enable Cloud APIs
echo -e "\n${GREEN}[Step 1/7]${NC} Enabling required Google Cloud APIs..."
gcloud services enable container.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       monitoring.googleapis.com --quiet

# Step 2: Create Artifact Registry
echo -e "\n${GREEN}[Step 2/7]${NC} Setting up Google Artifact Registry repository..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" &>/dev/null; then
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Docker repository for K8s Proactive Autoscaler" --quiet
    echo "Artifact Registry repository created."
else
    echo "Artifact Registry repository already exists."
fi

# Step 3: Build & Push CPA Container Image via Cloud Build
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/k8s-metrics-cpu:latest"
echo -e "\n${GREEN}[Step 3/7]${NC} Building and pushing CPA image with Cloud Build..."
echo "Target Image: ${IMAGE_URI}"
gcloud builds submit --tag "${IMAGE_URI}" ./k8s-metrics-cpu --quiet

# Step 4: Provision 3-Node GKE Cluster
echo -e "\n${GREEN}[Step 4/7]${NC} Provisioning Google Kubernetes Engine (GKE) Cluster..."
if ! gcloud container clusters describe "${CLUSTER_NAME}" --zone="${ZONE}" &>/dev/null; then
    gcloud container clusters create "${CLUSTER_NAME}" \
        --zone="${ZONE}" \
        --num-nodes=2 \
        --machine-type=e2-standard-2 \
        --scopes="https://www.googleapis.com/auth/cloud-platform" \
        --quiet
    echo "GKE cluster provisioned successfully."
else
    echo "GKE cluster '${CLUSTER_NAME}' is already active."
fi

# Step 5: Connect kubectl
echo -e "\n${GREEN}[Step 5/7]${NC} Configuring kubectl credentials..."
gcloud container clusters get-credentials "${CLUSTER_NAME}" --zone="${ZONE}"

# Step 6: Deploy Operator, Applications & Scalers
echo -e "\n${GREEN}[Step 6/7]${NC} Deploying workloads and autoscalers to GKE..."
kubectl apply -f manifests/crd-operator/cpa-operator.yaml
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml

# Temporarily point CPA manifest to the GAR image
sed "s|image: k8s-metrics-cpu:latest|image: ${IMAGE_URI}|g" manifests/cpa.yaml | kubectl apply -f -
kubectl apply -f manifests/hpa.yaml

# Wait for rollout
echo "Waiting for core services to become ready..."
kubectl rollout status deployment/php-cpa --timeout=180s
kubectl rollout status deployment/php-hpa --timeout=180s
kubectl rollout status deployment/custom-pod-autoscaler-operator --timeout=180s

# Step 7: Deploy Monitoring & Autonomous Traffic Generator
echo -e "\n${GREEN}[Step 7/7]${NC} Launching Prometheus Monitoring & Autonomous Traffic Pattern..."
# Deploy Kube-State-Metrics & Prometheus
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service-account.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role-binding.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service.yaml
kubectl apply -f manifests/monitoring/prometheus.yaml

# Launch Autonomous Traffic Pattern Bot
kubectl apply -f manifests/traffic-pattern-generator.yaml

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE! PROACTIVE AUTOSCALER IS ACTIVE ON GKE       ${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "The Autonomous Traffic Generator is now continuously cycling waves:"
echo -e "  - 2 Minutes Base Load (1 Pod)"
echo -e "  - 2.5 Minutes Flash Surge (CPA pre-scales ahead of HPA)"
echo -e "  - 2 Minutes Cooldown"
echo ""
echo -e "${CYAN}To view live scaling in terminal:${NC}"
echo -e "  ${YELLOW}kubectl get pods,hpa,cpa -w${NC}"
echo ""
echo -e "${CYAN}To view live Prometheus comparison graph:${NC}"
echo -e "  1. Run: ${YELLOW}kubectl port-forward svc/prometheus 9090:9090${NC}"
echo -e "  2. In Cloud Shell, click 'Web Preview' -> 'Preview on port 9090'"
echo -e "  3. Query: ${YELLOW}kube_deployment_status_replicas{deployment=~\"php-.*\"}${NC}"
echo -e "${BLUE}====================================================================${NC}"
