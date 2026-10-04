# Speaker Guide: Person 3
## Topic: Why GRU Won & The End-to-End Autoscaler Architecture

---

### 🎯 Your Goal
You are the third speaker. Your job is to explain the engineering decisions: why GRU won over all other models, how we packaged it into a lightweight container (<120MB), and the end-to-end software architecture of our Custom Pod Autoscaler (CPA) running inside the Kubernetes cluster.

---

### 🧠 Core Concepts in Simple English (Understand This First!)

1. **Why did GRU win? (The "Smart & Lean" Model):**
   * Standard LSTM has 3 gates (input, forget, output) and a separate cell memory. It's bulky.
   * **GRU simplifies this into just 2 gates: the Reset Gate and the Update Gate.**
   * It drops the parameter count by **25%**, which means it uses way less RAM and CPU, yet delivers the exact same accuracy.
   * It executes in **0.03 milliseconds**—over **8,700 times faster than ARIMA**!
2. **How does our Autoscaler actually run in Kubernetes?**
   * We didn't change the Kubernetes core source code. We built our autoscaler using the official **Kubernetes Custom Pod Autoscaler (CPA) Operator**.
   * It runs as an independent pod inside the cluster using a 2-phase control loop every 10 seconds:
     * **Phase 1: Metric Gatherer (`metric.py`)** — Collects current CPU and pods from kubelet and stores them in a rolling buffer.
     * **Phase 2: Evaluator Engine (`evaluate.py`)** — Feeds the past 24 timesteps into our pre-trained GRU model to calculate the future pod count.
3. **The "Hybrid Safety Maximizer" (Our Fail-Safe):**
   * What if traffic spikes unexpectedly before the AI saw it coming?
   * We added a safety formula: $\text{TargetReplicas} = \max(\text{Proactive}, \text{Reactive})$.
   * It guarantees that proactive AI **can only help, never hurt**. If reactive math asks for more pods, it takes the higher number.

---

### 🔬 Technical Details & Formulas to Cite

#### 1. GRU Mathematical Formulation:
* **Update Gate ($z_t$):** Determines how much past memory to retain.
  $$z_t = \sigma(W_z \cdot [h_{t-1}, x_t])$$
* **Reset Gate ($r_t$):** Determines how much past memory to forget.
  $$r_t = \sigma(W_r \cdot [h_{t-1}, x_t])$$
* **Candidate Hidden State ($\tilde{h}_t$) & Output State ($h_t$):**
  $$\tilde{h}_t = \tanh(W \cdot [r_t * h_{t-1}, x_t])$$
  $$h_t = (1 - z_t) * h_{t-1} + z_t * \tilde{h}_t$$
* **Key takeaway:** 25% fewer parameters than LSTM, zero GPU required, sub-millisecond execution.

#### 2. Container Size Optimization (ONNX Runtime):
* Heavy PyTorch / TensorFlow container = **~1.5 GB** (too heavy, high startup latency).
* Compiled to **ONNX Runtime CPU**: shrunk to **~120 MB** (92% reduction, 100% CPU-only, zero GPU needed).

#### 3. Visual CPA Architecture & Control Flow Diagram:

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

#### 4. The 2-Phase Control Loop Summary:
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

**Slide Title: Why GRU Won & The End-to-End Autoscaler Architecture**

* **Architectural Rationale for Selecting GRU:**
  * **25% fewer parameters** than LSTM by fusing reset and update gates.
  * **0.03 ms latency (8,700x faster than ARIMA)**, ensuring zero controller lag.
  * Exported to **ONNX Runtime CPU**: container shrunk from 1.5 GB to **<120 MB** (zero GPU required).
* **Two-Phase Control Loop (Every 10 Seconds):**
  * **Phase 1: Metric Gatherer (`metric.py`)** — Collects CPU usage and pod count, updating a local SQLite rolling window.
  * **Phase 2: Evaluator Engine (`evaluate.py`)** — Passes past 24 timesteps to the GRU model to forecast load ($Pre_u$).
* **Enterprise Production Safety Controls:**
  * **Hybrid Safety Maximizer:** $\text{Target} = \max(\text{Proactive}, \text{Reactive})$ — guarantees no under-scaling during unpredicted flash spikes.
  * **Downscale Stabilization Window:** 60-second cooldown prevents destructive container thrashing.

---

### 🗣️ Spoken Speech Script (Word-for-Word)

> *"Thank you, [Person 2]. Based on the empirical findings, we chose **Gated Recurrent Units (GRU)** as our production model architecture.
>
> *Here is the engineering rationale: Standard LSTM architectures utilize three gates and separate cell memory, requiring extensive matrix multiplications. In contrast, GRU elegantly merges the forget and input gates into a single Update Gate, and replaces cell state with a Reset Gate. This reduces the total parameter count by **25%** with zero loss in prediction accuracy.
>
> *Furthermore, to eliminate the massive 1.5 GB overhead of frameworks like PyTorch or TensorFlow, we compiled our trained GRU model into an **ONNX Runtime CPU binary**. This shrunk our final production container image down to **under 120 megabytes**—making it 100% CPU-only, ultra-fast to spin up, and capable of executing inference in just **0.03 milliseconds**.
>
> *Now, let’s look at how our autoscaler operates within the Kubernetes cluster.
>
> *We implemented the solution using the official **Kubernetes Custom Pod Autoscaler Operator**, running an autonomous 2-phase control loop every 10 seconds:
>
> *In **Phase 1, the Metric Gatherer (`metric.py`)** queries the Kubernetes Metrics API for the current replica count and mean CPU utilization, saving the data points into a rolling SQLite buffer.
>
> *In **Phase 2, the Evaluator Engine (`evaluate.py`)** reads the historical sequence. If fewer than 24 steps exist during cold start, it safely falls back to standard reactive calculations. Once 24 timesteps are gathered, it feeds the sequence to the GRU engine to forecast the next CPU load, and calculates the proactive replica target.
>
> *Crucially, we engineered two enterprise safeguards: First, the **Hybrid Safety Maximizer**, which takes the maximum of proactive and reactive formulas. This guarantees that even during an unlearned catastrophic spike, the system will never scale below reactive requirements. Second, a **60-second downscale stabilization window** prevents rapid pod churning and thrashing.
>
> *Now, **[Person 4's Name]** will present the live empirical benchmark results, comparing our proactive autoscaler against standard Kubernetes HPA."*

---

### ❓ Expected Q&A Questions & How to Answer

* **Q: How does the controller handle the cold-start phase before 24 metrics are collected?**
  * *Answer:* "During the initial 24 timesteps (first 4 minutes), the evaluator automatically triggers our fallback branch, executing standard reactive HPA math until the rolling buffer is fully populated, guaranteeing 100% uptime from second zero."
* **Q: Why did you use SQLite instead of an in-memory Python list?**
  * *Answer:* "SQLite is embedded, ACID-compliant, and runs in-process with microsecond read/write times. If the evaluator pod is temporarily restarted, the historical time-series persists in the container's volume rather than being wiped out."
