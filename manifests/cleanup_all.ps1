# PowerShell script to tear down all testbed components cleanly

Write-Host "Tearing down benchmark resources..." -ForegroundColor Yellow

kubectl delete -f manifests/load-generator.yaml --ignore-not-found
kubectl delete -f manifests/cpa.yaml --ignore-not-found
kubectl delete -f manifests/hpa.yaml --ignore-not-found
kubectl delete -f manifests/php-cpa.yaml --ignore-not-found
kubectl delete -f manifests/php-hpa.yaml --ignore-not-found

Write-Host "Cleanup complete." -ForegroundColor Green
