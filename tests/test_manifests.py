"""
Unit tests for Kubernetes Manifests and CRD Configurations (Phase 3)
"""

import os
import glob
import yaml
import pytest


def test_all_manifests_are_valid_yaml():
    manifests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "manifests"))
    yaml_files = glob.glob(os.path.join(manifests_dir, "*.yaml"))

    assert len(yaml_files) >= 5, f"Expected at least 5 YAML manifest files, found {len(yaml_files)}"

    for fpath in yaml_files:
        with open(fpath, "r") as f:
            docs = list(yaml.safe_load_all(f))
            assert len(docs) > 0, f"File {fpath} is empty or invalid YAML"
            for doc in docs:
                assert "apiVersion" in doc, f"Missing apiVersion in {fpath}"
                assert "kind" in doc, f"Missing kind in {fpath}"
                assert "metadata" in doc, f"Missing metadata in {fpath}"


def test_php_cpa_and_hpa_deployments_consistency():
    manifests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "manifests"))

    with open(os.path.join(manifests_dir, "php-cpa.yaml"), "r") as f:
        cpa_docs = list(yaml.safe_load_all(f))
        cpa_deploy = next(d for d in cpa_docs if d["kind"] == "Deployment")

    with open(os.path.join(manifests_dir, "php-hpa.yaml"), "r") as f:
        hpa_docs = list(yaml.safe_load_all(f))
        hpa_deploy = next(d for d in hpa_docs if d["kind"] == "Deployment")

    # Verify resource parity for fair comparison
    cpa_res = cpa_deploy["spec"]["template"]["spec"]["containers"][0]["resources"]
    hpa_res = hpa_deploy["spec"]["template"]["spec"]["containers"][0]["resources"]

    assert cpa_res["requests"]["cpu"] == "50m"
    assert hpa_res["requests"]["cpu"] == "50m"
    assert cpa_res["limits"]["cpu"] == "500m"
    assert hpa_res["limits"]["cpu"] == "500m"


def test_cpa_and_hpa_target_references():
    manifests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "manifests"))

    with open(os.path.join(manifests_dir, "cpa.yaml"), "r") as f:
        cpa_crd = yaml.safe_load(f)
        assert cpa_crd["kind"] == "CustomPodAutoscaler"
        assert cpa_crd["spec"]["scaleTargetRef"]["name"] == "php-cpa"
        
        # Verify interval and stabilization parameters
        cfg = {c["name"]: c["value"] for c in cpa_crd["spec"]["config"]}
        assert cfg.get("interval") == "10000"
        assert cfg.get("downscaleStabilization") == "60"

    with open(os.path.join(manifests_dir, "hpa.yaml"), "r") as f:
        hpa = yaml.safe_load(f)
        assert hpa["kind"] == "HorizontalPodAutoscaler"
        assert hpa["spec"]["scaleTargetRef"]["name"] == "php-hpa"
        assert hpa["spec"]["minReplicas"] == 1
        assert hpa["spec"]["maxReplicas"] == 30
