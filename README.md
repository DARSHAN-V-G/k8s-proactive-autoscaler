# Kubernetes Proactive Autoscaler (GRU-Based CPA)

[![Paper](https://img.shields.io/badge/Paper-MDPI%20Mathematics%202023-blue)](https://doi.org/10.3390/math11122675)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Implementation of the proactive cloud autoscaler proposed in the research paper:
> **"Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"**  
> *Subrota Kumar Mondal, Xiaohai Wu, Hussain Mohammed Dipu Kabir, Hong-Ning Dai, Kan Ni, Honggang Yuan, Ting Wang*  
> *MDPI Mathematics, 2023, 11(12), 2675.*

---

## 🎯 Key Concepts & Motivation

Standard Kubernetes **Horizontal Pod Autoscaler (HPA)** is purely reactive:
$$\text{desiredReplicas} = \left\lceil \text{currentReplicas} \times \frac{\text{currentMetricValue}}{\text{desiredMetricValue}} \right\rceil$$

When sudden surges or flash crowds occur, reactive HPA experiences a **50–60 second delay** before triggering scale-up. This delay causes QoS violations, long tail latency, and dropped requests.

### The Proposed Proactive Solution
This project implements a **Custom Pod Autoscaler (CPA)** driven by a **24-Step Gated Recurrent Unit (GRU)** deep learning model:
1. **Load Prediction**: Analyzes sliding sequence history of length 24 ($Seq[]$) to forecast the upcoming CPU load ($Pre\_u$).
2. **Proactive Scaling**: Scales deployment replicas *in advance*:
   $$\text{Tar\_r} = \left\lceil \text{Cur\_r} \times \frac{\text{Pre\_u}}{\text{Tar\_ut}} \right\rceil \quad (\text{Target threshold } \text{Tar\_ut} = 50\%)$$
3. **Reactive Fallback**: If history is insufficient ($Seq\_len < 24$) or prediction evaluates to 0, automatically falls back to reactive HPA calculation using average CPU ($Avg\_u$).
4. **Stabilization Window**: 60s cooldown downscale window prevents pod flapping / oscillation.

---

## 📁 Repository Structure

```
k8s-proactive-autoscaler/
├── data/                               # Dataset ingestion & synthetic trace generator
│   ├── generate_synthetic_trace.py     # Generates Borg/Alibaba-style diurnal + burst traces
│   └── dataset_loader.py               # Preprocessing, normalization & 24-step sliding window
├── model/                              # Model architectures, training & evaluation
│   ├── gru_model.py                    # GRU predictor (50 hidden units) & ONNX inference engine
│   ├── baseline_models.py              # ARIMA(3,1,2), LSTM(50), BiLSTM(100) baselines
│   ├── train.py                        # Training pipeline & ONNX model exporter
│   ├── evaluate.py                     # Empirical benchmark script (reproduces Paper Table 3)
│   └── saved_models/                   # Trained weights & exported ONNX models
│       ├── GRU_Model_24.onnx           # Lightweight ONNX model (<15ms latency)
│       └── scaler.json                 # Fitted min-max scaler bounds
├── k8s-metrics-cpu/                    # Custom Pod Autoscaler container runtime (Phase 2)
│   ├── metric.py                       # Metric Gatherer script (Figure 19 in paper)
│   ├── evaluate.py                     # Evaluator & GRU inference script (Figure 20 in paper)
│   ├── config.yaml                     # CPA execution configuration
│   └── Dockerfile                      # Container image definition
├── manifests/                          # Kubernetes manifests & test workloads (Phase 3)
│   ├── php-cpa.yaml                    # Proactive scaling target deployment
│   ├── php-hpa.yaml                    # Reactive baseline target deployment
│   ├── cpa.yaml                        # CustomPodAutoscaler CRD definition
│   └── load-generator.yaml             # HTTP stress test generator
├── tests/                              # Unit & integration test suite
│   ├── test_data_pipeline.py           # Data loader, scaling & windowing tests
│   └── test_gru_model.py               # Model architecture, ONNX export & latency tests
├── train_colab.ipynb                   # Self-contained Google Colab notebook
└── requirements.txt                    # Project Python dependencies
```

---

## 🚀 Automated Deployment & Testing (By Phase)

We provide modular automation scripts for each phase under the `scripts/` folder (available for both **Bash** and **PowerShell**):

| Phase | Bash Script | PowerShell Script | Description |
| :--- | :--- | :--- | :--- |
| **Phase 1** | `bash scripts/01_phase1_train_model.sh` | `.\scripts\01_phase1_train_model.ps1` | Generates Borg workload traces, trains 24-step GRU model, evaluates baselines (Table 3), and syncs weights. |
| **Phase 2** | `bash scripts/02_phase2_build_cpa.sh` | `.\scripts\02_phase2_build_cpa.ps1` | Creates 3-node Kind cluster, builds `k8s-metrics-cpu` CPA Docker image, and sideloads images into Kind nodes. |
| **Phase 3** | `bash scripts/03_phase3_deploy_manifests.sh` | `.\scripts\03_phase3_deploy_manifests.ps1` | Deploys Metrics Server, CPA Operator & RBAC, target apps (`php-cpa`, `php-hpa`), and scalers (CPA, HPA). |
| **Phase 4** | `bash scripts/04_phase4_test_and_monitor.sh` | `.\scripts\04_phase4_test_and_monitor.ps1` | Deploys Prometheus, launches 5-replica stress load generator, runs offline simulation report, and prints Prometheus instructions. |
| **Run All** | `bash scripts/run_all.sh` | `.\scripts\run_all.ps1` | Executes all 4 phases end-to-end sequentially. |
| **Teardown** | `bash scripts/cleanup.sh` | `.\scripts\cleanup.ps1` | Tears down Kubernetes deployments, CRDs, monitoring, and cleans up resources. |

---

## 📊 Live Observability & Prometheus Monitoring

1. **Port-forward Prometheus**:
   ```bash
   kubectl port-forward svc/prometheus 9090:9090
   ```
2. **Open Dashboard**:
   Navigate to `http://localhost:9090` in your web browser.
3. **Execute Replica Query**:
   ```promql
   kube_deployment_status_replicas{deployment=~"php-.*"}
   ```
   Visualizes both the proactive CPA (`php-cpa`, green) and reactive HPA (`php-hpa`, blue) curves in real-time.

---

## 🧪 Automated Unit Tests
```bash
pytest tests/ -v
```

