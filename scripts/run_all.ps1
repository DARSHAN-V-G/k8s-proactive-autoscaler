# End-to-End Runner: Execute all 4 Phases sequentially (PowerShell)
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host " Starting Full End-to-End Deployment (Phases 1 to 4)..." -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

& "$PSScriptRoot\01_phase1_train_model.ps1"
& "$PSScriptRoot\02_phase2_build_cpa.ps1"
& "$PSScriptRoot\03_phase3_deploy_manifests.ps1"
& "$PSScriptRoot\04_phase4_test_and_monitor.ps1"

Write-Host "====================================================================" -ForegroundColor Green
Write-Host " All 4 Phases Executed Successfully!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
