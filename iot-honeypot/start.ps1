# ============================================================
# start.ps1  —  One-command launcher for the IoT Honeypot
# ============================================================
# Usage:
#   .\start.ps1            launch everything (install + run)
#   .\start.ps1 -SkipJava   skip the Java honeypot (SSH/RTSP/HTTP)
#   .\start.ps1 -SkipBuild  skip mvn build (JAR already built)
# ============================================================
param(
    [switch]$SkipJava,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Banner($msg) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Check($name, $cmd) {
    try {
        Invoke-Expression $cmd | Out-Null
        Write-Host "[OK] $name found" -ForegroundColor Green
    }
    catch {
        Write-Host "[MISSING] $name not found. Please install it and re-run." -ForegroundColor Red
        exit 1
    }
}

# ────────────────────────────────────────────────────────────
# 1. PRE-FLIGHT CHECKS
# ────────────────────────────────────────────────────────────
Banner "Checking prerequisites"
Check "Docker"  "docker --version"
Check "Python"  "python --version"
Check "Node.js" "node --version"
Check "npm"     "npm --version"
if (-not $SkipJava) {
    Check "Java (17+)" "java -version"
}

# ────────────────────────────────────────────────────────────
# 2. START POSTGRES + REDIS (Docker)
# ────────────────────────────────────────────────────────────
Banner "Starting Postgres + Redis (Docker)"
Push-Location "$Root\backend"
docker compose -f docker-compose.dev.yml up -d
Write-Host "Waiting 5s for Postgres to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Pop-Location

# ────────────────────────────────────────────────────────────
# 3. PYTHON BACKEND — install deps + migrate + run
# ────────────────────────────────────────────────────────────
Banner "Installing Python backend dependencies"
Push-Location "$Root\backend"
pip install -e "." --quiet
Write-Host "[OK] Python packages installed" -ForegroundColor Green

Banner "Running database migrations (Alembic)"
alembic upgrade head
Write-Host "[OK] Database schema up-to-date" -ForegroundColor Green
Pop-Location

Banner "Starting FastAPI backend (port 8000)"
$BackendJob = Start-Process -FilePath "powershell" `
    -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" `
    -PassThru
Write-Host "[OK] Backend started (PID $($BackendJob.Id))" -ForegroundColor Green
Write-Host "     Swagger docs -> http://localhost:8000/docs" -ForegroundColor DarkGray

# Give backend time to boot
Start-Sleep -Seconds 4

# ────────────────────────────────────────────────────────────
# 4. REACT FRONTEND — install + run
# ────────────────────────────────────────────────────────────
Banner "Installing frontend npm packages"
Push-Location "$Root\frontend"
if (-not (Test-Path "node_modules")) {
    npm install
    Write-Host "[OK] npm packages installed" -ForegroundColor Green
}
else {
    Write-Host "[SKIP] node_modules already exists" -ForegroundColor Yellow
}
Pop-Location

Banner "Starting React frontend (port 5173)"
$FrontendJob = Start-Process -FilePath "powershell" `
    -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev" `
    -PassThru
Write-Host "[OK] Frontend started (PID $($FrontendJob.Id))" -ForegroundColor Green
Write-Host "     Dashboard -> http://localhost:5173" -ForegroundColor DarkGray

# ────────────────────────────────────────────────────────────
# 5. JAVA HONEYPOT — build + run
# ────────────────────────────────────────────────────────────
if (-not $SkipJava) {
    Banner "Building Java honeypot (Maven)"
    Push-Location $Root
    if (-not $SkipBuild) {
        & "$Root\mvnw.cmd" -B -ntp clean package
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Maven build failed! Fix errors above and re-run." -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Host "[OK] JAR built successfully" -ForegroundColor Green
    }
    else {
        Write-Host "[SKIP] Maven build skipped (-SkipBuild flag)" -ForegroundColor Yellow
    }

    Banner "Starting Java honeypot (SSH:2222, HTTP:8080, RTSP:554)"
    $HoneypotJob = Start-Process -FilePath "powershell" `
        -ArgumentList "-NoExit", "-Command", "cd '$Root'; java -Dhoneypot.bind=0.0.0.0 -Dhoneypot.port=2222 -Dhoneypot.profile=full -jar target\iot-honeypot.jar" `
        -PassThru
    Write-Host "[OK] Java honeypot started (PID $($HoneypotJob.Id))" -ForegroundColor Green
    Pop-Location
}

# ────────────────────────────────────────────────────────────
# 6. DONE
# ────────────────────────────────────────────────────────────
Banner "All services are running!"
Write-Host ""
Write-Host "  Dashboard     ->  http://localhost:5173" -ForegroundColor White
Write-Host "  API / Swagger ->  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  SSH Trap      ->  port 2222" -ForegroundColor White
Write-Host "  HTTP Trap     ->  port 8080" -ForegroundColor White
Write-Host "  RTSP Trap     ->  port 554" -ForegroundColor White
Write-Host ""
Write-Host "  First time? Register an admin account at:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs  ->  POST /api/v1/auth/register" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop. Or close the windows." -ForegroundColor DarkGray
