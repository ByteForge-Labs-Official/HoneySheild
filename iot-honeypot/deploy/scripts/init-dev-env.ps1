# Generate dev secrets for honeynet. Safe to run on Windows; produces files in
# deploy/secrets/.  Real deploys should use a secret manager — this is dev-only.
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$secretsDir = Join-Path $root 'secrets'

# Charset excludes: space, tab, ;, #, ", ', `, $, \, /, *, ?, [, ], {, }, (, ),
# &, |, <, >, !, ~, =, ,, ^, ., +, :
$ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'

function New-RandomString([int]$Len = 32) {
    $bytes = New-Object byte[] $Len
    (Get-Random -Count $Len -InputObject $ALPHABET.ToCharArray()) -join ''
}

$files = @{
    'postgres_password'      = 32
    'postgres_ro_password'   = 32
    'relay_password'         = 32
    'grafana_admin_password' = 32
    'grafana_secret_key'     = 64
    'grafana_db_password'    = 32
    'am_basic_auth'          = 32
    'prom_basic_auth'        = 32
}

foreach ($k in $files.Keys) {
    $path = Join-Path $secretsDir ($k + '.txt')
    New-RandomString $files[$k] | Set-Content -Path $path -NoNewline
    Write-Host "wrote $path"
}

$optFiles = @(
    'caddy_cloudflare_token',
    'pagerduty_key',
    'slack_webhook_sec',
    'slack_webhook_ops',
    'slack_webhook_dba'
)
foreach ($k in $optFiles) {
    $path = Join-Path $secretsDir ($k + '.txt')
    if (-not (Test-Path $path)) {
        New-RandomString 32 | Set-Content -Path $path -NoNewline
        Write-Host "wrote $path"
    }
}

# Materialise .env from .env.example, line-by-line, only replacing placeholder
# values (not URL fragments inside SLACK_WEBHOOK_*, etc.).
$envPath = Join-Path $root '.env'
$examplePath = Join-Path $root '.env.example'
if (Test-Path $envPath) { Remove-Item $envPath -Force }
$lines = Get-Content $examplePath
foreach ($line in $lines) {
    $trim = $line.TrimStart()
    if ($trim.StartsWith('#') -or [string]::IsNullOrWhiteSpace($trim)) {
        Add-Content -Path $envPath -Value $line
        continue
    }
    # Split on the first "=" only.
    $idx = $line.IndexOf('=')
    if ($idx -lt 0) {
        Add-Content -Path $envPath -Value $line
        continue
    }
    $key = $line.Substring(0, $idx)
    $val = $line.Substring($idx + 1)
    if ($val -match '^changeme(-[A-Za-z0-9_-]+)?$') {
        $newVal = New-RandomString 32
        Add-Content -Path $envPath -Value ($key + '=' + $newVal)
    } else {
        Add-Content -Path $envPath -Value $line
    }
}
Write-Host "rewrote $envPath"
