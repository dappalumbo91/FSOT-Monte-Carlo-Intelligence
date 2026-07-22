# Create GitHub repo and push (requires: gh auth login)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\publish_github.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path .git)) {
    git init
    git branch -M main
}

# Ensure gitignore
if (-not (Test-Path .gitignore)) {
    @"
.venv/
__pycache__/
.pytest_cache/
*.pyc
data/exports/
data/patterns/
data/journals/
*.egg-info/
dist/
build/
"@ | Set-Content .gitignore
}

git add -A
git status
$msg = "feat: FSOT Monte Carlo Intelligence v0.2 — authority D1D38A, multi-horizon, publication packaging"
git commit -m $msg 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing to commit or commit failed (ok if already committed)."
}

# Auth check
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: gh auth login"
    exit 1
}

$user = (gh api user --jq .login)
$repo = "FSOT-Monte-Carlo-Intelligence"
Write-Host "Creating github.com/$user/$repo (public) if missing..."
gh repo create $repo --public --source=. --remote=origin --description "FSOT 2.1 Monte Carlo intelligence — observer collapse + pattern solidification (zero free parameters)" 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote remove origin 2>$null
    git remote add origin "https://github.com/$user/$repo.git"
}

git push -u origin main
Write-Host "Done: https://github.com/$user/$repo"
