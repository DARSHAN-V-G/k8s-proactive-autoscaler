# Speaker Guide: Person 3
## Topic: The End-to-End Autoscaler Architecture & ONNX Optimization

---

### 🎯 Your Goal
You are the third speaker. Your job is to explain the engineering implementation and cloud architecture:
1. How we packaged the GRU model into a lightweight container (<120MB) using **ONNX Runtime CPU**.
2. The end-to-end software architecture of our Custom Pod Autoscaler (CPA) running inside the Kubernetes cluster.
3. The 2-phase autonomous control loop (`metric.py` and `evaluate.py`).
4. The enterprise production safety controls (Cold-start fallback, Hybrid Safety Maximizer, and 60s downscale stabilization).

---

### 🧠 Core Concepts in Simple English (Understand This First!)

1. **How did we deploy the AI model without making it slow or heavy?**
   * Standard deep learning images containing PyTorch or TensorFlow are massive (**~1.5 GB**), causing high network overhead and slow pod spin-up times.
   * To solve this, we compiled our trained GRU model into an **ONNX Runtime CPU binary**.
   * This slashed our final Docker container image size down to **under 120 MB** (a 92% reduction). It requires **zero GPUs**, uses minimal memory, and runs inference in **0.03 milliseconds** directly on standard CPU worker nodes.

2. **How does our Autoscaler actually run in Kubernetes?**
   * We didn't change the Kubernetes core source code. We built our autoscaler using the official **Kubernetes Custom Pod Autoscaler (CPA) Operator**.
   * It runs as an independent pod inside the cluster using an autonomous 2-phase control loop every **10 seconds**:
     * **Phase 1: Metric Gatherer (`metric.py`)** — Collects current pod CPU and replica count from the K8s Metrics Server and stores them in a rolling buffer.
     * **Phase 2: Evaluator Engine (`evaluate.py`)** — Reads the past 24 timesteps and feeds them into our ONNX GRU engine to predict future load and calculate target replicas.

3. **The Embedded Rolling Buffer (SQLite):**
   * Instead of a volatile in-memory list, we persist the sliding 24-step sequence in a lightweight local **SQLite database (`db.py`)** inside the CPA pod.
   * This ensures state persistence even if individual scripts cycle or experience transient container restarts.

4. **Enterprise Fail-Safes (Production Stability):**
   * **Cold-Start Fallback:** Before 24 timesteps are gathered (first 4 minutes), the system automatically uses standard reactive HPA math so pods are always protected from second zero.
   * **Hybrid Safety Maximizer:** What if traffic spikes in an unpredicted, sudden burst? We added a safety formula: $\text{TargetReplicas} = \max(\text{Proactive}, \text{Reactive})$. Proactive AI can **only help, never hurt**. If reactive math requires more pods, it takes the higher number.
   * **60-Second Stabilization Window:** Prevents destructive pod flapping (thrashing) during momentary traffic dips.

---

### 🔬 Technical Details & Architecture Flow

#### 1. Container Size Optimization (ONNX Runtime CPU):
* Heavy PyTorch / TensorFlow container = **~1.5 GB** (slow deployment, GPU dependencies).
* Compiled to **ONNX Runtime CPU**: shrunk to **~120 MB** (92% reduction, 100% CPU-only, zero GPU needed).
* Inference latency: **0.03 ms**, well within the 10-second controller interval.

---

#### 2. Visual CPA Architecture & Control Flow Diagram:

```mermaid
graph TD
    classDef k8s fill:#326ce5,stroke:#fff,stroke-width:2px,color:#fff;
    classDef cpa fill:#f59e0b,stroke:#333,stroke-width:2px,color:#000;
    classDef ai fill:#10b981,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#8b5cf6,stroke:#fff,stroke-width:2px,color:#fff;

    subgraph K8S_CLUSTER["Kubernetes Cluster Environment"]
        direction TB
        PODS["Target Pods (php-cpa Deployments)"]:::k8s
        METRICS_SRV["Kubernetes Metrics Server API"]:::k8s

        subgraph CPA_POD["Custom Pod Autoscaler (CPA Pod)"]
            direction TB
            subgraph PHASE1["Phase 1: Metric Gatherer (metric.py)"]
                GATHER["Kubelet / Metrics API Scraper<br/>Extracts: Current Replicas (Cur_r) & CPU (Avg_u)"]:::cpa
            end

            SQLITE[("SQLite Rolling Buffer (db.py)<br/>Stores 24 Historical Timesteps")]:::db

            subgraph PHASE2["Phase 2: Evaluator Engine (evaluate.py)"]
                CHECK{"Sequence Length < 24?"}
                REACTIVE_FB["Cold-Start Fallback<br/>Tar_r = ceil(Cur_r * Avg_u / Tar_u)"]:::cpa
                
                GRU_INF["Pre-Trained GRU Model<br/>(ONNX Runtime CPU Engine - 0.03ms)"]:::ai
                PRED["Forecast Upcoming CPU Load (Pre_u)"]:::ai
                PROACTIVE_CALC["Calculate Proactive Replicas<br/>Tar_r_pro = ceil(Cur_r * Pre_u / Tar_u)"]:::ai
                
                HYBRID["Hybrid Safety Maximizer<br/>Tar_r = max(Proactive, Reactive, MinReplicas)"]:::cpa
                STABILIZE["60-Second Downscale Stabilization<br/>(Prevents Destructive Pod Thrashing)"]:::cpa
            end
        end

        K8S_API["Kubernetes API Server<br/>(Scale Subresource)"]:::k8s
    end

    PODS -->|CPU & Memory Usage| METRICS_SRV
    METRICS_SRV -->|Every 10 Seconds| GATHER
    GATHER -->|Store (Cur_r, Avg_u)| SQLITE
    SQLITE -->|Feed Past 24 Steps| CHECK
    
    CHECK -->|Yes: Cold Start Phase| REACTIVE_FB
    CHECK -->|No: Ready for AI Inference| GRU_INF
    
    GRU_INF --> PRED
    PRED --> PROACTIVE_CALC
    PROACTIVE_CALC --> HYBRID
    REACTIVE_FB --> HYBRID
    
    HYBRID --> STABILIZE
    STABILIZE -->|Issue Scale Command| K8S_API
    K8S_API -->|Update Desired Replicas| PODS
```

---

#### 3. The 2-Phase Control Loop Summary:
```text
[Kubernetes Pods & Metrics Server]
                │ (every 10s)
                ▼
1. Metric Gatherer (metric.py) ──> Appends (Cur_r, Avg_u) to SQLite Rolling DB (db.py)
                │
                ▼
2. Evaluator Engine (evaluate.py)
   ├── If steps < 24: Cold-Start Fallback -> Tar_r = ceil(Cur_r * (Avg_u / Target_u))
   └── If steps >= 24: 
          │──> Feeds past 24 steps to GRU model
          │──> Forecasts Pre_u (Future CPU load)
          │──> Tar_r_proactive = ceil(Cur_r * (Pre_u / Target_u))
          │──> Hybrid Maximizer: Tar_r = max(Tar_r_proactive, Tar_r_reactive, MinReplicas)
          └──> 60-second Downscale Stabilization (Prevents pod thrashing)
                │
                ▼
[Kubernetes Deployment Scaled to Target Replicas]
```

---

### 🖥️ Slide Content (Copy this onto your slide)

**Slide Title: End-to-End Autoscaler Architecture & Production Safeguards**

* **Edge AI Containerization (ONNX Runtime CPU):**
  * Shrunk deep learning container from 1.5 GB (PyTorch) to **<120 MB** using ONNX.
  * **100% CPU-only execution:** Microsecond inference (0.03 ms) with zero expensive GPU hardware.
* **Two-Phase Control Loop (Executed Every 10 Seconds):**
  * **Phase 1: Metric Gatherer (`metric.py`)** — Collects CPU usage and replica count, updating a local SQLite rolling window (`db.py`).
  * **Phase 2: Evaluator Engine (`evaluate.py`)** — Reads past 24 timesteps to forecast upcoming load ($Pre_u$) and scale deployment.
* **Enterprise Production Safety Controls:**
  * **Cold-Start Fallback:** Reverts to standard reactive HPA during the initial 24 timesteps.
  * **Hybrid Safety Maximizer:** $\text{Target} = \max(\text{Proactive}, \text{Reactive})$ — guarantees no under-scaling during unpredicted flash spikes.
  * **Downscale Stabilization Window:** 60-second cooldown prevents destructive container thrashing and pod flapping.

---

### 🗣️ Spoken Speech Script (Word-for-Word)

> *"Thank you, [Person 2]. Now that Person 2 has established why the 24-step GRU model was chosen as our production model, I will explain how we packaged it and engineered the end-to-end Kubernetes Custom Pod Autoscaler architecture.*
>
> *Our first major engineering challenge was deployment footprint. A typical machine learning container with PyTorch or TensorFlow exceeds **1.5 gigabytes** in size, requiring extensive network bandwidth and high startup overhead. To eliminate this, we compiled our trained GRU model into an **ONNX Runtime CPU binary**.*
> *This shrunk our final production container image down to **under 120 megabytes**—a 92% reduction. It runs 100% CPU-only on commodity worker nodes with zero GPU requirements, executing predictions in a lightning-fast **0.03 milliseconds**.*
>
> *Now, let’s look at how our autoscaler operates within the Kubernetes cluster.*
>
> *We implemented the solution using the official **Kubernetes Custom Pod Autoscaler Operator**, running an autonomous 2-phase control loop every 10 seconds:*
>
> *In **Phase 1, the Metric Gatherer (`metric.py`)** queries the Kubernetes Metrics API for the current replica count and mean CPU utilization, saving the data points into a rolling SQLite buffer.*
>
> *In **Phase 2, the Evaluator Engine (`evaluate.py`)** reads the historical sequence. If fewer than 24 steps exist during cold start, it safely falls back to standard reactive calculations. Once 24 timesteps are gathered, it feeds the sequence to the GRU engine to forecast the next CPU load, and calculates the proactive replica target.*
>
> *Crucially, we engineered two enterprise safeguards: First, the **Hybrid Safety Maximizer**, which takes the maximum of proactive and reactive formulas. This guarantees that even during an unlearned catastrophic spike, the system will never scale below reactive requirements. Second, a **60-second downscale stabilization window** prevents rapid pod churning and thrashing.*
>
> *Now, **[Person 4's Name]** will present the live empirical benchmark results, comparing our proactive autoscaler against standard Kubernetes HPA."*

---

### ❓ Expected Q&A Questions & How to Answer

* **Q: How does the controller handle the cold-start phase before 24 metrics are collected?**
  * *Answer:* "During the initial 24 timesteps (first 4 minutes), the evaluator automatically triggers our fallback branch, executing standard reactive HPA math until the rolling buffer is fully populated, guaranteeing 100% uptime from second zero."
* **Q: Why did you use SQLite instead of an in-memory Python list?**
  * *Answer:* "SQLite is embedded, ACID-compliant, and runs in-process with microsecond read/write times. If the evaluator pod is temporarily restarted, the historical time-series persists in the container's volume rather than being wiped out."
* **Q: Why did you choose ONNX Runtime instead of native PyTorch?**
  * *Answer:* "Native PyTorch installs hundreds of megabytes of unnecessary CUDA and training dependencies. ONNX Runtime CPU is a lean, highly optimized C++ inference engine that dropped our container size below 120 MB and gave us deterministic 0.03 ms latency on commodity cloud CPUs without requiring GPUs."
