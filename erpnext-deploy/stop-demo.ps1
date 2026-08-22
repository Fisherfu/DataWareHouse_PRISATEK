# Stop the public link and (optionally) the ERPNext containers
param(
    [switch]$StopContainers  # pass this to also stop containers; default only stops the tunnel
)

Set-Location $PSScriptRoot

Write-Output "Stopping cloudflared tunnel..."
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force

if ($StopContainers) {
    $dockerBin = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
    if ($env:Path -notlike "*$dockerBin*") { $env:Path += ";$dockerBin" }
    Write-Output "Stopping ERPNext containers..."
    docker compose -f pwd.yml down
} else {
    Write-Output "Containers are still running (http://localhost:8080 still works locally). To stop them too, run: .\stop-demo.ps1 -StopContainers"
}
