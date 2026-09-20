# 📚 Complete System Overview & Conceptual Flow

This document provides a beginner-friendly, step-by-step explanation of the entire project, why it was built, how the AI works, and how the Kubernetes components interact.

---

## 1. The Core Problem in Cloud & Kubernetes Autoscaling

### What is Autoscaling in Kubernetes?
Imagine you are running a web application (like an e-commerce store or video streaming site) inside Kubernetes:
- Your application runs inside container instances called **Pods**.
- When **10 users** visit your website, **1 Pod** is enough.
- When **10,000 users** suddenly rush in (like during a flash sale or Black Friday), that single Pod will crash from CPU overload. You need **10 Pods** running in parallel to share the load.
- Automatically adding or removing Pods based on user demand is called **Horizontal Pod Autoscaling (HPA)**.

---

### What is wrong with Kubernetes default HPA? (The "Reactive Lag" Problem)
Default Kubernetes HPA is **purely reactive**:
1. Traffic suddenly surges at **Minute 1:00**.
2. CPU usage shoots to 95% on your pods.
3. Kubernetes Metrics Server takes **~15–30 seconds** to notice the CPU increase.
4. Kubernetes decides to add new pods, but starting new containers and warming them up takes another **~30 seconds**.
5. **Total Delay = 50 to 60 seconds!**

During that 1 full minute of delay, your website becomes slow, requests time out, and users experience errors.

```
Traffic Spike Starts ---> [ 50-60 Seconds of Slowdowns & Crashes ] ---> New Pods Finally Ready
```

---

## 2. The Research Paper Solution: Proactive AI Scaling

The research paper asks:  
> *"Why wait for the server to get overloaded before creating pods? Why not use an AI model to **predict** the traffic spike in advance and create the pods **before** the users even arrive?"*

```
AI Predicts Traffic Spike ---> Pods Scaled In Advance! ---> Traffic Spike Hits ---> Zero Lag & Zero Crashes!
```

---

## 3. Step 1: Choosing the Best AI Model (Phase 1)

The authors tested 4 different forecasting algorithms on real-world cloud traffic datasets (from Google's Borg clusters):
1. **ARIMA**: Traditional statistics formula. (Very slow during online prediction: ~180 ms).
2. **LSTM**: Standard deep learning for sequences.
3. **BiLSTM**: Bidirectional LSTM (processes sequences forward & backward, but in live cloud autoscaling you cannot look into the future, so backward processing is unrealistic and takes 2x the compute).
4. **GRU (Gated Recurrent Unit)**: A simpler, faster neural network designed for sequence prediction.

### The Winner: GRU with a 24-Step Window (`GRU_Model_24`)
- **Input**: The last 24 CPU readings (e.g., CPU utilization over the last few minutes).
- **Output**: The predicted CPU utilization for the next minute ($Pre\_u$).
- **Inference Speed**: Under **1 millisecond** (300x faster than ARIMA!).
- **Model Size**: Only ~32 KB — super lightweight.

---

## 4. Step 2: How Kubernetes Runs Our AI Model (Phase 2 & CPA)

Kubernetes native HPA has hardcoded rules and does not allow you to run a Python neural network inside its core engine.

So the authors used an open-source framework called **Custom Pod Autoscaler (CPA)** (`jthomperoo/custom-pod-autoscaler`).

CPA is a wrapper that executes our custom scaling logic using two simple Python scripts:

```
+-----------------------------------------------------------------------+
|                 Custom Pod Autoscaler (k8s-metrics-cpu)               |
|                                                                       |
|  [ K8s Metrics Server ]                                               |
|           |                                                           |
|           v                                                           |
|    1. metric.py  -------> Saves CPU readings into SQLite DB (db.py)   |
|           |                                                           |
|           v                                                           |
|    2. evaluate.py <------ Reads last 24 CPU readings from SQLite DB   |
|           |                                                           |
|           +-------------> Feeds into GRU_Model_24.pt                  |
|           |               (Predicts upcoming CPU: Pre_u)              |
|           v                                                           |
|    Output: {"targetReplicas": 4}  =====> Tells K8s to scale pods      |
+-----------------------------------------------------------------------+
```

1. **`metric.py` (Metric Gatherer)**:
   - Reads current CPU from Kubernetes and stores it in a local SQLite file (`metrics.db`).
2. **`evaluate.py` (The Evaluator)**:
   - Queries `metrics.db` for the last 24 readings.
   - If it has 24 readings $\rightarrow$ feeds them into `GRU_Model_24.pt` to predict future CPU ($Pre\_u$) and calculates desired pods:
     $$\text{Target Pods} = \left\lceil \text{Current Pods} \times \frac{\text{Predicted CPU}}{50\%} \right\rceil$$
   - If the system just started and doesn't have 24 points yet $\rightarrow$ it safely falls back to standard reactive HPA so nothing breaks.

---

## 5. Step 3: What are `php-cpa` and `php-hpa`? (Phase 3)

Now we need a way to **prove and test** that our GRU autoscaler is actually better than default Kubernetes HPA.

To do a fair **A/B test**, we run two identical setups side-by-side in the same cluster:

```
                          [ Traffic Generator ]
                        (Sends spikes of traffic)
                                 /     \
                                /       \
                               v         v
             +--------------------+   +--------------------+
             |      php-cpa       |   |      php-hpa       |
             | (Target Web App 1) |   | (Target Web App 2) |
             +--------------------+   +--------------------+
                       ^                         ^
                       |                         |
               [ Our GRU Proactive ]     [ Default K8s Reactive ]
                 [ Autoscaler ]              [ Autoscaler ]
```

### 1. `php-cpa`:
- A web server application (in the paper, it runs PHP Apache math loops to simulate CPU work).
- **Controlled by**: Our proactive **Custom Pod Autoscaler (CPA)** using the GRU model.

### 2. `php-hpa`:
- The exact same web server application with identical CPU limits.
- **Controlled by**: Kubernetes default **Horizontal Pod Autoscaler (HPA)**.

### 3. `load-generator`:
- A background traffic bot that sends identical waves of HTTP requests to both `php-cpa` and `php-hpa` at the exact same time.

### Why do this?
When the traffic bot sends a sudden burst of requests:
- You watch **`php-cpa`** scale up pods **instantly / in advance** (because GRU foresaw the trend).
- You watch **`php-hpa`** sit idle for 50 seconds before finally reacting.
