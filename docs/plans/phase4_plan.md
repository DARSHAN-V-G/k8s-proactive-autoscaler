# Phase 4: Prometheus Monitoring, Simulation & Live Benchmarking

## 🏛️ Architecture Flow Diagram

```mermaid
flowchart TD
    subgraph LiveCluster["Live Kubernetes Cluster (WSL2 + Kind)"]
        subgraph TargetApps["Target Benchmark Deployments"]
            CPA_App["php-cpa (Proactive GRU Autoscaler)"]
            HPA_App["php-hpa (Reactive Native HPA)"]
        end

        LG["Traffic Load Generator (manifests/load-generator.yaml)"]
        LG -->|HTTP Stress Loops| CPA_App
        LG -->|HTTP Stress Loops| HPA_App

        subgraph Monitoring["Prometheus Monitoring Stack (manifests/monitoring/)"]
            Prom["Prometheus Server (Port 9090)"]
            KSM["Kube-State-Metrics"]
            CPA_App -.->|Scrapes Pod Replicas| Prom
            HPA_App -.->|Scrapes Pod Replicas| Prom
            KSM -.->|Cluster Metrics| Prom
            Prom --> UI["Prometheus Graph UI (Figure 21 Line Chart)\n- Blue: php-cpa replicas\n- Red: php-hpa replicas"]
        end
    end

    subgraph OfflineSim["Offline Simulation (sim/simulate_autoscaling.py)"]
        SimTrace["Workload Trace Dataset"] --> SimEngine["Simulator Engine"]
        SimEngine --> Plot["Comparison Plot: docs/plots/scaling_comparison.png"]
    end
```

---

## 📋 Phase 4 Deliverables

1. **Prometheus Monitoring Stack (`manifests/monitoring/`)**:
   - `prometheus.yaml`: Prometheus deployment, ConfigMap, and ClusterIP/NodePort service.
   - `setup_monitoring.sh` / `setup_monitoring.ps1`: Automated installation script for Prometheus & kube-state-metrics.
   - Live Prometheus queries matching Figure 21:
     - `kube_deployment_status_replicas{deployment="php-cpa"}` (Blue line)
     - `kube_deployment_status_replicas{deployment="php-hpa"}` (Red line)
2. **Offline Simulation Engine (`sim/simulate_autoscaling.py`)**:
   - Compares Proactive CPA vs. Reactive HPA over synthetic/Borg traces.
   - Generates `docs/plots/scaling_comparison.png` (reproducing Figure 21).
   - Computes SLA violation reduction and reaction lag metrics.
3. **Live Deployment Guide (`docs/live_cluster_guide.md`)**:
   - Step-by-step instructions for running in WSL2 + Kind.
4. **Automated Verification Tests (`tests/test_simulator.py`)**.
