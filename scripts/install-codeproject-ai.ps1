# install-codeproject-ai.ps1 - Phase 4: CodeProject.AI on Windows dev PC
# Requires: admin for .NET install; GUI installer for CodeProject.AI
param(
    [switch]$SkipDotNet
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $repoRoot ".env"

function Get-DevPcHost {
    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match '^DEV_PC_HOST=' } | Select-Object -First 1
        if ($line) { return ($line -replace '^DEV_PC_HOST=', '').Trim() }
    }
    return "192.168.68.136"
}

Write-Host "=== CodeProject.AI setup (Phase 4) ===" -ForegroundColor Cyan

try {
    $health = Invoke-WebRequest -Uri "http://localhost:32168/v1/status/health" -UseBasicParsing -TimeoutSec 3
    if ($health.StatusCode -eq 200) {
        Write-Host "OK  CodeProject.AI already running on :32168" -ForegroundColor Green
        Write-Host "    Dashboard: http://localhost:32168"
        Write-Host "    Next: enable Face Recognition module in dashboard"
        exit 0
    }
} catch { }

if (Test-Path "C:\Program Files\CodeProject\AI") {
    Write-Host "WARN  CodeProject.AI installed but service not responding on :32168"
    Write-Host "      Start service: Services -> CodeProject.AI Server"
}

if (-not $SkipDotNet) {
    $runtimes = & dotnet --list-runtimes 2>$null
    $hasNet9 = $runtimes | Where-Object { $_ -match 'Microsoft\.AspNetCore\.App 9\.' }
    if (-not $hasNet9) {
        Write-Host "Installing .NET 9 ASP.NET Runtime (required)..." -ForegroundColor Yellow
        winget install Microsoft.DotNet.AspNetCore.9 `
            --accept-source-agreements --accept-package-agreements --silent
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "winget install failed - install manually: https://dotnet.microsoft.com/download/dotnet/9.0"
        }
    } else {
        Write-Host "OK  .NET 9 ASP.NET runtime present"
    }
}

$downloadPage = "https://codeproject.github.io/codeproject.ai/latest.html"
Write-Host ""
Write-Host "Install CodeProject.AI Server:" -ForegroundColor Yellow
Write-Host "  1. Download Windows x64 installer from:"
Write-Host "     $downloadPage"
Write-Host "  2. Run installer (installs Windows service)"
Write-Host "  3. Open http://localhost:32168"
Write-Host "  4. Modules -> install/enable Face Recognition"
Write-Host ""

Start-Process $downloadPage

$devHost = Get-DevPcHost
Write-Host "After install, verify Double Take points to:" -ForegroundColor Cyan
Write-Host "  http://${devHost}:32168"
Write-Host "  config/double-take/config.yml - sync with .\scripts\sync-config.ps1"
Write-Host ""
Write-Host "Train faces: http://192.168.68.175:3000"
Write-Host "Runbook: docs/runbooks/codeproject-ai-setup.md"
