# 🚀 Live Kubernetes Cluster Deployment Guide (WSL2 + Kind)

This guide walks you through deploying the complete proactive autoscaling testbed and Prometheus monitoring stack onto a local Kubernetes cluster using **WSL2** and **Kind (Kubernetes in Docker)**.

---

## 🛠️ Step 0: Prerequisites in WSL2
Ensure you have the following installed inside your WSL2 terminal:
```bash
# 1. Docker (via Docker Desktop with WSL2 integration enabled)
docker --version

# 2. Kind (Kubernetes in Docker)
# If not installed: curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
kind --version

# 3. Kubectl & Helm
kubectl version --client
helm version
```

---

## 📦 Step 1: Create Local Kubernetes Cluster
Navigate to your repository directory in WSL2:
```bash
cd /mnt/e/Repositories/cloudcomp-k8s-autoscaler/k8s-proactive-autoscaler

# Create 3-node cluster (1 Master + 2 Workers)
kind create cluster --config kind-config.yaml
```

---

## 🏗️ Step 2: Build & Load the Proactive CPA Docker Image
Build the Custom Pod Autoscaler container and load it directly into Kind:
```bash
# 1. Build local container image
docker build -t k8s-metrics-cpu:latest ./k8s-metrics-cpu

# 2. Load the image into the Kind cluster nodes (no registry needed!)
kind load docker-image k8s-metrics-cpu:latest --name k8s-autoscaler
```

---

## ⚙️ Step 3: Install Cluster Metrics Server & CPA Operator
```bash
# 1. Install Metrics Server (required for CPU metrics)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics server for local Kind certificates
kubectl patch -n kube-system deployment metrics-server --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# 2. Install Custom Pod Autoscaler Operator
bash manifests/crd-operator/setup_operator.sh
```

---

## 📊 Step 4: Install Prometheus Monitoring Stack
Deploy Prometheus and `kube-state-metrics` to graph replica counts:
```bash
bash manifests/monitoring/setup_monitoring.sh
```

---

## 🚀 Step 5: Deploy the Target Applications & Autoscalers
Deploy `php-cpa`, `php-hpa`, `cpa.yaml`, `hpa.yaml`, and start the traffic load generator:
```bash
bash manifests/deploy_all.sh
```

---

## 📈 Step 6: View Live Scaling in Real Time!

### 1. View in Terminal (Live Pod Tracking)
```bash
kubectl get pods,hpa,custompodautoscalers -w
```

### 2. View in Browser via Prometheus Dashboard
Open your browser on Windows: **`http://localhost:9090`**

In the Prometheus query bar, enter:
- **Proactive CPA Replicas (Blue line in Figure 21)**:
  ```promql
  kube_deployment_status_replicas{deployment="php-cpa"}
  ```
- **Reactive HPA Replicas (Red line in Figure 21)**:
  ```promql
  kube_deployment_status_replicas{deployment="php-hpa"}
  ```

---

## 🧹 Cleanup
When finished testing, remove all benchmark resources:
```bash
bash manifests/cleanup_all.sh

# To delete the entire Kind cluster:
kind delete cluster --name k8s-autoscaler
```
