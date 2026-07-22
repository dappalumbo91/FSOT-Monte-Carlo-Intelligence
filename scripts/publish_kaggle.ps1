# Create/update Kaggle dataset from exports (requires: kaggle.json credentials)
param(
    [string]$Symbol = "BTC"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python scripts\export_publication_bundle.py --symbol $Symbol --history

$Export = Join-Path $Root "data\exports"
$KaggleDir = Join-Path $Root "publishing\kaggle\upload"
New-Item -ItemType Directory -Force -Path $KaggleDir | Out-Null
Copy-Item -Force (Join-Path $Export "*") $KaggleDir
Copy-Item -Force (Join-Path $Root "publishing\kaggle\dataset-metadata.json") $KaggleDir
Copy-Item -Force (Join-Path $Root "publishing\kaggle\fsot_mc_demo.ipynb") $KaggleDir

# Try create; if exists, version
kaggle datasets create -p $KaggleDir --dir-mode zip 2>$null
if ($LASTEXITCODE -ne 0) {
    kaggle datasets version -p $KaggleDir -m "FSOT MC intelligence export refresh" --dir-mode zip
}
Write-Host "Kaggle dataset update attempted from $KaggleDir"
