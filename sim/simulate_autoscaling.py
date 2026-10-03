"""
End-to-End Autoscaling Simulation Engine (Phase 4)
Reproduces Figure 21 & Table 1 from MDPI Mathematics 2023 paper:
Compares Proactive GRU CPA vs. Reactive Kubernetes HPA over time:
- Models real-world pod provisioning startup lag (30s)
- Models downscale stabilization cooldown window (60s)
- Calculates SLA/QoS violations and resource over-provisioning
- Generates high-resolution comparative visualization (docs/plots/scaling_comparison.png)
"""

import os
import sys
import math
import json
import tempfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add k8s-metrics-cpu and project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, os.path.join(root_dir, "k8s-metrics-cpu"))
sys.path.insert(0, root_dir)

from data.generate_synthetic_trace import generate_workload_trace
from db import MetricsDatabase
from evaluate import evaluate_scaling


class AutoscalingSimulator:
    def __init__(
        self,
        target_cpu_threshold: float = 50.0,
        pod_startup_delay_steps: int = 3,      # 30s delay (3 steps @ 10s)
        downscale_stabilization_steps: int = 6, # 60s cooldown window (6 steps @ 10s)
        min_replicas: int = 1,
        max_replicas: int = 20
    ):
        self.target_cpu = target_cpu_threshold
        self.startup_delay = pod_startup_delay_steps
        self.stabilization_window = downscale_stabilization_steps
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    def simulate_workload(
        self,
        workload_series: np.ndarray,
        step_interval_sec: int = 10,
        output_plot_path: str = "docs/plots/scaling_comparison.png"
    ) -> dict:
        """
        Executes parallel simulation of Proactive CPA vs Reactive HPA over the workload stream.
        """
        n_steps = len(workload_series)
        
        # Temporary DB for CPA simulation
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "sim_metrics.db")
            db = MetricsDatabase(db_path=db_path)

            # State tracking: Proactive CPA
            cpa_desired_replicas = []
            cpa_ready_replicas = [1] * n_steps
            cpa_pending_queue = [] # (scheduled_step, new_replicas)
            cpa_predicted_cpu = []
            cpa_recent_desires = [] # for stabilization window

            # State tracking: Reactive HPA
            hpa_desired_replicas = []
            hpa_ready_replicas = [1] * n_steps
            hpa_pending_queue = []
            hpa_recent_desires = [] # for stabilization window

            # Metrics
            cpa_sla_violations = 0
            hpa_sla_violations = 0

            cur_cpa_pods = 1
            cur_hpa_pods = 1

            for t in range(n_steps):
                current_cpu = float(workload_series[t])

                # 1. Update Ready Pods from Pending Startup Queues
                ready_cpa = cur_cpa_pods
                for sched_t, target_p in list(cpa_pending_queue):
                    if t >= sched_t + self.startup_delay:
                        ready_cpa = target_p
                        cpa_pending_queue.remove((sched_t, target_p))
                cpa_ready_replicas[t] = ready_cpa
                cur_cpa_pods = ready_cpa

                ready_hpa = cur_hpa_pods
                for sched_t, target_p in list(hpa_pending_queue):
                    if t >= sched_t + self.startup_delay:
                        ready_hpa = target_p
                        hpa_pending_queue.remove((sched_t, target_p))
                hpa_ready_replicas[t] = ready_hpa
                cur_hpa_pods = ready_hpa

                # -----------------------------------------------------------------
                # PROACTIVE CPA EVALUATION
                # -----------------------------------------------------------------
                db.insert_metric(avg_u=current_cpu, cur_r=cur_cpa_pods)
                cpa_input = json.dumps({"cur_r": cur_cpa_pods, "avg_u": current_cpu})
                eval_res = evaluate_scaling(
                    cpa_input, 
                    target_cpu_threshold=self.target_cpu,
                    window_size=24,
                    db_path=db_path
                )
                
                raw_cpa_tar = eval_res["targetReplicas"]
                pred_cpu = eval_res.get("pre_u") or current_cpu
                cpa_predicted_cpu.append(pred_cpu)

                # CPA Stabilization (matching Kubernetes downscaleStabilization)
                raw_cpa_tar = min(self.max_replicas, max(self.min_replicas, raw_cpa_tar))
                cpa_recent_desires.append(raw_cpa_tar)
                if len(cpa_recent_desires) > self.stabilization_window:
                    cpa_recent_desires.pop(0)

                if raw_cpa_tar > cur_cpa_pods:
                    des_cpa = raw_cpa_tar
                    cpa_pending_queue.append((t, des_cpa))
                elif raw_cpa_tar < cur_cpa_pods:
                    des_cpa = max(cpa_recent_desires)
                    if des_cpa < cur_cpa_pods:
                        cpa_pending_queue.append((t, des_cpa))
                else:
                    des_cpa = cur_cpa_pods

                cpa_desired_replicas.append(des_cpa)

                # -----------------------------------------------------------------
                # REACTIVE HPA EVALUATION (Standard Kubernetes algorithm)
                # -----------------------------------------------------------------
                raw_hpa_tar = math.ceil(cur_hpa_pods * (current_cpu / self.target_cpu))
                raw_hpa_tar = min(self.max_replicas, max(self.min_replicas, raw_hpa_tar))
                hpa_recent_desires.append(raw_hpa_tar)
                if len(hpa_recent_desires) > self.stabilization_window:
                    hpa_recent_desires.pop(0)

                if raw_hpa_tar > cur_hpa_pods:
                    des_hpa = raw_hpa_tar
                    hpa_pending_queue.append((t, des_hpa))
                elif raw_hpa_tar < cur_hpa_pods:
                    des_hpa = max(hpa_recent_desires)
                    if des_hpa < cur_hpa_pods:
                        hpa_pending_queue.append((t, des_hpa))
                else:
                    des_hpa = cur_hpa_pods

                hpa_desired_replicas.append(des_hpa)

                # -----------------------------------------------------------------
                # SLA / QoS Overload Check
                # -----------------------------------------------------------------
                effective_cpa_load = current_cpu / max(1, cpa_ready_replicas[t])
                effective_hpa_load = current_cpu / max(1, hpa_ready_replicas[t])

                if effective_cpa_load > 85.0:
                    cpa_sla_violations += 1
                if effective_hpa_load > 85.0:
                    hpa_sla_violations += 1

        # -----------------------------------------------------------------
        # Generate Visualization (Matches Figure 21 in Paper)
        # -----------------------------------------------------------------
        os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)
        time_axis = np.arange(n_steps) * (step_interval_sec / 60.0) # in minutes

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, dpi=300)
        fig.patch.set_facecolor("#ffffff")

        # Top Graph: Workload & Predicted Load
        ax1.plot(time_axis, workload_series, label="Actual Workload CPU (%)", color="#0f172a", lw=2, alpha=0.85)
        ax1.plot(time_axis, cpa_predicted_cpu, label="GRU Predicted Workload (Pre_u)", color="#3b82f6", lw=1.8, linestyle="--")
        ax1.axhline(self.target_cpu, color="#ef4444", linestyle=":", lw=1.5, label=f"Target CPU Threshold ({int(self.target_cpu)}%)")
        ax1.set_ylabel("CPU Utilization (%)", fontsize=11, fontweight="bold")
        ax1.set_title("Kubernetes Autoscaling Comparison: Proactive CPA (GRU) vs. Reactive HPA", fontsize=14, fontweight="bold", pad=12)
        ax1.legend(loc="upper right", framealpha=0.9)
        ax1.grid(True, alpha=0.3)

        # Bottom Graph: Scaling Replicas (Figure 21)
        ax2.plot(time_axis, cpa_ready_replicas, label="Proactive CPA Replicas (Our Scheme)", color="#2563eb", lw=2.5)
        ax2.plot(time_axis, hpa_ready_replicas, label="Native Reactive HPA Replicas", color="#dc2626", lw=2, linestyle="-.")
        ax2.set_ylabel("Pod Replicas Count", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Time (Minutes)", fontsize=11, fontweight="bold")
        ax2.legend(loc="upper right", framealpha=0.9)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Comparison plot successfully generated -> {output_plot_path}")

        # Metrics Report
        report = {
            "Total Steps": n_steps,
            "Duration (min)": round(n_steps * step_interval_sec / 60.0, 1),
            "CPA SLA Violations (steps)": cpa_sla_violations,
            "HPA SLA Violations (steps)": hpa_sla_violations,
            "SLA Violation Reduction": f"{max(0, (hpa_sla_violations - cpa_sla_violations) / max(1, hpa_sla_violations) * 100):.1f}%",
            "CPA Avg Replicas": round(float(np.mean(cpa_ready_replicas)), 2),
            "HPA Avg Replicas": round(float(np.mean(hpa_ready_replicas)), 2),
            "Plot Path": output_plot_path
        }
        return report


def run_simulation(
    n_points: int = 200,
    step_sec: int = 10,
    output_path: str = "docs/plots/scaling_comparison.png"
):
    print("Generating simulated cluster workload trace with sudden burst spikes...")
    trace_df = generate_workload_trace(
        n_points=n_points,
        interval_sec=step_sec,
        base_load=0.30,
        diurnal_amp=0.20,
        noise_std=0.02,
        n_spikes=3,
        spike_amp_range=(0.4, 0.6)
    )
    cpu_stream = trace_df["cpu_rate"].values * 100.0

    print(f"Running autoscaling simulation across {n_points} time steps...")
    sim = AutoscalingSimulator(target_cpu_threshold=50.0)
    metrics = sim.simulate_workload(
        cpu_stream,
        step_interval_sec=step_sec,
        output_plot_path=output_path
    )

    print("\n" + "=" * 60)
    print("AUTOSCALING SIMULATION BENCHMARK REPORT")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k:30s} : {v}")
    print("=" * 60)
    return metrics


if __name__ == "__main__":
    run_simulation()
