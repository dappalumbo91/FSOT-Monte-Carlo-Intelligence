# Push export bundle to Hugging Face dataset (requires: huggingface-cli login)
param(
    [string]$RepoId = "dappalumbo91/fsot-monte-carlo-intelligence",
    [string]$Symbol = "BTC"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python scripts\export_publication_bundle.py --symbol $Symbol --history
$Export = Join-Path $Root "data\exports"
Copy-Item -Force (Join-Path $Root "publishing\huggingface\README.md") (Join-Path $Export "README.md")

huggingface-cli upload $RepoId $Export --repo-type dataset
Write-Host "Dataset: https://huggingface.co/datasets/$RepoId"
