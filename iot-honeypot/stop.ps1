# ============================================================
# stop.ps1  —  Stop all IoT Honeypot services
# ============================================================
param([switch]$KeepDatabase)

$Root = $PSScriptRoot
$ErrorActionPreference = "SilentlyContinue"

function Banner($msg) {
    Write-Host ""
    Write-Host "  $msg" -ForegroundColor Cyan
}

Banner "Stopping IoT Honeypot services..."

# Kill processes listening on known ports
@(8000, 5173, 2222, 8080, 554) | ForEach-Object {
    $port = $_
    $pid = (netstat -ano | Select-String ":$port ") -replace '.*\s+(\d+)\s*$', '$1' | Select-Object -First 1
    if ($pid) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "[STOP] Port $port process ($pid) killed" -ForegroundColor Yellow
    }
}

# Stop Docker containers
if (-not $KeepDatabase) {
    Banner "Stopping Postgres + Redis containers"
    Push-Location "$Root\backend"
    docker compose -f docker-compose.dev.yml down
    Pop-Location
    Write-Host "[OK] Docker containers stopped" -ForegroundColor Green
}
else {
    Write-Host "[SKIP] Keeping database containers running (-KeepDatabase)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "All services stopped." -ForegroundColor Green
