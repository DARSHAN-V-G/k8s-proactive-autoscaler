"""
Generate high-resolution visual architectural diagrams for all phases.
Saves PNG diagram images to docs/plans/images/
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def create_phase1_diagram(output_path="docs/plans/images/phase1_architecture.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # Background canvas
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    # Title
    ax.text(7, 6.5, "Phase 1: Workload Data Pipeline & GRU Model Training", 
            fontsize=16, fontweight="bold", ha="center", color="#0f172a")

    # Box 1: Data Ingestion
    rect1 = patches.FancyBboxPatch((0.5, 3.2), 3.2, 2.4, boxstyle="round,pad=0.15", 
                                  facecolor="#e0f2fe", edgecolor="#0284c7", linewidth=2)
    ax.add_patch(rect1)
    ax.text(2.1, 5.2, "1. Trace Ingestion", fontsize=12, fontweight="bold", ha="center", color="#0369a1")
    ax.text(2.1, 4.4, "Synthetic / Borg Traces\n8,352 steps @ 300s\n(Diurnal + Noise + Spikes)", 
            fontsize=9.5, ha="center", color="#1e293b")

    # Box 2: Preprocessing
    rect2 = patches.FancyBboxPatch((4.3, 3.2), 3.4, 2.4, boxstyle="round,pad=0.15", 
                                  facecolor="#fef3c7", edgecolor="#d97706", linewidth=2)
    ax.add_patch(rect2)
    ax.text(6.0, 5.2, "2. Preprocessing", fontsize=12, fontweight="bold", ha="center", color="#b45309")
    ax.text(6.0, 4.3, "Min-Max Normalization\n24-Step Sliding Window\nX: (N, 24, 1)\ny: (N, 1)", 
            fontsize=9.5, ha="center", color="#1e293b")

    # Box 3: Model Training
    rect3 = patches.FancyBboxPatch((8.3, 3.2), 5.2, 2.4, boxstyle="round,pad=0.15", 
                                  facecolor="#dcfce7", edgecolor="#16a34a", linewidth=2)
    ax.add_patch(rect3)
    ax.text(10.9, 5.2, "3. Model Training & Comparison", fontsize=12, fontweight="bold", ha="center", color="#15803d")
    ax.text(10.9, 4.3, "• GRU_Model_24 (50 Units, ReLU, Adam)\n• Baselines: ARIMA(3,1,2), LSTM, BiLSTM\n• Metrics: MSE (0.00142), Speed (0.55ms)", 
            fontsize=9.5, ha="center", color="#1e293b")

    # Box 4: Serialization
    rect4 = patches.FancyBboxPatch((4.3, 0.5), 5.4, 1.8, boxstyle="round,pad=0.15", 
                                  facecolor="#f3e8ff", edgecolor="#9333ea", linewidth=2)
    ax.add_patch(rect4)
    ax.text(7.0, 1.8, "4. Lightweight Model Serialization", fontsize=12, fontweight="bold", ha="center", color="#7e22ce")
    ax.text(7.0, 1.1, "• GRU_Model_24.pt (TorchScript JIT Standalone)\n• GRU_Model_24.onnx (ONNX Runtime)\n• scaler.json (Min/Max Bounds)", 
            fontsize=9.5, ha="center", color="#1e293b")

    # Connecting Arrows
    arrow_props = dict(arrowstyle="->", color="#475569", lw=2.5, mutation_scale=18)
    ax.annotate("", xy=(4.2, 4.4), xytext=(3.8, 4.4), arrowprops=arrow_props)
    ax.annotate("", xy=(8.2, 4.4), xytext=(7.8, 4.4), arrowprops=arrow_props)
    ax.annotate("", xy=(7.0, 2.4), xytext=(7.0, 3.1), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {output_path}")


def create_phase2_diagram(output_path="docs/plans/images/phase2_architecture.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 8), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8)
    ax.axis("off")

    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    ax.text(7.5, 7.5, "Phase 2: Custom Pod Autoscaler (CPA) Engine Flow", 
            fontsize=16, fontweight="bold", ha="center", color="#0f172a")

    # Metrics Server
    p1 = patches.FancyBboxPatch((0.5, 4.8), 3.0, 1.8, boxstyle="round,pad=0.15", 
                                facecolor="#e0f2fe", edgecolor="#0284c7", linewidth=2)
    ax.add_patch(p1)
    ax.text(2.0, 5.9, "K8s Metrics Server", fontsize=11, fontweight="bold", ha="center", color="#0369a1")
    ax.text(2.0, 5.2, "Resource Metrics API\n(Pod CPU Usage)", fontsize=9, ha="center", color="#1e293b")

    # Metric Gatherer
    p2 = patches.FancyBboxPatch((4.3, 4.8), 3.4, 1.8, boxstyle="round,pad=0.15", 
                                facecolor="#fef3c7", edgecolor="#d97706", linewidth=2)
    ax.add_patch(p2)
    ax.text(6.0, 5.9, "Metric Gatherer (metric.py)", fontsize=11, fontweight="bold", ha="center", color="#b45309")
    ax.text(6.0, 5.2, "• Computes Cur_r, Tot_u\n• Calculates Avg_u = Tot_u/Cur_r\n• Emits {'cur_r', 'avg_u'}", 
            fontsize=8.5, ha="center", color="#1e293b")

    # SQLite DB
    p3 = patches.FancyBboxPatch((4.3, 1.2), 3.4, 2.2, boxstyle="round,pad=0.15", 
                                facecolor="#f1f5f9", edgecolor="#64748b", linewidth=2)
    ax.add_patch(p3)
    ax.text(6.0, 2.9, "SQLite DB (metrics.db)", fontsize=11, fontweight="bold", ha="center", color="#334155")
    ax.text(6.0, 2.0, "• Table: metrics_history\n• Stores Seq[] sliding window\n• Auto-prunes to 1000 records", 
            fontsize=8.5, ha="center", color="#1e293b")

    # Evaluator
    p4 = patches.FancyBboxPatch((8.7, 4.0), 3.4, 2.8, boxstyle="round,pad=0.15", 
                                facecolor="#dcfce7", edgecolor="#16a34a", linewidth=2)
    ax.add_patch(p4)
    ax.text(10.4, 6.3, "Evaluator (evaluate.py)", fontsize=11, fontweight="bold", ha="center", color="#15803d")
    ax.text(10.4, 5.0, "Decision Logic:\n• If Seq_len >= 24:\n   GRU predicts Pre_u\n   Tar_r = ceil(Cur_r * Pre_u/50%)\n• Else (Fallback):\n   Tar_r = ceil(Cur_r * Avg_u/50%)", 
            fontsize=8.5, ha="center", color="#1e293b")

    # Target Deployment
    p5 = patches.FancyBboxPatch((12.6, 4.8), 2.0, 1.8, boxstyle="round,pad=0.15", 
                                facecolor="#f3e8ff", edgecolor="#9333ea", linewidth=2)
    ax.add_patch(p5)
    ax.text(13.6, 5.9, "Target Pods", fontsize=11, fontweight="bold", ha="center", color="#7e22ce")
    ax.text(13.6, 5.2, "php-cpa\nDeployment\n(Scale: Tar_r)", fontsize=9, ha="center", color="#1e293b")

    # Model file
    p6 = patches.FancyBboxPatch((8.7, 1.2), 3.4, 2.0, boxstyle="round,pad=0.15", 
                                facecolor="#ffe4e6", edgecolor="#e11d48", linewidth=2)
    ax.add_patch(p6)
    ax.text(10.4, 2.7, "GRU_Model_24.pt", fontsize=11, fontweight="bold", ha="center", color="#be123c")
    ax.text(10.4, 1.8, "Pre-trained TorchScript JIT\nInference Latency: 0.55ms", fontsize=8.5, ha="center", color="#1e293b")

    # Connecting Arrows
    arrow_props = dict(arrowstyle="->", color="#334155", lw=2, mutation_scale=15)
    ax.annotate("", xy=(4.2, 5.7), xytext=(3.6, 5.7), arrowprops=arrow_props)
    ax.annotate("", xy=(6.0, 3.5), xytext=(6.0, 4.7), arrowprops=arrow_props)
    ax.annotate("", xy=(8.6, 5.7), xytext=(7.8, 5.7), arrowprops=arrow_props)
    ax.annotate("", xy=(8.6, 5.0), xytext=(7.8, 2.5), arrowprops=dict(arrowstyle="->", color="#334155", lw=2, linestyle="--"))
    ax.annotate("", xy=(10.4, 3.9), xytext=(10.4, 3.3), arrowprops=arrow_props)
    ax.annotate("", xy=(12.5, 5.7), xytext=(12.2, 5.7), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {output_path}")


def create_phase3_diagram(output_path="docs/plans/images/phase3_architecture.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 8), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8)
    ax.axis("off")

    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    ax.text(7.5, 7.5, "Phase 3: Kubernetes Cluster Testbed & Dual-Autoscaler Layout", 
            fontsize=16, fontweight="bold", ha="center", color="#0f172a")

    # Load Generator
    p_load = patches.FancyBboxPatch((0.5, 3.0), 3.0, 2.5, boxstyle="round,pad=0.15", 
                                   facecolor="#ffe4e6", edgecolor="#e11d48", linewidth=2)
    ax.add_patch(p_load)
    ax.text(2.0, 5.0, "Traffic Load Generator", fontsize=11, fontweight="bold", ha="center", color="#be123c")
    ax.text(2.0, 3.8, "manifests/load-generator.yaml\n• Bursty HTTP Loops\n• Step-load Traffic\n• Parallel Synchronized", 
            fontsize=8.5, ha="center", color="#1e293b")

    # Proactive Branch (Upper)
    p_cpa = patches.FancyBboxPatch((4.5, 4.3), 4.5, 2.5, boxstyle="round,pad=0.15", 
                                  facecolor="#dcfce7", edgecolor="#16a34a", linewidth=2)
    ax.add_patch(p_cpa)
    ax.text(6.75, 6.3, "Proactive Scheme (Custom Pod Autoscaler)", fontsize=11, fontweight="bold", ha="center", color="#15803d")
    ax.text(6.75, 5.1, "• manifests/cpa.yaml (CustomPodAutoscaler CRD)\n• k8s-metrics-cpu Pod (GRU Evaluator)\n• Interval: 10s, DownscaleStabilization: 60s", 
            fontsize=8.5, ha="center", color="#1e293b")

    p_cpa_pod = patches.FancyBboxPatch((9.8, 4.3), 4.6, 2.5, boxstyle="round,pad=0.15", 
                                      facecolor="#f0fdf4", edgecolor="#22c55e", linewidth=2)
    ax.add_patch(p_cpa_pod)
    ax.text(12.1, 6.3, "Target App: php-cpa", fontsize=11, fontweight="bold", ha="center", color="#15803d")
    ax.text(12.1, 5.1, "• manifests/php-cpa.yaml\n• CPU Request: 50m, Limit: 500m\n• Scaled proactively by CPA", 
            fontsize=8.5, ha="center", color="#1e293b")

    # Reactive Branch (Lower)
    p_hpa = patches.FancyBboxPatch((4.5, 0.8), 4.5, 2.5, boxstyle="round,pad=0.15", 
                                  facecolor="#fef3c7", edgecolor="#d97706", linewidth=2)
    ax.add_patch(p_hpa)
    ax.text(6.75, 2.8, "Reactive Baseline (Native K8s HPA)", fontsize=11, fontweight="bold", ha="center", color="#b45309")
    ax.text(6.75, 1.6, "• manifests/hpa.yaml (HorizontalPodAutoscaler)\n• Target: 50% CPU Utilization\n• Min: 1, Max: 20 Replicas", 
            fontsize=8.5, ha="center", color="#1e293b")

    p_hpa_pod = patches.FancyBboxPatch((9.8, 0.8), 4.6, 2.5, boxstyle="round,pad=0.15", 
                                      facecolor="#fffbeb", edgecolor="#f59e0b", linewidth=2)
    ax.add_patch(p_hpa_pod)
    ax.text(12.1, 2.8, "Target App: php-hpa", fontsize=11, fontweight="bold", ha="center", color="#b45309")
    ax.text(12.1, 1.6, "• manifests/php-hpa.yaml\n• Identical resource constraints\n• Scaled reactively by HPA", 
            fontsize=8.5, ha="center", color="#1e293b")

    # Arrows
    arrow_props = dict(arrowstyle="->", color="#334155", lw=2, mutation_scale=15)
    ax.annotate("", xy=(4.4, 5.5), xytext=(3.6, 4.8), arrowprops=arrow_props)
    ax.annotate("", xy=(4.4, 2.0), xytext=(3.6, 3.8), arrowprops=arrow_props)
    ax.annotate("", xy=(9.7, 5.5), xytext=(9.1, 5.5), arrowprops=arrow_props)
    ax.annotate("", xy=(9.7, 2.0), xytext=(9.1, 2.0), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {output_path}")


def create_phase4_diagram(output_path="docs/plans/images/phase4_architecture.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 7.5), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    ax.text(7.5, 7.0, "Phase 4: Verification, Simulation & Live Benchmarking", 
            fontsize=16, fontweight="bold", ha="center", color="#0f172a")

    # Path A: Simulator
    p_sim = patches.FancyBboxPatch((0.5, 1.2), 6.5, 4.8, boxstyle="round,pad=0.15", 
                                  facecolor="#eff6ff", edgecolor="#3b82f6", linewidth=2)
    ax.add_patch(p_sim)
    ax.text(3.75, 5.5, "Path A: Offline Cluster Simulator", fontsize=12, fontweight="bold", ha="center", color="#1d4ed8")
    ax.text(3.75, 4.5, "• No K8s cluster or Docker required\n• Feeds synthetic/Borg traces into evaluator\n• Compares CPA vs HPA replica counts\n• Produces scaling response plots (Fig 21)", 
            fontsize=9.5, ha="center", color="#1e293b")
    ax.text(3.75, 2.0, "Output: comparison_plot.png\n(Proactive vs Reactive scaling curves)", 
            fontsize=9.5, fontweight="bold", ha="center", color="#1e40af")

    # Path B: Live K8s
    p_k8s = patches.FancyBboxPatch((7.8, 1.2), 6.5, 4.8, boxstyle="round,pad=0.15", 
                                  facecolor="#fdf4ff", edgecolor="#c026d3", linewidth=2)
    ax.add_patch(p_k8s)
    ax.text(11.05, 5.5, "Path B: Live K8s Cluster (WSL2 + Kind)", fontsize=12, fontweight="bold", ha="center", color="#86198f")
    ax.text(11.05, 4.5, "• Kind cluster running in WSL2\n• Build & load image: k8s-metrics-cpu:latest\n• Install CPA Operator & apply manifests\n• Watch real-time scaling: kubectl get pods -w", 
            fontsize=9.5, ha="center", color="#1e293b")
    ax.text(11.05, 2.0, "Live Metrics: Prometheus & Metrics Server\n(No tail latency / Zero dropped requests)", 
            fontsize=9.5, fontweight="bold", ha="center", color="#701a75")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {output_path}")


if __name__ == "__main__":
    create_phase1_diagram()
    create_phase2_diagram()
    create_phase3_diagram()
    create_phase4_diagram()
