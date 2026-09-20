"""
Helper to synchronize trained weights into k8s-metrics-cpu/saved_models/
"""
import os
import shutil

src_pt = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model", "saved_models", "GRU_Model_24.pt"))
src_sc = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model", "saved_models", "scaler.json"))

dst_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))
os.makedirs(dst_dir, exist_ok=True)

if os.path.exists(src_pt):
    shutil.copy2(src_pt, os.path.join(dst_dir, "GRU_Model_24.pt"))
    print(f"Copied GRU_Model_24.pt -> {dst_dir}")

if os.path.exists(src_sc):
    shutil.copy2(src_sc, os.path.join(dst_dir, "scaler.json"))
    print(f"Copied scaler.json -> {dst_dir}")
