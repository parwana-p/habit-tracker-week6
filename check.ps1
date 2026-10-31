# Run all guardrails locally. Stops at the first failure and exits non-zero.
# Usage (PowerShell):  .\check.ps1
$ErrorActionPreference = "Stop"
function Step($name, $cmd) {
    Write-Host "==> $name" -ForegroundColor Cyan
    & $cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $name" -ForegroundColor Red; exit $LASTEXITCODE }
}
Step "ruff (lint)"    { python -m ruff check . }
Step "black (format)" { python -m black --check . }
Step "pytest (tests)" { python -m pytest -q }
Write-Host "All checks passed." -ForegroundColor Green
