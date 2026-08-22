# Start ERPNext demo environment and create a public link (Cloudflare quick tunnel)
$ErrorActionPreference = "Stop"

$dockerBin = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
if ($env:Path -notlike "*$dockerBin*") { $env:Path += ";$dockerBin" }

$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $cloudflared)) { $cloudflared = "C:\Program Files\cloudflared\cloudflared.exe" }
if (-not (Test-Path $cloudflared)) { $cloudflared = "$env:LOCALAPPDATA\Microsoft\WinGet\Links\cloudflared.exe" }

Set-Location $PSScriptRoot

# 1. Make sure Docker engine is running; try to launch Docker Desktop if not
try {
    docker info *> $null
} catch {
    Write-Output "Docker engine is not running. Trying to launch Docker Desktop..."
    Start-Process "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe"
    Write-Output "Please wait ~30-60s for Docker Desktop to fully start, then run this script again."
    exit 1
}

# 2. Start containers
Write-Output "Starting ERPNext containers..."
docker compose -f pwd.yml up -d

# 3. Wait for port 8080 to respond
Write-Output "Waiting for ERPNext to be ready..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    Write-Output "Warning: timed out waiting. ERPNext may not be fully ready yet; continuing to create tunnel anyway."
}

# 4. Start cloudflared quick tunnel
Write-Output "Creating public link..."
$log = Join-Path $PSScriptRoot "cloudflared.log"
$logOut = Join-Path $PSScriptRoot "cloudflared.stdout.log"
if (Test-Path $log) { Remove-Item $log }
if (Test-Path $logOut) { Remove-Item $logOut }
Start-Process -FilePath $cloudflared -ArgumentList "tunnel --url http://localhost:8080" `
    -WindowStyle Hidden -RedirectStandardError $log -RedirectStandardOutput $logOut

# 5. Extract the URL from the log
$url = $null
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $log) {
        $match = Select-String -Path $log -Pattern "https://[a-zA-Z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue
        if ($match) { $url = $match.Matches[0].Value; break }
    }
}

Write-Output ""
Write-Output "=================================================="
if ($url) {
    Write-Output "Demo link: $url"
} else {
    Write-Output "Could not read the link yet, check $log"
}
Write-Output "Username: Administrator"
Write-Output "Password: default is 'admin' unless you changed it (see README.md to change it)"
Write-Output "=================================================="
