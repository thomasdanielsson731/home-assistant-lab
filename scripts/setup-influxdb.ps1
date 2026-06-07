# setup-influxdb.ps1 — Create InfluxDB 1.x database/user and update .env
param(
    [string]$InfluxUrl = "http://192.168.68.175:8086",
    [string]$Database = "home_lab",
    [string]$User = "homelab",
    [string]$Password = ""
)

$repoRoot = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $repoRoot ".env"

if (-not $Password) {
    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match '^MQTT_PASS=' } | Select-Object -First 1
        if ($line) { $Password = ($line -replace '^MQTT_PASS=', '').Trim() }
    }
    if (-not $Password) { $Password = "change-me" }
}

function Invoke-InfluxQuery([string]$Query, [hashtable]$Auth = @{}) {
    $uri = "$InfluxUrl/query?q=$([uri]::EscapeDataString($Query))"
    $params = @{ Uri = $uri; Method = 'GET'; TimeoutSec = 15; UseBasicParsing = $true }
    if ($Auth.User) {
        $params.Credential = [pscredential]::new(
            $Auth.User, (ConvertTo-SecureString $Auth.Password -AsPlainText -Force)
        )
    }
    try { return Invoke-WebRequest @params } catch { return $_.Exception.Response }
}

Write-Host "InfluxDB at $InfluxUrl (1.8.x)"

# Try bootstrap without auth (fresh install) or with admin credentials
$adminPairs = @(
    @{ User = ''; Password = '' },
    @{ User = 'admin'; Password = $Password },
    @{ User = 'homeassistant'; Password = $Password }
)

$bootstrapped = $false
foreach ($cred in $adminPairs) {
    $r = Invoke-InfluxQuery "SHOW DATABASES" $cred
    if ($r -and $r.StatusCode -eq 200) {
        Write-Host "Connected to InfluxDB"
        Invoke-InfluxQuery "CREATE DATABASE $Database" $cred | Out-Null
        Invoke-InfluxQuery "CREATE USER $User WITH PASSWORD '$Password' WITH ALL PRIVILEGES" $cred | Out-Null
        $bootstrapped = $true
        break
    }
}

if (-not $bootstrapped) {
    Write-Warning @"
Could not auto-create InfluxDB user. Open HA → Add-ons → InfluxDB → Open Web UI (Chronograf):
  1. Create database: $Database
  2. Create user: $User with read/write on $Database
Then re-run: .\scripts\setup-influxdb.ps1 -Password 'yourpassword'
"@
    exit 1
}

# Update .env
$lines = if (Test-Path $envFile) { Get-Content $envFile } else { @() }
$keys = @{
    'INFLUX_URL' = $InfluxUrl
    'INFLUX_V2' = 'false'
    'INFLUX_DB' = $Database
    'INFLUX_USER' = $User
    'INFLUX_PASSWORD' = $Password
    'INFLUX_MEASUREMENT' = 'home_metrics'
}
$out = New-Object System.Collections.Generic.List[string]
$seen = @{}
foreach ($line in $lines) {
    $matched = $false
    foreach ($k in $keys.Keys) {
        if ($line -match "^$k=") {
            $out.Add("$k=$($keys[$k])")
            $seen[$k] = $true
            $matched = $true
            break
        }
    }
    if (-not $matched) { $out.Add($line) }
}
foreach ($k in $keys.Keys) {
    if (-not $seen[$k]) { $out.Add("$k=$($keys[$k])") }
}
$out | Set-Content $envFile -Encoding UTF8
Write-Host "Updated .env with INFLUX_* settings"
Write-Host "Restart bridges: .\scripts\start-bridges.ps1"
