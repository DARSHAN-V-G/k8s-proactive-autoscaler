# PowerShell script to install Custom Pod Autoscaler Operator into local Kubernetes cluster
# Based on Listing 15 of MDPI Mathematics 2023 paper

$VERSION = "v1.2.1"
$HELM_CHART = "custom-pod-autoscaler-operator"
$URL = "https://github.com/jthomperoo/custom-pod-autoscaler-operator/releases/download/$VERSION/custom-pod-autoscaler-operator-$VERSION.tgz"

Write-Host "Installing Custom Pod Autoscaler Operator ($VERSION)..." -ForegroundColor Cyan
helm install $HELM_CHART $URL

Write-Host "Verifying Operator Pod status..." -ForegroundColor Green
kubectl get pods -l app=custom-pod-autoscaler-operator
