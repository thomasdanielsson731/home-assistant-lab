# sync-config.ps1 — Windows alternative to sync-config.sh
# Requires: OpenSSH (built into Windows 10/11)
#
# Usage:
#   .\scripts\sync-config.ps1
#   .\scripts\sync-config.ps1 -DryRun

param([switch]$DryRun)

$repoRoot = Split-Path $PSScriptRoot -Parent

# Load .env
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=][^=]*)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

$HA_HOST       = if ($env:HA_HOST)       { $env:HA_HOST }       else { "192.168.68.175" }
$HA_USER       = if ($env:HA_USER)       { $env:HA_USER }       else { "root" }
$HA_SSH_PORT   = if ($env:HA_SSH_PORT)   { $env:HA_SSH_PORT }   else { "22222" }
$HA_CONFIG_PATH = if ($env:HA_CONFIG_PATH) { $env:HA_CONFIG_PATH } else { "/config" }

$target = "${HA_USER}@${HA_HOST}"
$sshOpts = @("-p", $HA_SSH_PORT, "-o", "StrictHostKeyChecking=no")
$scpOpts = @("-P", $HA_SSH_PORT, "-o", "StrictHostKeyChecking=no")

if ($DryRun) {
    Write-Host "[dry-run] Would sync to ${target}:${HA_CONFIG_PATH}"
    exit 0
}

Write-Host "Syncing config to ${target}:${HA_CONFIG_PATH} ..."

$excludedNames = @("secrets.yaml")
$excludedExts  = @(".db", ".db-shm", ".db-wal", ".log")
$excludedDirs  = @(".storage")

function Sync-Directory {
    param($localDir, $remotePath)

    $files = Get-ChildItem -Path $localDir -Recurse -File | Where-Object {
        $excludedNames -notcontains $_.Name -and
        $excludedExts  -notcontains $_.Extension -and
        ($_.FullName -split '\\' | Where-Object { $excludedDirs -contains $_ }).Count -eq 0
    }

    # Collect unique remote directories and create them in one SSH call
    $remoteDirs = $files | ForEach-Object {
        $rel = $_.DirectoryName.Substring($localDir.Length).TrimStart('\').Replace('\', '/')
        if ($rel) { "$remotePath/$rel" } else { $remotePath }
    } | Sort-Object -Unique

    if ($remoteDirs) {
        $mkdirCmd = "mkdir -p " + ($remoteDirs -join " ")
        ssh @sshOpts $target $mkdirCmd | Out-Null
    }

    foreach ($file in $files) {
        $rel = $file.FullName.Substring($localDir.Length).TrimStart('\').Replace('\', '/')
        $remoteFile = "$remotePath/$rel"
        Write-Host "  -> $rel"
        scp @scpOpts $file.FullName "${target}:${remoteFile}" | Out-Null
    }
}

# Pass 1: HA config
Sync-Directory (Join-Path $repoRoot "config\home-assistant") $HA_CONFIG_PATH

# Pass 2: Frigate config
Write-Host "  -> frigate/config.yml"
scp @scpOpts (Join-Path $repoRoot "config\frigate\config.yml") "${target}:${HA_CONFIG_PATH}/frigate/config.yml"

# Pass 3: Double Take config
Write-Host "  -> double-take/config.yml"
scp @scpOpts (Join-Path $repoRoot "config\double-take\config.yml") "${target}:${HA_CONFIG_PATH}/double-take/config.yml"

Write-Host ""
Write-Host "Done. Restart affected add-ons in HA if config changed."
