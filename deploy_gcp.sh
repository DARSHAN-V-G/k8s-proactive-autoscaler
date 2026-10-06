#!/usr/bin/env bash
# ==============================================================================
# One-Click Autonomous Deployment for Google Cloud Platform (GCP)
# Provisions GKE Cluster, Google Artifact Registry, builds lightweight ONNX CPA,
# deploys comparative HPA/CPA workloads, and sets up Prometheus monitoring.
# ==============================================================================

set -e

# ANSI Color codes for clean terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  AUTONOMOUS DEPLOYMENT: K8s PROACTIVE AUTOSCALER ON GOOGLE CLOUD   ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# 0. Check gcloud CLI
if ! command -v gcloud &>/dev/null; then
    echo -e "${RED}Error: 'gcloud' CLI is not installed or not in PATH.${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Detect GCP Project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo -e "${YELLOW}Warning: No default GCP project is currently set in gcloud.${NC}"
    read -rp "Please enter your GCP Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

REGION="us-central1"
ZONE="us-central1-a"
CLUSTER_NAME="k8s-autoscaler"
REPO_NAME="autoscaler-images"

echo -e "Target GCP Project : ${CYAN}${PROJECT_ID}${NC}"
echo -e "GCP Region / Zone  : ${CYAN}${REGION} / ${ZONE}${NC}"
echo -e "GKE Cluster Name   : ${CYAN}${CLUSTER_NAME}${NC}"
echo -e "Artifact Registry  : ${CYAN}${REPO_NAME}${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Ensure kubectl is installed
if ! command -v kubectl &>/dev/null; then
    echo -e "\n${YELLOW}kubectl not found. Installing kubectl via gcloud...${NC}"
    sudo gcloud components install kubectl --quiet 2>/dev/null || gcloud components install kubectl --quiet || true
fi

# ------------------------------------------------------------------------------
# Step 1: Enable Cloud APIs
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}[Step 1/7]${NC} Enabling required Google Cloud APIs..."
gcloud services enable container.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       monitoring.googleapis.com --quiet

# ------------------------------------------------------------------------------
# Step 2: Create Google Artifact Registry Repository
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}[Step 2/7]${NC} Setting up Google Artifact Registry repository..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" &>/dev/null; then
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Docker repository for K8s Proactive Autoscaler" --quiet
    echo "Artifact Registry repository created successfully."
else
    echo "Artifact Registry repository already exists."
fi

# ------------------------------------------------------------------------------
# Step 3: Build & Push CPA Image using Cloud Build (No local Docker daemon needed!)
# ------------------------------------------------------------------------------
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/k8s-metrics-cpu:latest"
echo -e "\n${GREEN}[Step 3/7]${NC} Building and pushing lightweight ONNX CPA image via Cloud Build..."
echo "Target Image: ${IMAGE_URI}"
gcloud builds submit --tag "${IMAGE_URI}" ./k8s-metrics-cpu --quiet

# ------------------------------------------------------------------------------
# Step 4: Provision 2-Node GKE Cluster
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Step 5: Configure Kubectl Credentials
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}[Step 5/7]${NC} Fetching GKE cluster credentials for kubectl..."
gcloud container clusters get-credentials "${CLUSTER_NAME}" --zone="${ZONE}"

# ------------------------------------------------------------------------------
# Step 6: Deploy Operator, RBAC, Applications & Autoscalers
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}[Step 6/7]${NC} Deploying Operator, RBAC, Target Deployments & Scalers..."

# 1. Apply CPA Operator and CRD
kubectl apply -f manifests/crd-operator/cpa-operator.yaml

# 2. Grant cluster-admin to operator service account
kubectl create clusterrolebinding cpa-operator-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=default:custom-pod-autoscaler-operator 2>/dev/null || true

# 3. Deploy PHP applications
kubectl apply -f manifests/php-cpa.yaml
kubectl apply -f manifests/php-hpa.yaml

# 4. Deploy HPA (maxReplicas: 30)
kubectl apply -f manifests/hpa.yaml

# 5. Deploy CPA with the GCP Artifact Registry image URI
sed "s|image: k8s-metrics-cpu:latest|image: ${IMAGE_URI}|g" manifests/cpa.yaml | kubectl apply -f -

echo "Waiting for core deployments to become ready..."
kubectl rollout status deployment/php-cpa --timeout=120s
kubectl rollout status deployment/php-hpa --timeout=120s
kubectl rollout status deployment/custom-pod-autoscaler-operator --timeout=120s

# ------------------------------------------------------------------------------
# Step 7: Deploy Monitoring & Autonomous Traffic Pattern Generator
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}[Step 7/7]${NC} Deploying Prometheus Monitoring & Traffic Pattern Generator..."

# Deploy Kube-State-Metrics
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service-account.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/cluster-role-binding.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/examples/standard/service.yaml

# Deploy Prometheus
kubectl apply -f manifests/monitoring/prometheus.yaml

# Deploy Real-Time Latency Exporter
kubectl apply -f manifests/monitoring/latency-exporter.yaml

# Deploy Autonomous Traffic Pattern Bot
kubectl apply -f manifests/traffic-pattern-generator.yaml

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN}  DEPLOYMENT SUCCESSFUL! K8s AUTOSCALER BENCHMARK IS ACTIVE ON GCP  ${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "The autonomous traffic generator is now running cyclic workloads:"
echo -e "  - Phase 1: Low Base Load (90s)       -> ~1-2 pods"
echo -e "  - Phase 2: Traffic Surge (90s)        -> Replicas spike up to 30 (CPA leads!)"
echo -e "  - Phase 3: Cooldown Window (90s)     -> Replicas step down back to 1"
echo ""
echo -e "${CYAN}To watch real-time autoscaling in terminal:${NC}"
echo -e "  ${YELLOW}kubectl get pods,hpa,cpa,deployment -w${NC}"
echo ""
echo -e "${CYAN}To view Prometheus live comparison graphs:${NC}"
echo -e "  1. Run port-forward in a separate terminal:"
echo -e "     ${YELLOW}kubectl port-forward svc/prometheus 9090:9090${NC}"
echo -e "  2. Open in browser: ${YELLOW}http://localhost:9090${NC} (or use GCP Web Preview on port 9090)"
echo -e "  3. Query 1 (Replicas):     ${YELLOW}kube_deployment_status_replicas{deployment=~\"php-.*\"}${NC}"
echo -e "  4. Query 2 (Response Time): ${YELLOW}http_response_time_seconds${NC}"
echo -e "  5. kubectl patch svc prometheus -p '{"spec": {"type": "LoadBalancer"}}'}'"
echo -e "  6. kubectl get svc prometheus -w"
echo -e "${BLUE}====================================================================${NC}"
