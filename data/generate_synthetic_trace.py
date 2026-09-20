"""
Synthetic Cloud Workload Generator
Simulates realistic cloud CPU load traces matching Google Borg / Alibaba cluster statistics:
- Diurnal / cyclic daily variation
- Gaussian background noise
- Poisson-distributed traffic surges (flash crowds / burst spikes)
"""

import os
import argparse
import numpy as np
import pandas as pd


def generate_workload_trace(
    n_points: int = 8352,
    interval_sec: int = 300,
    seed: int = 42,
    base_load: float = 0.25,
    diurnal_amp: float = 0.15,
    noise_std: float = 0.03,
    n_spikes: int = 15,
    spike_amp_range: tuple = (0.2, 0.45),
    spike_duration_range: tuple = (3, 12),
) -> pd.DataFrame:
    """
    Generates a time-series CPU load trace.
    Default parameters mimic the Borg clusterdata-2011-2 (8352 steps @ 300s = 29 days).
    """
    np.random.seed(seed)
    time_points = np.arange(n_points)
    timestamps = time_points * interval_sec

    # 1. Base Diurnal Cycles (24-hour periodicity)
    # Number of points in a 24-hour cycle: (24 * 3600) / interval_sec
    cycle_points = (24 * 3600) / interval_sec
    diurnal = diurnal_amp * np.sin(2 * np.pi * time_points / cycle_points - np.pi / 2)

    # 2. Add subtle weekly cycle (7 days)
    week_points = cycle_points * 7
    weekly = (diurnal_amp * 0.3) * np.sin(2 * np.pi * time_points / week_points)

    # 3. Gaussian Background Noise
    noise = np.random.normal(0, noise_std, size=n_points)

    # Combine baseline
    cpu_usage = base_load + diurnal + weekly + noise

    # 4. Inject Burst Spikes (Flash Crowds / Sudden Load Surges)
    if n_points > 100 and n_spikes > 0:
        actual_n_spikes = min(n_spikes, max(1, n_points // 20))
        margin = max(10, n_points // 10)
        valid_range = range(margin, n_points - margin)
        if len(valid_range) > actual_n_spikes:
            spike_indices = np.random.choice(valid_range, size=actual_n_spikes, replace=False)
            for idx in spike_indices:
                dur = np.random.randint(spike_duration_range[0], spike_duration_range[1])
                amp = np.random.uniform(spike_amp_range[0], spike_amp_range[1])
                # Smooth bell-shaped spike
                spike_shape = amp * np.exp(-0.5 * ((np.arange(dur) - dur / 2) / (dur / 4)) ** 2)
                end_idx = min(idx + dur, n_points)
                actual_len = end_idx - idx
                cpu_usage[idx:end_idx] += spike_shape[:actual_len]

    # Clip CPU usage between realistic bounds [0.02, 0.98]
    cpu_usage = np.clip(cpu_usage, 0.02, 0.98)

    # Calculate simulated memory usage (weak correlation ~0.208 as noted in research paper)
    mem_noise = np.random.normal(0, 0.05, size=n_points)
    mem_usage = np.clip(0.35 + 0.208 * (cpu_usage - np.mean(cpu_usage)) + mem_noise, 0.05, 0.95)

    df = pd.DataFrame({
        "step": time_points,
        "timestamp_sec": timestamps,
        "cpu_rate": np.round(cpu_usage, 5),
        "memory_rate": np.round(mem_usage, 5)
    })
    return df


def generate_multiple_machine_traces(
    n_machines: int = 100,
    n_points: int = 8352,
    interval_sec: int = 300,
    output_path: str = "data/sample_cluster_data.csv"
) -> pd.DataFrame:
    """
    Generates workload traces across multiple virtual machines as done in the paper.
    """
    all_traces = []
    for m_id in range(n_machines):
        m_seed = 42 + m_id * 17
        base_load = np.random.uniform(0.15, 0.35)
        df_m = generate_workload_trace(
            n_points=n_points,
            interval_sec=interval_sec,
            seed=m_seed,
            base_load=base_load,
            n_spikes=np.random.randint(10, 25)
        )
        df_m["machine_id"] = f"machine_{m_id:03d}"
        all_traces.append(df_m)

    combined = pd.concat(all_traces, ignore_index=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.to_csv(output_path, index=False)
    print(f"Successfully generated {n_machines} machine traces ({len(combined)} records) -> {output_path}")
    return combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic cloud CPU workload traces")
    parser.add_argument("--machines", type=int, default=10, help="Number of machines to simulate (default: 10)")
    parser.add_argument("--points", type=int, default=8352, help="Number of time steps per machine (default: 8352)")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds (default: 300)")
    parser.add_argument("--output", type=str, default="data/sample_cluster_data.csv", help="Output CSV path")
    args = parser.parse_args()

    generate_multiple_machine_traces(
        n_machines=args.machines,
        n_points=args.points,
        interval_sec=args.interval,
        output_path=args.output
    )
