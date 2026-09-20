#!/usr/bin/env bash
# ==============================================================================
# End-to-End Runner: Execute all 4 Phases sequentially
# Research Paper: "Toward Optimal Load Prediction and Customizable Autoscaling Scheme for Kubernetes"
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "===================================================================="
echo " Starting Full End-to-End Deployment (Phases 1 to 4)..."
echo "===================================================================="

bash scripts/01_phase1_train_model.sh
bash scripts/02_phase2_build_cpa.sh
bash scripts/03_phase3_deploy_manifests.sh
bash scripts/04_phase4_test_and_monitor.sh

echo "===================================================================="
echo " All 4 Phases Executed Successfully!"
echo "===================================================================="
