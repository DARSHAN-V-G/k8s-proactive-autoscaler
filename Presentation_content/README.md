# Master Presentation Guide: Intelligent Proactive Kubernetes Autoscaler

Welcome to the presentation briefing packet! This folder contains dedicated, comprehensive preparation guides for all 4 presenters.

---

## ⏱️ Presentation Timing & Flow Overview (Total: 12–15 Minutes)

| Presenter | Role / Section | Time Allocated | Key Focus |
| :--- | :--- | :--- | :--- |
| **Person 1** | **The Problem & The Solution** | 3 – 4 mins | Why standard HPA fails (50s lag) & the proactive AI vision |
| **Person 2** | **Dataset & ML Model Evaluation** | 3 – 4 mins | Google Borg 31-day trace & Table 3 benchmark (ARIMA vs LSTM vs GRU) |
| **Person 3** | **Why GRU & Autoscaler Architecture** | 3 – 4 mins | Why GRU won (0.03ms speed) & CPA 2-phase controller inner workings |
| **Person 4** | **CPA vs. HPA Performance Comparison** | 3 – 4 mins | Live Prometheus graphs (Replicas pre-scaling & 40ms vs 420ms latency) |

---

## 📂 Navigation to Individual Preparation Docs

1. 📄 **[Person 1 Guide: The Problem & The Solution](./Person_1_Problem_and_Solution.md)**
   * Native Kubernetes HPA math & reactive delay breakdown (50–60s).
   * Flash crowd impact (10x latency degradation, SLA breaches).
   * The proactive paradigm shift.

2. 📄 **[Person 2 Guide: Dataset & ML Model Evaluation](./Person_2_Dataset_and_ML_Models.md)**
   * Real-world Google Borg Cluster Trace (405k task events, 31 days).
   * Pearson auto-correlation analysis ($r = 0.6664$).
   * Table 3 empirical benchmark: ARIMA vs. LSTM vs. BiLSTM vs. GRU.

3. 📄 **[Person 3 Guide: Why GRU & Autoscaler Architecture](./Person_3_Why_GRU_and_Architecture.md)**
   * Mathematical & engineering reasons for choosing GRU over LSTM and ARIMA.
   * CPA Operator framework, CRD, and 2-phase control loop (`metric.py`, `evaluate.py`).
   * Hybrid Safety Maximizer and ONNX CPU lightweight container (<120MB).

4. 📄 **[Person 4 Guide: CPA vs. HPA Performance Comparison](./Person_4_Performance_Comparison.md)**
   * Experimental testbed (Kind local & GKE cloud) with autonomous cyclic traffic surges.
   * Real-time scaling lead time (CPA scales 30–45s earlier).
   * Real-time QoS response time graph (CPA steady at 40ms vs. HPA spiking to 420ms).
   * Project conclusion & business impact.

---

## 🤝 Rules for Smooth Handoffs Between Speakers
At the end of each document, you will find an **exact transition script**. Use it to smoothly hand over the speaking turn to your teammate without awkward pauses.
